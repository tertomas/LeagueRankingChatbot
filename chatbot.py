import os
import yaml
from openai import OpenAI
from dotenv import load_dotenv
from database import connect_db


load_dotenv()

# paths definitions
semantic_layer_path = "semantic_layer.yml"


# loading semantic layer
def load_semantic_layer():
    with open(semantic_layer_path, "r") as file:
        return yaml.safe_load(file)


# createing deepinfra client with openai API
def create_client():
    return OpenAI(
        api_key=os.getenv("deepinfra_api_key"),
        base_url="https://api.deepinfra.com/v1/openai")


# prompt definition and rules for SQK generation
def create_sql_prompt(question, semantic_layer, universities, subjects):
    return f"""
        You are an SQL generator for a DuckDB database.
        Your ONLY task is to convert the user's question into a valid SQL query.
        IMPORTANT:
        This function is only used for questions that require querying the database.
        If the user asks to explain the meaning of a metric, do not use this function.

        You MUST NOT answer the user's question.
        You MUST NOT use your own knowledge.
        You MUST only use information contained in the database schema
        and semantic layer below.

        DATABASE TABLES IN DUCKDB:
        - ranking (contains overall university metrics)
        - subject_areas (contains subject-specific metrics)

        SEMANTIC LAYER:
        {semantic_layer}

        VALID UNIVERSITY NAMES:
        {universities}

        VALID SUBJECT AREAS:
        {subjects}

        RULES:
        - Return ONLY the SQL query.
        - Do not use markdown.
        - Do not explain the query.
        - The semantic layer contains two names for each field:
            - "name" is the semantic/business name.
            - "sql_column" is the actual column name in the database.
        - TABLE NAMES: In your FROM clause, you MUST ONLY use the exact physical 
        table names 'ranking' or 'subject_areas'. NEVER use 'guardian_ranking', 
        'guardian_subjects', or any other names from the semantic layer as SQL table names.
        - COLUMN NAMES: The semantic layer contains "name" and "sql_column". 
        ALWAYS use the value of "sql_column" as the column name. NEVER use the semantic "name".
        - When writing SQL, ALWAYS use the value of "sql_column" as the column name.
        - NEVER use the semantic "name" directly as a SQL column name.
        - When the user refers to a university, use a university name
        from AVAILABLE UNIVERSITIES.
        - When the user refers to a subject, use a subject name
        from AVAILABLE SUBJECT AREAS.
        - Do not invent university or subject names.
        - If the question cannot be answered using the available database
        tables, columns, and semantic layer, return exactly:

        CANNOT_ANSWER

        - Do not generate SQL if the question cannot be answered from the database.
        - Do not invent information.
        - Do not use your own knowledge.

        TIME AND YEAR RULES:

        - If the user explicitly specifies a year, filter the query to that year.
        - If the user does NOT specify a year, NEVER assume a single year.
        - If no year is specified, return results for ALL available years.
        - When returning results for multiple years, ALWAYS include ranking_year
        in the SELECT clause.
        - When returning results for multiple years, ALWAYS order the results
        by ranking_year DESC.

        - For aggregation questions without a specified year, calculate the
        aggregation separately for each ranking_year.
        - Therefore, when aggregating without a specified year, include
        ranking_year in SELECT and GROUP BY.
        - When aggregating for a specific year, do not need to group by
        ranking_year unless it is needed for the result.

        - For questions asking for a ranking position such as "best",
        "second best", "third best", etc., apply the ranking separately
        for each year when no year is specified.
        - Do NOT select only the latest year unless the user explicitly asks
        for the latest, current, or most recent ranking.

        EXAMPLES:

        User: "What is the second best university in Dentistry?"
        Correct behavior:
        Return the second-ranked university for EVERY available year,
        include ranking_year in the result, and order by ranking_year DESC.

        User: "What is the second best university in Dentistry in 2020?"
        Correct behavior:
        Return only the second-ranked university for 2020.

        User: "What is the average Guardian score for Dentistry?"
        Correct behavior:
        Calculate the average separately for EVERY available year,
        include ranking_year, group by ranking_year, and order by
        ranking_year DESC.

        User: "What is the average Guardian score for Dentistry in 2020?"
        Correct behavior:
        Calculate the average only for 2020.

        - Aggregation questions such as average, mean, minimum, maximum,
        highest, lowest, sum, or count are valid database questions
        whenever the requested metric exists in the semantic layer.

        - Use the metric's sql_column when performing the aggregation.

        - "highest" or "lowest" may refer either to the value of a metric
        or to a ranking position. Use the context of the question to
        determine which one is intended.

        TOP N RULES:

        - When the user asks for "top N universities with the highest
        [metric]" or "top N universities with the lowest [metric]",
        return N universities ordered by that metric.

        - In this case, "top N" refers to the number of results requested,
        NOT to the university's ranking position.

        - For example:
        "Which top 4 universities had the highest career prospects?"
        means ORDER BY career_prospects DESC LIMIT 4.

        - If the user explicitly asks for the top N ranked universities,
        use the appropriate ranking column instead.

        - When no year is specified, apply the query separately for every
        available ranking_year. Do not return only one year.

        - When using a knowledge graph sql_rule, copy the sql_rule exactly.
        - Do not modify, reinterpret, or rewrite the SQL values contained
        in a knowledge graph sql_rule.
        - SQL string values must use single quotes.
        - If a string value contains an apostrophe, escape it by doubling
        the apostrophe.
        Example:
        King's College London
        must be written as:
        'King''s College London'

        USER QUESTION:
        {question}
        """


# generating SQL query from user question
def generate_sql(client, question, semantic_layer, universities, subjects):
    prompt = create_sql_prompt(question, semantic_layer, universities, subjects)

    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[{"role": "user","content": prompt}],
        temperature=0)

    # delete apostrophes from queries if present
    sql = response.choices[0].message.content.strip()

    if sql.startswith("```sql"):
        sql = sql[6:]

    if sql.startswith("```"):
        sql = sql[3:]

    if sql.endswith("```"):
        sql = sql[:-3]

    return sql.strip()


# executing SQL over DuckDB database
def execute_sql(sql, con):
    return con.execute(sql).fetchdf()

# loading university names and subject areas to allow user typos
def load_database_values(con):
    universities = con.execute("""
        SELECT DISTINCT university_name
        FROM ranking
        WHERE university_name IS NOT NULL
        ORDER BY university_name
    """).fetchdf()

    subjects = con.execute("""
        SELECT DISTINCT subject_name
        FROM subject_areas
        WHERE subject_name IS NOT NULL
        ORDER BY subject_name
    """).fetchdf()

    return (universities["university_name"].tolist(),
        subjects["subject_name"].tolist())

# if question is not analytical but asking about specific metric, 
# semantic layer is used for answer generation 
def explain_metric(client, question, semantic_layer):
    prompt = f"""
        You explain metrics used in the Guardian university rankings.

        Use ONLY the information in the semantic layer below.
        Do not use your own knowledge.
        Do not invent information.

        Explain the meaning of the metric asked about in the user's question.
        Keep the explanation short and clear.

        If the metric is not described in the semantic layer, return exactly:
        CANNOT_ANSWER

        SEMANTIC LAYER:
        {semantic_layer}

        USER QUESTION:
        {question}
        """
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[
            {"role": "user","content": prompt
            }],temperature=0)

    return response.choices[0].message.content.strip()

# determining whether the question is analytical or seeking metric explanation
def is_metric_question(client, question, semantic_layer):
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[
            {
                "role": "user",
                "content": f"""
                Is the following question asking for the meaning or definition
                of a metric described in the semantic layer?

                Answer only YES or NO.

                SEMANTIC LAYER:
                {semantic_layer}

                QUESTION:
                {question}
                """}], temperature=0)

    return response.choices[0].message.content.strip() == "YES"

# main orchestrator for chatbot
def ask_question(question):
    # preparing prompt inputs
    semantic_layer = load_semantic_layer()
    client = create_client()

    # checking type of question
    if is_metric_question(client, question, semantic_layer):
        explanation = explain_metric(
            client,question,semantic_layer)
        return None, explanation, "EXPLANATION"

    # for non-explanation questions, connection to db is established
    con = connect_db()
    try:
        # obtaining valid entities
        universities, subjects = load_database_values(con)
        sql = generate_sql(client,question,semantic_layer,
                           universities,subjects)
        if sql == "CANNOT_ANSWER":
            return None, None, "CANNOT_ANSWER"
        result = execute_sql(sql, con)

    finally:
        con.close()
    if result.empty or result.isna().all().all():
        return sql, None, "NO_DATA"
    return sql, result, "OK"


# testing purposes
if __name__ == "__main__":
    question = input("Ask a question: ")
    sql, result, status = ask_question(question)
    if status == "CANNOT_ANSWER":
        print("\nI can't answer this question because the required information")
        print("is not available in the league tables database.")

    elif status == "NO_DATA":
        print("\nI couldn't find any data matching your question.")
        print("\nGenerated SQL:")
        print(sql)

    elif status == "EXPLANATION":
        print("\nMetric Explanation:")
        print(result)

    else:
        print("\nGenerated SQL:")
        print(sql)
        print("\nResult:")
        print(result)
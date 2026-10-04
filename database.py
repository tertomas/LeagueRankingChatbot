import os
import duckdb

# data initialization
def prepare_db(database_path = 'database.db', 
               ranking_path = "data/cleaned/ranking.csv", 
               subject_areas_path = "data/cleaned/subject_areas.csv"):
    # Creating connection to the database
    con = duckdb.connect(database=database_path)

    # creating views out of cleaned data 
    con.execute(f"""
        CREATE OR REPLACE VIEW subject_areas AS 
        SELECT * FROM read_csv_auto('{subject_areas_path}')
        """)

    # creatig view for ranking table 
    # years and universities area added since this will be the main table
    con.execute(f"""
        CREATE OR REPLACE VIEW ranking AS
        SELECT 
            u.university_name,
            y.ranking_year,
            r.rank_current,
            r.rank_previous,
            r.rank_change,
            r.guardian_score,
            r.satisfaction_teaching,
            r.satisfaction_overall,
            r.spend_per_student,
            r.student_staff_ratio,
            r.career_prospects,
            r.value_added_score,
            r.entry_tariff,
            r.satisfaction_feedback
        FROM (
            SELECT university_name FROM read_csv_auto('{ranking_path}')
            UNION 
            SELECT university_name FROM read_csv_auto('{subject_areas_path}')
        ) u
        CROSS JOIN (
            SELECT unnest([2013, 2014, 2015]) AS ranking_year
        ) y
        LEFT JOIN read_csv_auto('{ranking_path}') r 
            ON u.university_name = r.university_name 
            AND y.ranking_year = r.ranking_year;""")

    # Closing the connection
    con.close()

# connecting to the database
def connect_db(database_path='database.db'):
    if not os.path.exists(database_path):
        prepare_db(database_path)
    # Create a connection to the DuckDB database
    return duckdb.connect(database=database_path)

if __name__ == "__main__":
    prepare_db()
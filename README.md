# Guardian League Ranking Chatbot

A Streamlit chatbot for querying Guardian UK university rankings using natural-language questions.

## Features

* Natural-language questions about university and subject rankings
* SQL generation using DeepSeek via DeepInfra
* SQL execution using DuckDB
* Metric explanations based on the semantic layer
* Ranking, aggregation and Top N questions
* Results for multiple years when no year is specified
* Knowledge Graph for concepts such as Oxbridge and Russell Group
* Displays generated SQL
* Handles unsupported questions and empty results

## Project Structure

```text
LeagueRankingChatbot/
├── app.py
├── chatbot.py
├── database.py
├── database.db
├── semantic_layer.yml
├── requirements.txt
│
└── data/
    ├── raw/
    │   └── TheGuardianRanking.xlsx
    ├── cleaned/
    │   ├── ranking.csv
    │   └── subject_areas.csv
    └── data_preparation.py
```

`exploration.ipynb` is used for data exploration and is not included in the repository.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file with your DeepInfra API key:

```text
deepinfra_api_key=YOUR_API_KEY
```

Run the application:

```bash
streamlit run app.py
```

## Technologies

Python · Streamlit · DuckDB · Pandas · PyYAML · DeepSeek · DeepInfra


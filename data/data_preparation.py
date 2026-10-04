import pandas as pd

excel_file_path = 'data/raw/theguardianranking.xlsx'
ranking = pd.read_excel(excel_file_path, sheet_name="The Guardian Ranking")
subject_areas = pd.read_excel(excel_file_path, sheet_name="The Guardian - Subject Areas")


# Rename columns
rename_overall = {
    'Ranking Year': 'ranking_year',
    'Ranking': 'rank_current',
    'Ranking (Prev)': 'rank_previous',
    'Ranking Change': 'rank_change',
    'Institution': 'university_name',
    'Guardian score/100': 'guardian_score',
    'NSS Teaching (%)': 'satisfaction_teaching',
    'NSS Overall (%)': 'satisfaction_overall',
    'Expenditure per student / 10': 'spend_per_student',
    'Student:staff ratio': 'student_staff_ratio',
    'Career prospects (%)': 'career_prospects',
    'Value added score/10': 'value_added_score',
    'Entry Tariff': 'entry_tariff',
    'NSS Feedback (%)': 'satisfaction_feedback'
}

rename_subjects = {
    'Subject Area Year': 'ranking_year',
    'Subject Area': 'subject_name',
    'Subject Area Rank': 'subject_rank_current',
    'Subject Area Rank (Prev)': 'subject_rank_previous',
    'Subject Area Rank Change': 'subject_rank_change',
    'Institution': 'university_name',
    'Guardian score/100': 'guardian_score',
    '% Satisfied with Teaching': 'satisfaction_teaching',
    '% Satisfied overall with course': 'satisfaction_overall',
    'Expenditure per student (FTE)': 'spend_per_student',
    'Student:staff ratio': 'student_staff_ratio',
    'Career prospects': 'career_prospects',
    'Value added score/10': 'value_added_score',
    'Average Entry Tariff': 'entry_tariff',
    '% Satisfied with Assessment': 'satisfaction_assessment'
}

ranking = ranking.rename(columns=rename_overall)
subject_areas = subject_areas.rename(columns=rename_subjects)

# Data descriptions
print(ranking.info())
print(subject_areas.info())

# Missing values
print(ranking.isna().sum())
print(subject_areas.isna().sum())

# Checking for duplicates
print("Ranking:", ranking.duplicated().sum())
print("Subject areas:", subject_areas.duplicated().sum())

# Identifying missing pairs in the ranking table
ranking_pairs = set(zip(ranking['university_name'], ranking['ranking_year']))
subject_pairs = set(zip(subject_areas['university_name'], subject_areas['ranking_year']))
missing_in_ranking = subject_pairs - ranking_pairs
print(missing_in_ranking)
missing_df = pd.DataFrame(list(missing_in_ranking), columns=['university_name', 'ranking_year'])
ranking_padded = pd.concat([ranking, missing_df], ignore_index=True)

# Saving cleaned data to CSV files
ranking_padded.to_csv("data/cleaned/ranking.csv",index=False)
subject_areas.to_csv("data/cleaned/subject_areas.csv",index=False)





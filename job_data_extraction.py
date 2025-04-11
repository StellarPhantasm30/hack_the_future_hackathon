import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()

jd_base_directory = os.environ.get("JD_BASE_DIRECTORY")
db = os.getenv("DB_NAME")

def insert_jd_data():
    jd = pd.read_excel(jd_base_directory)

    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_listings (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            job_description TEXT,
            title_and_description TEXT, 
            description_summary TEXT,
            summary_execution_time_minutes REAL
        )
    ''')

    for _, row in jd.iterrows():
        job_title = row['Job Title'].strip()
        job_description = row['Job Description'].strip()
        title_and_jd = "JobTitle: " + job_title + "\nJob " + job_description
    # Insert the candidate data into the table
        cursor.execute('''
            INSERT INTO job_listings (job_title, job_description, title_and_description)
            VALUES (?, ?, ?)
        ''', (job_title, job_description, title_and_jd))

    conn.commit()
    conn.close()

def main():
    insert_jd_data()


if __name__ == "__main__":
    main()
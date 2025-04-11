from ollama import ChatResponse, chat
import time
import sqlite3
import logging
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_NAME")
OLLAMA_MODEL = "gemma3:12b"
PROMPT_TEMPLATE = """Extract key skills, required experience, minimum education, desired certifications, main responsibilities, and job title from this job description, focusing on terms relevant to candidate matching.
Job Description:
{job_description_text}
Only reply with the extracted information in a clear text format."""

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_llm_summary(job_id: int, job_text: str):

    logger.info(f"Processing job ID: {job_id}")
    start = time.monotonic()
    summary = None
    time_taken = 0.0
    message = {
        "role": "user",
        "content": PROMPT_TEMPLATE.format(job_description_text=job_text),
    }
    response: ChatResponse = chat(
        model="gemma3:12b",
        messages=[message],
        options={"temperature": 0.2, "top_k": 30, "top_p": 0.95},
    )

    summary = response.message.content

    end = time.monotonic()
    time_taken = round((end - start) / 60, 2)
    logger.info(
        f"Received summary for resume ID: {job_id} Time Taken: {time_taken} minutes"
    )
    return (summary, time_taken)


def resume_extraction_function(cursor: sqlite3.Cursor):

    cursor.execute(
        """SELECT job_id, title_and_description FROM job_listings WHERE description_summary IS NULL"""
    )

    descriptions = cursor.fetchall()
    logger.info(f"Fetched {len(descriptions)} job descriptions to process.")
    return descriptions


def summary_insertion_function(
    summary: str,
    time_taken: float,
    cursor: sqlite3.Cursor,
    conn: sqlite3.Connection,
    job_id: int,
):
    cursor.execute(
        """UPDATE job_listings SET description_summary = ?, summary_execution_time_minutes = ? WHERE job_id = ?""",
        (summary, time_taken, job_id),
    )
    conn.commit()
    logger.info(f"Successfully updated summary for resume ID: {job_id}")


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    resumes = resume_extraction_function(cursor)

    for resume_id, resume_text in resumes:
        summary, time_taken = get_llm_summary(resume_id, resume_text)
        summary_insertion_function(summary, time_taken, cursor, conn, resume_id)

    conn.close()


if __name__ == "__main__":
    main()

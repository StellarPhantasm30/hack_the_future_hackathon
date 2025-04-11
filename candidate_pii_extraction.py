from ollama import ChatResponse, chat
import time
import sqlite3
import logging
import os
from dotenv import load_dotenv
import json

load_dotenv()

DB_PATH = os.getenv("DB_NAME")
OLLAMA_MODEL = "gemma3:12b"
PROMPT_TEMPLATE = """Extract phone number and email from below resume.
Resume:
{resume_text}
Only reply in json format don't add```json```:
Example:
{{"phone_number": "1234567890"}},
{{"email: "example@abc.com"}}
"""

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_llm_summary(candidate_id: int, cv_text: str):

    logger.info(f"Processing job ID: {candidate_id}")
    start = time.monotonic()
    time_taken = 0.0
    message = {
        "role": "user",
        "content": PROMPT_TEMPLATE.format(resume_text=cv_text),
    }
    response: ChatResponse = chat(
        model="gemma3:12b",
        messages=[message],
        options={"temperature": 0.1, "top_k": 30, "top_p": 0.95},
    )

    string_pii_data = response.message.content
    string_pii_data = string_pii_data.replace("json", "").replace("```", "").strip()
    try:
        dict_pii_data = json.loads(string_pii_data)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON response: {string_pii_data}, for resume ID: {candidate_id}")
        dict_pii_data = {}

    end = time.monotonic()
    time_taken = round((end - start), 2)
    logger.info(
        f"Received PII data for resume ID: {candidate_id} Time Taken: {time_taken} seconds"
    )
    return dict_pii_data


def resume_extraction_function(cursor: sqlite3.Cursor):

    cursor.execute(
        """SELECT candidate_id, structured_cv_data FROM candidates WHERE email_id IS NULL"""
    )

    descriptions = cursor.fetchall()
    logger.info(f"Fetched {len(descriptions)} CVs to process.")
    return descriptions


def summary_insertion_function(
    phone: str,
    email_id: str,
    cursor: sqlite3.Cursor,
    conn: sqlite3.Connection,
    candidate_id: int,
):
    cursor.execute(
        """UPDATE candidates SET email_id = ?, phone_number = ? WHERE candidate_id = ?""",
        (email_id, phone, candidate_id),
    )
    conn.commit()
    logger.info(f"Successfully updated email and phone number for resume ID: {candidate_id}")


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    resumes = resume_extraction_function(cursor)

    for resume_id, resume_text in resumes:
        dict_pii_data = get_llm_summary(resume_id, resume_text)
        phone_number = dict_pii_data.get("phone_number", None)
        email = dict_pii_data.get("email", None)
        logger.info(f"Extracted PII data: {dict_pii_data}")
        if phone_number is None or email is None:
            logger.warning(f"Failed to extract PII data for resume ID: {resume_id}")
            continue
        summary_insertion_function(phone_number, email, cursor, conn, resume_id)

    conn.close()


if __name__ == "__main__":
    main()

import sqlite3
import os
from dotenv import load_dotenv
import logging
import json
from pathlib import Path
from ollama import ChatResponse, chat
import time
from datetime import datetime

load_dotenv()

DB_PATH = os.getenv("DB_NAME")
OLLAMA_MODEL = "deepseek-r1:14b"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """Generate a customized email to send to shortlisted candidates for the next interview round. The email should be tailored to the specific job title and description provided. The company name is Ai Whisperers and hiring manager name is Aditya. Use a generic salutation like 'Hi' (do not include candidate names). Include scheduling options and a professional tone. Use {date} as the proposed date for interview.
{title_and_description}
Only reply in json format don't add```json```:
Example:
{{"email": "<customised email>"}}
"""

def get_custom_email():
    current_date = datetime.now().strftime("%d/%m/%y")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = """Select job_id, title_and_description from job_listings WHERE custom_emails IS NULL"""

    cursor.execute(query)
    descriptions = cursor.fetchall()

    conn.commit()
    conn.close()
    logger.info(f"Fetched {len(descriptions)} job title and descriptions to process.")

    for job_id, title_and_description in descriptions:

        logger.info(f"Processing job ID: {job_id}")

        message = {
            "role": "user",
            "content": PROMPT_TEMPLATE.format(title_and_description=title_and_description, date=current_date),
        }
        start = time.monotonic()
        response: ChatResponse = chat(
            model=OLLAMA_MODEL,
            messages=[message],
            options={"temperature": 0.1, "top_k": 25, "top_p": 0.95},
        )
        end = time.monotonic()
        time_taken = round((end - start)/60, 2)
        logger.info(f"Time taken for generating custom email for job_id:{job_id} is {time_taken} minutes")

        response = response.message.content
        response = response.split("</think>")[1].strip()
        logger.info("Before String manipulation: " + response)
        response = response.replace("json", "").replace("```", "").strip()
        try:
            email = json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {email}, for resume ID: {job_id}")
            email = {}
        insert_custom_email(email, job_id)

def insert_custom_email(custom_email, job_id):
    if custom_email is None or len(custom_email) == 0:
        logger.error(f"Custom email is None or empty for job id: {job_id}")
        return
    
    email = custom_email["email"]

    if(isinstance(email,dict)):
        email = email.get("email", None)
        if email is None:
            logger.error(f"Custom email is not present in the dictionary for Job id: {job_id}")
            return

    if not (isinstance(email,str)):
        logger.error(f"Custom email is not of String type for Job id: {job_id}, type:{type(email)}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """UPDATE job_listings SET custom_emails = ? WHERE job_id = ?"""

    cursor.execute(query, (email, job_id))

    conn.commit()
    conn.close()
    logger.info(f"Email updated to db for job id: {job_id}")

def main():
    get_custom_email()

if __name__ == "__main__":
    main()
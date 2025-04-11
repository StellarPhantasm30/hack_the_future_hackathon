import os
from pathlib import Path
import sqlite3
import logging
from dotenv import load_dotenv
import json
import math
from ollama import ChatResponse, chat
import time
from typing import List, Dict, Tuple
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

DB_PATH = os.getenv("DB_NAME")

PROMPT_TEMPLATE = """"Analyze the provided job description and candidate CV. Provide a match score (0-100) and a brief reason for the score in JSON format.
Job Description: {job_description}
Candidate CV: {cv_text}
Only reply in json format don't add```json```:
Output JSON: {{\"match_score\": <score>, \"reason\": \"<reason>\"}}"
"""

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_job_description() -> List[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """ SELECT job_id, description_summary FROM job_listings WHERE selected_email_ids IS NULL """
    cursor.execute(query)

    job_descriptions = cursor.fetchall()

    conn.commit()
    conn.close()
    logger.info("Fetched Job ID and Job Descriptions from the database.")
    return job_descriptions

def insert_selected_candidates(email_ids_string: str, job_id: str, email_id_reason_dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """UPDATE job_listings SET selected_email_ids = ? WHERE job_id = ?"""
    cursor.execute(query, (email_ids_string, job_id))

    # Candidates table update
    
    for email_id, reason in email_id_reason_dict.items():
        logger.info(f"Updating candidate status for email_id: {email_id}")
        query = f'''UPDATE candidates SET status = "shortlisted", outcome_reason = "{reason}" WHERE email_id = ? AND status IS NULL'''
        cursor.execute(query, (email_id,))
    conn.commit()
    conn.close()

def calculate_cv_job_score(job_description, cv, email_id):

        message = {
            "role": "user",
            "content": PROMPT_TEMPLATE.format(job_description=job_description, cv_text = cv),
        }
        start = time.monotonic()
        response: ChatResponse = chat(
            model="deepseek-r1:14b",
            messages=[message],
            options={"temperature": 0.1, "top_k": 25, "top_p": 0.95},
        )
        end = time.monotonic()
        time_taken = round((end - start)/60, 2)
        logger.info(f"Time taken for generating score and reason for email_id:{email_id} is {time_taken} minutes")

        response = response.message.content
        response = response.split("</think>")[1].strip()
        logger.info("Before String manipulation: " + response)
        response = response.replace("json", "").replace("```", "").strip()

        try:
            score_and_reason = json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {score_and_reason}, for Email ID: {email_id}")
            score_and_reason = {}

        return score_and_reason

def utility(job_id:int, job_description: str, vector_store) -> None:

    logger.info(f"similarity search starting for Job ID{job_id}.....")
    top_cv_documents = vector_store.similarity_search(job_description,
        k=6,
        # filter={"source": ""},
    )
    
    email_id_reason_dict = {}
    email_ids_string = ""

    for cv_doc in top_cv_documents:
        cv = cv_doc.page_content
        email_id = cv_doc.metadata["email_id"]
        cv_filename = cv_doc.metadata["cv_filename"]
        logger.info(f"Started processing Resume: {cv_filename} with Email: {email_id} against Job ID: {job_id}")
        
        score_and_reason = calculate_cv_job_score(job_description, cv, email_id)

        if score_and_reason is None:
            logger.error(f"Failed to calculate score for email_id: {email_id}")

        match_score = score_and_reason.get("match_score", None)
        reason = score_and_reason.get("reason", None)

        if match_score is None:
            logger.error(f"Match score is None for email_id: {email_id}")
            
        if reason is None:
            logger.error(f"Reason is None for email_id: {email_id}")

        if math.ceil(match_score) >= 80:
            email_ids_string = email_ids_string + "||" + email_id
            email_id_reason_dict[email_id] = reason
    insert_selected_candidates(email_ids_string, job_id, email_id_reason_dict)        


def main():
    
    logger.info("Setting up the model and vector store.....")
    model_kwargs = {"device": "cpu", "trust_remote_code": True}
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL, model_kwargs=model_kwargs
    )

    vector_store = FAISS.load_local(
        "faiss_index", embeddings, allow_dangerous_deserialization=True
    )

    logger.info("Set up completed.....")

    for jobid_and_description in get_job_description():
        job_id = jobid_and_description[0]
        job_description = jobid_and_description[1].strip()
        
        utility(job_id, job_description, vector_store)
    print("_" * 60)

if __name__ == "__main__":
    main()
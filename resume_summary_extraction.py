from ollama import ChatResponse, chat
from pathlib import Path
import time
import sqlite3
import logging

DB_PATH = Path("candidates.db")
OLLAMA_MODEL = 'gemma3:12b'
PROMPT_TEMPLATE = """Extract key skills, experience, education, certifications, achievement and job titles from this resume, focusing on terms relevant to job matching.
Resume:
{resume_text}
Only reply with the extracted information in a clear text format."""

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_llm_summary(resume_id: int, resume_text: str):

    logger.info(f"Processing resume ID: {resume_id}")
    start = time.monotonic()
    summary = None
    time_taken = 0.0
    message = {'role': 'user',
                'content': PROMPT_TEMPLATE.format(resume_text= resume_text)}
    response: ChatResponse = chat(model='gemma3:12b',
                                    messages=[message],
                                    options={'temperature': 0.2, 'top_k': 30, 'top_p': 0.95})

    summary = response.message.content

    end = time.monotonic()
    time_taken = round((end - start)/60, 2)
    logger.info(f"Received summary for resume ID: {resume_id} Time Taken: {time_taken} minutes")
    return (summary, time_taken)

def resume_extraction_function(cursor: sqlite3.Cursor):

  cursor.execute('''SELECT candidate_id, structured_cv_data FROM candidates WHERE cv_summary IS NULL''')

  resumes = cursor.fetchall()
  logger.info(f"Fetched {len(resumes)} resumes to process.")
  return resumes

def summary_insertion_function(summary:str, time_taken: float, cursor: sqlite3.Cursor, conn: sqlite3.Connection, resume_id: int):
  cursor.execute('''UPDATE candidates SET cv_summary = ?, summary_execution_time_minutes = ? WHERE candidate_id = ?''',(summary, time_taken, resume_id))
  conn.commit()
  logger.debug(f"Successfully updated summary for resume ID: {resume_id}")
     

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
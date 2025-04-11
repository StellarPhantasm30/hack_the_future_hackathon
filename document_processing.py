import time
from pathlib import Path
import sqlite3
import os
from dotenv import load_dotenv

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.models.tesseract_ocr_model import TesseractOcrOptions

load_dotenv()

def insert_candidate(cv_filename, structured_cv_data, ocr_time_taken):
    db = os.getenv("DB_NAME")
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cv_filename TEXT,
            structured_cv_data TEXT,
            cv_summary TEXT,
            outcome_reason TEXT,
            status TEXT,
            ocr_execution_time_seconds REAL,
            summary_execution_time_minutes REAL
        )
    ''')

    # Insert the candidate data into the table
    cursor.execute('''
        INSERT INTO candidates (cv_filename, structured_cv_data, ocr_execution_time_seconds)
        VALUES (?, ?, ?)
    ''', (cv_filename, structured_cv_data, ocr_time_taken))

    conn.commit()
    conn.close()

def main():
    root = os.getenv("CV_BASE_DIRECTORY")

    for file in os.listdir(root):
        if file.lower().endswith(".pdf"):
            input_doc_path = Path(root, file)

            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.do_table_structure = True
            pipeline_options.table_structure_options.do_cell_matching = True
            pipeline_options.ocr_options = TesseractOcrOptions()

            doc_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            start_time = time.time()
            conv_result = doc_converter.convert(input_doc_path)

            ## Export results
            output_dir = Path("scratch")
            output_dir.mkdir(parents=True, exist_ok=True)
            doc_filename = conv_result.input.file.stem

            cv_data = conv_result.document.export_to_text()
            end_time = time.time() - start_time
            time_taken = round(end_time, 2)


            insert_candidate(cv_filename=doc_filename,
                            structured_cv_data=cv_data,
                            ocr_time_taken=time_taken,
                            )



if __name__ == "__main__":
    main()
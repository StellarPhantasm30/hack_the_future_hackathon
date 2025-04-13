# ResumeLens AI

**Problem:** Manually screening hundreds of resumes for multiple job openings is a time-consuming, tedious, and potentially biased process for recruiters.

**Solution:** This project implements an automated multi-agent workflow to intelligently process candidate resumes against job descriptions, identify the best matches, and even draft initial outreach emails, significantly speeding up the initial stages of the hiring pipeline.

---

## ✨ Features

- **Automated Resume Parsing:** Extracts text content from PDF resumes using OCR.
- **PII Extraction:** Identifies and extracts personal information (Name, Email, Phone Number) from resumes using local LLM (Ollama).
- **Key Information Extraction:** Uses LLM (Ollama) to extract key skills/summaries from resumes and key requirements/points from job descriptions.
- **Semantic Matching:** Creates dense vector embeddings for resumes and utilizes HNSW clustering and semantic similarity to find the most relevant candidates for each job description, followed by local reasoning models to generate detailed match scores and justifications, all stored in the database.
- **Custom Email Generation:** Automatically generates personalized draft outreach emails tailored to each specific job description using LLM (Ollama).
- **Centralized Database:** Stores all processed information (candidate details, job details, extracted points, matches, emails) in an SQLite database.
- **Interactive Dashboard:** A Streamlit UI (`01_DashBoard.py`) to visualize the results, showcasing matched candidates and generated emails for each job.

---

## 🛠️ Tech Stack

- **Backend:** Python
- **AI/LLM:** Ollama (for local large language/reasoning model inference)
- **Vector Database/Search:** `HNSW` (implemented via `Faiss`) for efficient similarity search.
- **Data Processing:** Pandas
- **Database:** SQLite3
- **PDF Processing/OCR:** Docling with `Tesseract`
- **Frontend:** Streamlit

---

## ⚙️ Workflow Overview

The system follows a multi-step process orchestrated by different Python scripts:

1.  **Job Data Ingestion (`job_data_extraction.py`):** Reads job titles and descriptions from the input CSV file and stores to DB.
2.  **Job Analysis (`job_summary_extraction.py`):** Extracts key requirements and points from each job description using Ollama and stores them in the `job_listings` table in `candidates.db`.
3.  **Resume Ingestion & OCR (`document_processing.py`):** Processes input PDF resumes, performs OCR to extract text content, and stores the raw text (or path) in the `candidates` table in `candidates.db`.
4.  **Resume PII Extraction (`candidate_pii_extraction.py`):** Analyzes resume text using Ollama to find and store candidate email addresses and phone numbers in the `candidates` table.
5.  **Resume Analysis (`resume_summary_extraction.py`):** Extracts key skills and summaries from resume text using Ollama and stores them in the `candidates` table.
6.  **Vectorization (`resume_vector_db.py`):** Creates vector embeddings for the processed resumes (based on extracted text/skills) and builds a searchable vector index (HNSW).
7.  **Matching & Scoring (`resume_matching.py`):** Compares job description key points against the resume vector index using HNSW to identify and get top matching candidates for each job, followed by local reasoning models to generate detailed match scores and justifications, all stored in the database in the `job_listings` table.
8.  **Email Generation (`email_templating.py`):** Creates tailored draft outreach emails for each job description using Ollama, incorporating job key points, and stores them in the `job_listings` table.
9.  **Visualization (`01_DashBoard.py`):** A Streamlit application reads the processed data from `candidates.db` to provide an interactive interface for exploring job listings, their key points, the matched candidates, and the generated emails.

---

## 🚀 Getting Started (Demo Showcase)

This guide focuses on running the Streamlit dashboard to showcase the _pre-processed results_. The backend scripts require specific setup (Ollama, Python environment, input data) and are intended to be run beforehand to populate the database.

1.  **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Set up Python Environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Place the Database:**

    - Ensure the pre-generated SQLite database file named `candidates.db` (containing the results from running the backend scripts) is placed in the root directory of this repository. **This file is crucial for the dashboard to work.**

5.  **Run the Streamlit Dashboard:**

    ```bash
    streamlit run 01_DashBoard.py
    ```

6.  **View:** Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`). Explore the processed jobs, matched candidates, and generated emails!

---

## 📊 Data

- **Input:** The system is designed to process PDF resumes and a CSV file containing job titles and descriptions. (These are expected to be in the `Data/` directory but are gitignored).
- **Output:** All processed data, extracted insights, candidate matches, and generated emails are stored in the `candidates.db` SQLite database. Resume vector embeddings are stored separately (in `faiss_index/`, also gitignored). For convenient analysis, the `candidates` and `job_listings` tables from candidates.db have been exported to `candidates.xlsx` and `job_listings.xlsx` respectively."

Here's a demo of my project: [My Video Demo](https://drive.google.com/file/d/1ypdSPwPE9ub_p9pRuHi4NJzyWH9jiHe3/view?usp=drivesdk)

## License

This project is built for the [Hack the Future] Hackathon and is not licensed for commercial use.

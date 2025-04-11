import streamlit as st
import pandas as pd
import sqlite3  # Or your specific DB connector (psycopg2 for PostgreSQL, etc.)
from pathlib import Path  # To potentially show resume filenames if needed
from dotenv import load_dotenv
import os

# --- Configuration ---
load_dotenv()

DB_PATH = os.getenv("DB_NAME")


@st.cache_resource
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None


@st.cache_data
def load_job_listings():
    """Loads basic info for all job listings."""
    conn = get_db_connection()
    if conn:
        try:
            query = "SELECT job_id, job_title FROM job_listings"
            df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            st.error(f"Error loading job listings: {e}")
            return pd.DataFrame()
        # finally: # Don't close connection here if reused
        #     conn.close() # Close connection if not reused elsewhere
    return pd.DataFrame()


@st.cache_data
def load_job_details(job_id):
    """Loads full details for a specific job listing."""

    conn = get_db_connection()
    if conn:
        try:
            query = "SELECT * FROM job_listings WHERE job_id = ?"
            cursor = conn.cursor()
            cursor.execute(query, (job_id,))
            job_data = cursor.fetchone()
            return dict(job_data) if job_data else None
        except Exception as e:
            st.error(f"Error loading job details for {job_id}: {e}")
            return None
        # finally:
        #     conn.close()
    return None


@st.cache_data
def load_candidate_details(email):
    """Loads details for a specific candidate by email."""
    conn = get_db_connection()
    if conn:
        try:
            query = "SELECT candidate_id, cv_filename, structured_cv_data, cv_summary, email_id, phone_number, status, outcome_reason FROM candidates WHERE email_id = ?"
            cursor = conn.cursor()
            cursor.execute(query, (email,))
            candidate_data = cursor.fetchone()
            return dict(candidate_data) if candidate_data else None
        except Exception as e:
            st.error(f"Error loading candidate details for {email}: {e}")
            return None
        # finally:
        #     conn.close()
    return None


# --- Streamlit App Layout ---

st.set_page_config(
    layout="wide",
    page_title="Resume Processing Showcase",
    initial_sidebar_state="collapsed",
    page_icon="📄",
)

st.title("📄:violet[ **_ResumeLens AI_**]")
# st.header(":violet[**_ResumeLens AI_**]", divider="violet")
st.markdown(
    "**This dashboard showcases the results of our multi-agent system that processes resumes against job descriptions.**"
)

st.sidebar.header("Explore Results")

# --- Job-Centric View ---
st.sidebar.subheader("View by Job")
job_listings_df = load_job_listings()

if not job_listings_df.empty:
    # Create a mapping from a user-friendly display string to the j_id

    job_options = {
        f"{row['job_id']}: {row['job_title']}": row["job_id"]
        for _, row in job_listings_df.iterrows()
    }
    selected_job_display = st.sidebar.selectbox(
        "Select a Job Listing:", options=list(job_options.keys()), index=0
    )
    selected_job_id = job_options[selected_job_display]

    st.header(f"Analysis for Job ID: {selected_job_id}")
    job_details = load_job_details(selected_job_id)

    if job_details:
        tab1, tab2, tab3 = st.tabs(
            [
                "📋 Job Details & Key Points",
                "👥 Matched Candidates",
                "✉️ Generated Email",
            ]
        )

        with tab1:
            st.subheader("Original Job Description")
            st.text_area(
                "Description",
                job_details["title_and_description"],
                height=200,
                disabled=True,
                key=f"desc_{selected_job_id}",
            )
            st.subheader("✨ Extracted Key Points")
            st.markdown(job_details["description_summary"])
        with tab2:
            st.subheader("✅ Top Candidate Matches")
            emails_str = job_details.get("selected_email_ids", "")
            if emails_str:
                candidate_emails = [
                    email.strip() for email in emails_str.split("||") if email.strip()
                ]
                st.info(
                    f"Found {len(candidate_emails)} potential matches for this role."
                )

                candidate_to_view = st.selectbox(
                    "Select a candidate email to see details:",
                    options=["Select..."] + candidate_emails,
                    key=f"cand_select_{selected_job_id}",
                )

                if candidate_to_view != "Select...":
                    candidate_data = load_candidate_details(candidate_to_view)
                    if candidate_data:
                        with st.expander(
                            f"Details for  {candidate_to_view}", expanded=True
                        ):
                            # st.write(f"Email: {candidate_data['email_id']}")
                            st.write(
                                f"Phone: {candidate_data.get('phone_number', 'N/A')}"
                            )
                            st.write(
                                f"📄 Resume File: {candidate_data.get('cv_filename', 'N/A')}"
                            )
                            st.write("🔑 Extracted Key Skills:")
                            st.markdown(candidate_data.get("cv_summary", "N/A"))
                            st.write(f"Status: {candidate_data.get('status', 'N/A')}")
                            st.write(
                                f"##### Reason:\n {candidate_data.get('outcome_reason', 'N/A')}"
                            )
                    else:
                        st.warning(f"Could not load details for {candidate_to_view}")
                else:
                    # Display the list if none is selected for details view
                    st.dataframe(
                        pd.DataFrame({"Matched Candidate Emails": candidate_emails}),
                        use_container_width=True,
                    )

            else:
                st.warning(
                    "No candidates were selected/matched for this job based on the stored data."
                )

        with tab3:
            st.subheader("📧 Generated Outreach Email")
            # Assuming customized_emails contains the email body for this job
            st.text_area(
                "Email Content",
                job_details.get("custom_emails", "No email generated/stored."),
                height=300,
                disabled=True,
                key=f"email_{selected_job_id}",
            )

    else:
        st.error(f"Could not load details for Job ID {selected_job_id}.")

else:
    st.sidebar.warning("No job listings found in the database.")
    st.warning("No job listings loaded. Cannot display job-centric view.")

st.sidebar.divider()
st.sidebar.subheader("View by Candidate")

# --- About Section ---
st.sidebar.divider()
with st.sidebar.expander("ℹ️  About the System"):
    st.markdown(
        """
    This system uses a multi-agent workflow to automatically:
    1.  Parse resumes (PDFs).
    2.  Extract key skills & contact info.
    3.  Analyze job descriptions for key requirements.
    4.  Match candidates to relevant jobs using clustering and semantic similarity.
    5.  Generate draft outreach emails for each listed job.

    This UI reads the processed data directly from the backend database.
    """
    )

# --- Final Touches ---
# Close the connection when the script finishes if it wasn't closed earlier
# conn = get_db_connection()
# if conn:
#     conn.close()
# Note: With Streamlit's execution model, managing connection state can be tricky.
# Using a context manager or ensuring functions close cursors might be better in complex apps.
# For a simple demo, leaving the connection open via @st.cache_data might be acceptable.

import os
from dotenv import load_dotenv
import sqlite3
from uuid import uuid4
import faiss
import logging
from ollama import ChatResponse, chat

from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

DB_PATH = os.getenv("DB_NAME")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_vector_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""Select cv_summary, cv_filename, email_id from candidates""")
    resume_details = cursor.fetchall()
    conn.commit()
    conn.close()

    documents = []

    for resume_detail in resume_details:
        
        cv_summary = resume_detail[0].strip()
        cv_filename = resume_detail[1].strip()
        email_id = resume_detail[2].strip()
        documents.append(
            Document(
                page_content=cv_summary,
                metadata={"cv_filename": cv_filename, "email_id": email_id},
            )
        )

    print(len(documents))
    uuids = [str(uuid4()) for _ in range(len(documents))]

    model_kwargs = {"device": "cpu", "trust_remote_code": True}
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL, model_kwargs=model_kwargs
    )

    dimension = len(embeddings.embed_query("hello world"))
    index = faiss.IndexHNSWFlat(dimension, 32)
    index.hnsw.efConstruction = 200
    index.hnsw.efSearch = 64

    print("embedding dimension: ", dimension)

    vector_store = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
    )

    vector_store.add_documents(documents=documents, ids=uuids)
    logger.info("documents converted to embeddings and added to vector database")

    vector_store.save_local("faiss_index")
    logger.info("database stored locally")


if __name__ == "__main__":
    create_vector_db()
import sqlite3
import numpy as np
import faiss
import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain_groq import ChatGroq
from langchain.schema import BaseRetriever
from langchain.schema import Document as LangChainDocument

# Set up logging
logging.basicConfig(
    filename=os.path.join('logs', 'rag_engine.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY not found in .env file")
    sys.exit(1)

# Database path
DB_DIR = "DB"
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "faces.db")

# Custom retriever that passes all documents to the LLM
class AllDocumentsRetriever(BaseRetriever):
    def __init__(self, documents):
        super().__init__()
        self._documents = documents

    def _get_relevant_documents(self, query):
        return self._documents

    async def _aget_relevant_documents(self, query):
        return self._documents

# Fetch face data from SQLite
def fetch_face_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, encoding, timestamp FROM faces')
        rows = cursor.fetchall()
        conn.close()
        logging.info(f"Fetched {len(rows)} rows from database")
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        logging.error(f"Database error: {e}")
        return []

# Convert face data to LangChain Documents and prepare embeddings
def prepare_documents_and_embeddings(face_data):
    documents = []
    embeddings = []
    for row in face_data:
        name, timestamp = row[1], row[3]
        encoding = np.frombuffer(row[2], dtype=np.float64)
        if encoding.shape[0] != 128:
            logging.warning(f"Invalid encoding size for ID {row[0]}: {encoding.shape[0]}")
            continue
        embeddings.append(encoding)
        text = f"Person: {name}, Timestamp: {timestamp}"
        metadata = {"name": name, "timestamp": timestamp if timestamp else "Unknown", "id": row[0]}
        documents.append(LangChainDocument(page_content=text, metadata=metadata))

    # Sort documents by timestamp (newest first)
    try:
        documents.sort(
            key=lambda x: datetime.strptime(
                x.metadata["timestamp"], "%Y-%m-%d %H:%M:%S"
            ) if x.metadata["timestamp"] != "Unknown" else datetime.min,
            reverse=True
        )
    except ValueError as e:
        logging.error(f"Error sorting documents by timestamp: {e}")
        print(f"Error sorting documents by timestamp: {e}")

    # Log the documents for debugging
    logging.info("Documents prepared for RAG:")
    for doc in documents:
        logging.info(f"Content: {doc.page_content}, Metadata: {doc.metadata}")

    return documents, embeddings

# Build FAISS index for face encodings
def build_faiss_index(embeddings):
    if not embeddings:
        return None
    embeddings = np.array(embeddings, dtype=np.float32)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index

# Set up the RAG engine using Groq
def create_rag_engine():
    face_data = fetch_face_data()
    if not face_data:
        logging.warning("No faces registered in database")
        return None

    documents, embeddings = prepare_documents_and_embeddings(face_data)
    faiss_index = build_faiss_index(embeddings)  # For face encodings, not text queries

    retriever = AllDocumentsRetriever(documents)

    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.2,
        max_tokens=200
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are a helpful assistant with access to a database of registered people. "
            "The context below contains information about each person, including their name and registration timestamp in the format 'YYYY-MM-DD HH:MM:SS'. "
            "The documents are sorted from newest to oldest by timestamp. "
            "Answer the question based on this context, performing any necessary calculations or sorting. "
            "For example, you can count the number of people, identify the most recent registration, extract timestamps, or list names. "
            "If a timestamp is 'Unknown' or missing, note that it affects ordering or timing-related answers. "
            "If the question cannot be answered due to missing information, explain why.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        )
    )

    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt}
    )
    return rag_chain

# Run query
def process_query(query):
    logging.info(f"Processing query: {query}")
    rag_engine = create_rag_engine()
    if not rag_engine:
        return "No face data available."
    try:
        response = rag_engine.invoke(query)
        answer = response["result"]
        logging.info(f"Query response: {answer}")
        return answer
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return f"Error: {e}"

def main():
    if len(sys.argv) != 2:
        print("Usage: python rag_engine.py '<your question>'")
        sys.exit(1)
    query = sys.argv[1]
    answer = process_query(query)
    print(answer)

if __name__ == "__main__":
    main()
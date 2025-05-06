import sqlite3
import numpy as np
import faiss
import sys
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain.schema import BaseRetriever
from langchain.schema import Document as LangChainDocument

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY not found in .env file")
    sys.exit(1)

# Define paths
DB_DIR = "DB"
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "faces.db")

# Custom retriever that passes all documents to the LLM
class AllDocumentsRetriever(BaseRetriever):
    def __init__(self, documents):
        super().__init__()
        # Store documents as an instance variable without Pydantic validation
        self._documents = documents

    def _get_relevant_documents(self, query):
        """Return all documents for the LLM to interpret."""
        return self._documents

    async def _aget_relevant_documents(self, query):
        """Async version of _get_relevant_documents (required by LangChain)."""
        return self._documents

# Function to fetch face data from the database
def fetch_face_data():
    """Fetch face data (name, encoding, timestamp) from the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, encoding, timestamp FROM faces')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

# Prepare documents and embeddings for FAISS
def prepare_documents_and_embeddings(face_data):
    """Prepare LangChain Documents and embeddings for FAISS."""
    if not face_data:
        return [], []

    documents = []
    embeddings = []
    for row in face_data:
        # Convert BLOB to numpy array
        encoding = np.frombuffer(row[2], dtype=np.float64)
        if encoding.shape[0] != 128:
            continue
        embeddings.append(encoding)
        # Create a Document with metadata
        doc_content = f"Person: {row[1]}"
        doc_metadata = {"name": row[1], "timestamp": row[3], "id": row[0]}
        documents.append(LangChainDocument(page_content=doc_content, metadata=doc_metadata))

    return documents, embeddings

# Create a FAISS index (used for face encodings, not text retrieval)
def create_faiss_index(embeddings):
    """Create a FAISS index for face encodings."""
    if not embeddings:
        return None

    embeddings = np.array(embeddings, dtype=np.float32)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index

# Set up the RAG engine with LangChain and Groq
def create_rag_engine():
    """Set up the RAG engine with LangChain and Groq's LLM."""
    face_data = fetch_face_data()
    documents, embeddings = prepare_documents_and_embeddings(face_data)
    
    if not documents:
        return None

    # Create a FAISS index for face encodings (though not used for text retrieval here)
    faiss_index = create_faiss_index(embeddings)

    # Use a custom retriever that passes all documents to the LLM
    retriever = AllDocumentsRetriever(documents)

    # Initialize Groq's LLM via LangChain
    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=150
    )

    # Define the prompt template
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are a helpful assistant. Use the following context to answer the question. "
            "The context contains a list of registered people with their names and timestamps. "
            "Each entry is in the format 'Person: <name>' with metadata including 'timestamp' in the format 'YYYY-MM-DD HH:MM:SS'. "
            "Use the timestamps to determine the most recent registrations when needed.\n\n"
            "If a timestamp is 'Unknown' or missing, note that you cannot determine the order of registration for those entries. "
            "Use the timestamps to determine the most recent registrations when possible, assuming the list is already sorted from newest to oldest.\n\n"
            "{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        )
    )

    # Create the RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt_template}
    )

    return qa_chain

# Process the query using the RAG engine
def process_query(query):
    """Process the user's query using the RAG engine."""
    rag_engine = create_rag_engine()
    if not rag_engine:
        return "No faces registered yet. Please register a face first."

    try:
        # Run the query through the RAG engine using the updated method
        response = rag_engine.invoke(query)
        # Extract the answer from the response dictionary
        return response["result"]
    except Exception as e:
        return f"Error processing query: {e}"

def main():
    if len(sys.argv) != 2:
        print("Usage: python rag_engine.py <query>")
        sys.exit(1)

    query = sys.argv[1]
    response = process_query(query)
    print(response)

if __name__ == "__main__":
    main()
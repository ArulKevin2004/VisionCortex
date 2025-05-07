import os
import sys
import logging
import pickle
import json
import sqlite3
import argparse
import asyncio
import websockets
import string
import warnings
from datetime import datetime
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from transformers import logging as transformers_logging

# Suppress transformers warning
transformers_logging.set_verbosity_error()
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")

# Set up logging to file and console
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler
file_handler = logging.FileHandler(os.path.join(log_dir, "rag_engine.log"))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not found in .env file")
    print("Error: GROQ_API_KEY not found in .env file")
    sys.exit(1)
if not HUGGINGFACEHUB_API_TOKEN:
    logger.error("HUGGINGFACEHUB_API_TOKEN not found in .env file")
    print("Error: HUGGINGFACEHUB_API_TOKEN not found in .env file")
    sys.exit(1)
os.environ["HF_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Suppress tokenizers parallelism warning

# Database and cache paths
DB_DIR = "DB"
INDEX_DIR = "index"
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "faces.db")
INDEX_PATH = os.path.join(INDEX_DIR, "faiss_index.pkl")
DB_TIMESTAMP_PATH = os.path.join(INDEX_DIR, "db_timestamp.pkl")

# Fetch face data from SQLite
def fetch_face_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, encoding, timestamp FROM faces')
        rows = cursor.fetchall()
        conn.close()
        logger.info(f"Fetched {len(rows)} rows from database")
        return rows
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        print(f"Database error: {e}")
        return []

# Convert face data to LangChain Documents
def prepare_documents(face_data):
    documents = []
    for row in face_data:
        name, timestamp = row[1], row[3]
        text = f"Person: {name}, Timestamp: {timestamp}"
        metadata = {"name": name, "timestamp": timestamp if timestamp else "Unknown", "id": row[0]}
        documents.append(Document(page_content=text, metadata=metadata))

    # Sort documents by timestamp (newest first)
    try:
        documents.sort(
            key=lambda x: datetime.strptime(
                x.metadata["timestamp"], "%Y-%m-%d %H:%M:%S"
            ) if x.metadata["timestamp"] != "Unknown" else datetime.min,
            reverse=True
        )
    except ValueError as e:
        logger.error(f"Error sorting documents by timestamp: {e}")
        print(f"Error sorting documents by timestamp: {e}")

    logger.info("Documents prepared for FAISS:")
    for doc in documents:
        logger.info(f"Content: {doc.page_content}, Metadata: {doc.metadata}")

    return documents

# Check if database has changed
def get_db_timestamp():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(timestamp) FROM faces")
        max_timestamp = cursor.fetchone()[0]
        conn.close()
        return max_timestamp
    except sqlite3.Error:
        return None

# Build or load FAISS index
def build_vector_store(documents):
    try:
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
        os.makedirs(cache_dir, exist_ok=True)
        
        embeddings = HuggingFaceEmbeddings(
            model_name="multi-qa-MiniLM-L6-cos-v1",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        
        # Check if FAISS index exists and database hasn't changed
        current_db_timestamp = get_db_timestamp()
        cached_timestamp = None
        if os.path.exists(DB_TIMESTAMP_PATH):
            with open(DB_TIMESTAMP_PATH, "rb") as f:
                cached_timestamp = pickle.load(f)

        if os.path.exists(INDEX_PATH) and current_db_timestamp == cached_timestamp:
            logger.info("Loading cached FAISS index")
            with open(INDEX_PATH, "rb") as f:
                vectorstore = pickle.load(f)
        else:
            logger.info("Building new FAISS index")
            vectorstore = FAISS.from_documents(documents, embedding=embeddings)
            with open(INDEX_PATH, "wb") as f:
                pickle.dump(vectorstore, f)
            with open(DB_TIMESTAMP_PATH, "wb") as f:
                pickle.dump(current_db_timestamp, f)
        return vectorstore
    except Exception as e:
        logger.error(f"Error building FAISS vector store: {e}")
        print(f"MojoException: Error building FAISS vector store: {e}")
        sys.exit(1)

# Normalize query
def normalize_query(query):
    # General-purpose normalization: lowercase, strip whitespace, remove punctuation
    query = query.lower().strip()
    # Remove punctuation except for critical characters
    query = query.translate(str.maketrans("", "", string.punctuation.replace(":", "")))
    # Collapse multiple spaces
    query = " ".join(query.split())
    return query

# Set up the RAG engine
def create_rag_engine():
    face_data = fetch_face_data()
    if not face_data:
        logger.warning("No faces registered in database")
        return None

    documents = prepare_documents(face_data)
    vectorstore = build_vector_store(documents)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})  # Increased k for broader context

    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.2,
        max_tokens=200
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are a precise assistant with access to a database of registered people. "
            "The context contains names and registration timestamps in 'YYYY-MM-DD HH:MM:SS' format, sorted newest to oldest. "
            "Answer the question concisely based on the context. Handle a wide range of questions, including counting registrations, identifying earliest/latest registrations, extracting timestamps, listing people, or filtering by date/name. "
            "Interpret variations in phrasing (e.g., 'first' as 'earliest', 'last' as 'most recent'). "
            "If a timestamp is 'Unknown', note it affects timing answers. If the question cannot be answered, say so clearly with a brief explanation.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        )
    )

    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    return rag_chain

# Process query
def process_query(query):
    start_time = datetime.now()
    normalized_query = normalize_query(query)
    logger.info(f"Processing query: {query} (Normalized: {normalized_query})")
    rag_engine = create_rag_engine()
    if not rag_engine:
        logger.warning("No face data available")
        return "No face data available."
    try:
        response = rag_engine.invoke(normalized_query)
        answer = response["result"]
        sources = response["source_documents"]
        latency = (datetime.now() - start_time).total_seconds()
        logger.info(f"Query response: {answer}")
        logger.debug(f"Retrieved documents: {[doc.page_content for doc in sources]}")
        logger.info(f"Query execution time: {latency} seconds")
        # Log performance metrics
        logger.info(json.dumps({
            "query": query,
            "normalized_query": normalized_query,
            "latency": latency,
            "num_documents_retrieved": len(sources)
        }))
        return answer
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return f"Error: {e}"

# WebSocket handler
async def websocket_handler(websocket):
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                query = data.get("query")
                if not query:
                    await websocket.send(json.dumps({"error": "No query provided"}))
                    continue
                logger.info(f"Received WebSocket query: {query}")
                answer = process_query(query)
                await websocket.send(json.dumps({"answer": answer}))
                logger.info(f"Sent WebSocket response: {answer}")
            except json.JSONDecodeError:
                logger.error("Invalid JSON received in WebSocket message")
                await websocket.send(json.dumps({"error": "Invalid JSON format"}))
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send(json.dumps({"error": str(e)}))

# Start WebSocket server
async def main():
    server = await websockets.serve(websocket_handler, "localhost", 8765)
    logger.info("Starting WebSocket server on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Engine for Face Recognition Hackathon")
    parser.add_argument("--query", help="Run a single query")
    parser.add_argument("--websocket", action="store_true", help="Start WebSocket server")
    args = parser.parse_args()

    if args.websocket:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("WebSocket server stopped")
            sys.exit(0)
    elif args.query:
        answer = process_query(args.query)
        print(answer)
    else:
        print("Usage: python rag_engine.py --query '<your question>' or --websocket")
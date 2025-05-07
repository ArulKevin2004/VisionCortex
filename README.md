# VisionCortex: Face Recognition Platform with Real-Time AI Q&A

VisionCortex is a browser-based platform, which enables users to register faces, recognize them in real-time using a webcam, and query face registration data through a chat interface powered by a Retrieval-Augmented Generation (RAG) pipeline. The platform combines full-stack development (React, Node.js) with AI-driven face recognition and RAG-based query processing (Python, LangChain, FAISS, LLM).

## Features

### Registration Tab
- Captures face images via webcam using `face_recognition`.
- Stores name, face encoding, and timestamp in an SQLite database.
- Supports multiple unique face registrations.
  
  ![image](https://github.com/user-attachments/assets/61a75cff-1626-4069-8c0e-9fd466e12df0)


### Live Recognition Tab
- Streams webcam feed and detects known faces in real-time.
- Overlays bounding boxes and names for recognized faces.
- Handles multiple faces in a single frame.

  ![image](https://github.com/user-attachments/assets/88c72022-55e1-4284-9f9b-dc357df85052)

  

### Chat-Based Query Interface
- Embedded chat widget in the React frontend.
- Uses WebSockets for communication: React ↔ Node.js ↔ Python RAG engine.
- Answers queries like "How many people are registered?" or "When was John registered?" using a RAG pipeline (LangChain, FAISS, LLM).

  ![image](https://github.com/user-attachments/assets/c4c212ff-5e19-4a19-a832-a17cfc4a9056)


## Tech Stack

| Module            | Technology                          |
|-------------------|-------------------------------------|
| Frontend          | React.js                           |
| Backend           | Node.js (Express, WebSocket)       |
| Face Recognition  | Python (`face_recognition`, OpenCV)|
| RAG Pipeline      | Python (LangChain, FAISS, LLM)|
| Database          | SQLite (`faces.db`)                |
| LLM               | GroqCloud: llama-3.3-70b-versatile |

## Architecture

The system is modular, with distinct components for face registration, recognition, and query processing, all centered around a shared SQLite database (`faces.db`). Below is a high-level overview:

- **Frontend (React)**: `App.js` manages tabs (`RegisterTab`, `RecognitionTab`, `ChatTab`). Uses Axios for HTTP requests to Node.js and WebSocket (ws://5001) for chat queries.
- **Backend (Node.js)**: `server.js` handles HTTP APIs (`/api/register`, `/api/recognize`) by spawning Python scripts and forwards chat queries to `rag_engine.py` via WebSocket (ws://8765).
- **Face Registration (`register.py`)**: Captures webcam input, generates face encodings, and stores data in `faces.db`.
- **Face Recognition (`recognize.py`)**: Streams webcam feed, matches faces against stored encodings, and displays names.
- **RAG Pipeline (`rag_engine.py`)**: Fetches data from `faces.db`, builds a FAISS vector store with text embeddings, and uses Grok LLM to answer queries.
- **Database (`faces.db`)**: Stores `id`, `name`, `encoding`, and `timestamp` for each registered face.

![image](https://github.com/user-attachments/assets/790ef7a1-e0e9-41b3-8674-6eec690be626)

![image](https://github.com/user-attachments/assets/dccde284-81b2-4002-bfcf-c98000dbd6ce)


## Prerequisites

- **Python 3.8+**: For `register.py`, `recognize.py`, and `rag_engine.py`.
- **Node.js 16+**: For `server.js` and React frontend.
- **API Keys**:
  - Groq API key for the LLM (set in `.env`).
  - HuggingFace API token for embeddings (set in `.env`).

## Setup Instructions

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/your-username/visioncortex.git
    cd visioncortex
    ```

2. **Set Up Python Environment**:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r backend/requirements.txt
    ```
Install required libraries:

 - face_recognition, opencv-python, numpy (for face recognition).
 - langchain, faiss-cpu, langchain-huggingface, langchain-groq (for RAG).

**Note**: On macOS/Linux, install cmake and libopenblas for face_recognition:

    ```bash
    # macOS
    brew install cmake libopenblas
    # Ubuntu
    sudo apt-get install cmake libopenblas-dev
    ```


3.**Set Up Node.js Environment**:

  ```bash
  cd frontend
  npm install
  cd ../backend
  npm install
  ```
4.**Configure Environment Variables**:
 - Create a `.env` file in the backend/ directory:

  ```plaintext
  GROQ_API_KEY=your_groq_api_key
  HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
  ```
 - Obtain keys from Groq and HuggingFace.

5.**Run the Application**:

 - Start the Node.js backend:
    ```bash
    cd backend
    node server.js
    ```
    Runs on `http://localhost:5001`.
 - Start the React frontend:
    ```bash
    cd frontend
    npm start
    ```
    Runs on `http://localhost:3000`.
 - Start the RAG WebSocket server:
    ```bash
    cd backend
    python3 rag_engine.py --websocket
    ```
    Runs on `ws://localhost:8765`.
   
6.**Access the Platform**:

 - Open `http://localhost:3000` in a browser.
 - Use the "Register" tab to add faces.
 - Use the "Recognition" tab to start live recognition.
 - Use the "Chat" tab to query face data (e.g., "How many people are registered?").

## Usage
 - Register a Face:
   - Enter a name in the "Register" tab and click "Register".
   - A webcam window opens. Press `s` to save the face or `q` to quit.
 - Recognize Faces:
   - Click "Start Recognition" in the "Recognition" tab.
   - The webcam shows live feed with names overlaid on recognized faces.
   - Press `q` to quit
 - Query Data:
   - Type queries in the "Chat" tab (e.g., "Who was the last person registered?").
   - Responses appear in the chat box.

## Logging
 - **Face Recognition Logs** : Stored in backend/logs/face_recognition.log (e.g., registration and recognition events).
 - **RAG Pipeline Logs** : Stored in backend/logs/rag_engine.log (e.g., query processing, retrieval details).
 - Logs include timestamps, levels (INFO, ERROR), and detailed messages for event tracking.
## Assumptions
 - LLM Choice: Used Groqcloud (llama-3.3-70b-versatile) instead of OpenAI's ChatGPT due to availability and performance. The RAG pipeline remains compatible with any LLM via LangChain.
 - Database: Chose SQLite for simplicity and lightweight storage, suitable for a hackathon prototype.
 - WebSocket Ports: Node.js WebSocket runs on ws://5001, RAG WebSocket on ws://8765.

## Repository Structure
  ![image](https://github.com/user-attachments/assets/d00845bd-d004-45b1-8618-2154ef3936b2)

## Demo Video
 - A walkthrough of the platform, demonstrating registration, recognition, and chat queries, is available at:

## Acknowledgments
This project is a part of a hackathon run by https://katomaran.com.

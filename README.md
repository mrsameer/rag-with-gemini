# RAG with Gemini Vertex AI

This project demonstrates a Retrieval-Augmented Generation (RAG) application using Google's Gemini 2.5 Flash model and Vertex AI RAG Engine.

## Features

- **Document Management**: Upload and delete documents to/from Vertex AI RAG Corpus.
- **Chat Interface**: Chat with your documents using Gemini 2.5 Flash.
- **RAG Integration**: Uses Vertex AI RAG Engine for retrieval.

## Prerequisites

- Python 3.8+
- Node.js 18+
- Google Cloud Project with Vertex AI API enabled.
- Service Account Key (`gemini-api-key.json`) with necessary permissions.

## Setup

1.  **Clone the repository** (if applicable).
2.  **Place your credentials**: Ensure `gemini-api-key.json` is in the project root.

### Backend

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the server:
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

### Frontend

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```

## Usage

1.  Open your browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
2.  Go to the **Documents** tab to upload text files.
3.  Switch to the **Chat** tab to ask questions based on the uploaded documents.

## Notes

- The application uses `asia-south1` region for Vertex AI resources.
- Google Search integration is currently disabled due to SDK compatibility issues.

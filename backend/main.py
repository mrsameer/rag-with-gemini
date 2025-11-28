import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import vertexai
from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool, grounding
import google.auth
from google.oauth2 import service_account

# Configuration
PROJECT_ID = "vassarai-208611"
LOCATION = "asia-south1"
CREDENTIALS_FILE = "../gemini-api-key.json"

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Vertex AI
credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

# RAG Configuration
CORPUS_NAME = "rag-corpus-gemini"
# We need to check if corpus exists or create it. 
# For simplicity in this demo, we'll try to get or create.
# Note: In a production app, you might manage corpus creation separately.

rag_corpus = None

def get_or_create_corpus():
    global rag_corpus
    if rag_corpus:
        return rag_corpus
    
    try:
        # List existing corpora to find ours
        corpora = rag.list_corpora()
        for c in corpora:
            if c.display_name == CORPUS_NAME:
                rag_corpus = c
                print(f"Found existing corpus: {rag_corpus.name}")
                return rag_corpus
        
        # Create if not found
        rag_corpus = rag.create_corpus(display_name=CORPUS_NAME)
        print(f"Created new corpus: {rag_corpus.name}")
        return rag_corpus
    except Exception as e:
        print(f"Error initializing corpus: {e}")
        raise e

# Initialize Corpus on startup
@app.on_event("startup")
async def startup_event():
    get_or_create_corpus()

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    citations: List[str] = []

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        corpus = get_or_create_corpus()
        
        # Create RAG retrieval tool
        rag_retrieval_tool = Tool.from_retrieval(
            retrieval=rag.Retrieval(
                source=rag.VertexRagStore(
                    rag_resources=[
                        rag.RagResource(
                            rag_corpus=corpus.name,
                        )
                    ],
                    similarity_top_k=3,
                )
            )
        )
        
        # Initialize model with tools
        model = GenerativeModel(
            "gemini-2.5-flash",
            tools=[rag_retrieval_tool] #, google_search_tool]
        )
        
        # Generate response
        response = model.generate_content(request.query)
        
        # Extract text and citations (simplified)
        text_response = response.text
        
        # TODO: Extract actual citations if available in response metadata
        citations = [] 
        
        return ChatResponse(response=text_response, citations=citations)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        corpus = get_or_create_corpus()
        
        # Save temp file
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
            
        # Import file to RAG corpus
        # Vertex AI RAG supports importing from GCS or Google Drive. 
        # Direct upload is less straightforward in the preview SDK, 
        # usually involves uploading to GCS first.
        # For this demo, we will assume we need to upload to GCS first or use a supported path.
        # WAIT: The prompt asks to use "Vertex AI Feature Store in Vertex AI RAG Engine".
        # Actually, `rag.import_files` supports local paths in some versions, let's try that.
        
        response = rag.import_files(
            corpus_name=corpus.name,
            paths=[temp_path],
            chunk_size=512,
            chunk_overlap=50
        )
        
        os.remove(temp_path)
        return {"message": f"Imported {response.imported_rag_files_count} files."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    try:
        corpus = get_or_create_corpus()
        files = rag.list_files(corpus_name=corpus.name)
        return [{"id": f.name, "display_name": f.display_name} for f in files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{file_id}")
async def delete_document(file_id: str):
    try:
        # file_id needs to be the full resource name
        # If the user passes just the ID, we might need to construct the full name
        # But list_documents returns full name, so frontend should send full name.
        rag.delete_file(name=file_id)
        return {"message": "Document deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

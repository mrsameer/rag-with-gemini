# RAG with Gemini - Complete File Inventory Management

A comprehensive RAG (Retrieval-Augmented Generation) application with complete file inventory management using Google Gemini File Search API and Streamlit.

## Features

### 📚 Complete File Inventory Management
- **View all documents** with full metadata (name, status, size, type, timestamps)
- **Track document status** in real-time (Active, Pending, Failed)
- **Custom metadata** support with key-value pairs
- **Advanced filtering** by status and search terms
- **Flexible sorting** by upload time, name, or size
- **Detailed document viewer** with JSON export

### 📊 Store Analytics Dashboard
- **Real-time metrics** showing total, active, pending, and failed documents
- **Storage usage tracking** with warnings when approaching limits
- **Store management** - create, switch between, and monitor multiple stores
- **Document lifecycle tracking** from upload to deletion

### 📤 Advanced Upload Options
- **Custom display names** for better organization
- **Custom metadata** (up to 20 key-value pairs per document)
- **Configurable chunking** - adjust chunk size (100-2000 tokens) and overlap
- **Progress tracking** with real-time operation monitoring
- **Multiple file type support** (PDF, DOC, DOCX, TXT, CSV, XLSX, PPTX, MD, HTML, code files)

### 💬 Smart Chat Interface
- **Chat with your documents** using Gemini 2.5 Flash
- **View citations** and sources for AI responses
- **Optional Google Search** mode for current events
- **Chat history** management
- **Grounding metadata** extraction

## Quick Start

### 1. Get Your Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create an API key
3. Copy it for the next step

### 2. Setup

```bash
# Clone or navigate to the project directory
cd rag-with-gemini

# Create .env file with your API key
cp .env.example .env
# Then edit .env and add your GEMINI_API_KEY

# Install dependencies (using uv - recommended)
uv add streamlit google-genai python-dotenv

# OR using pip
pip install -r requirements.txt
```

### 3. Run

```bash
# Easy way - using the run script
./run.sh

# OR using uv directly
uv run streamlit run app.py

# OR using python directly
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

## Usage Guide

### Store Management

1. **Select Store** - Choose from existing stores in the sidebar dropdown
2. **Create New Store** - Click "Create New Store" and enter a display name
3. **Switch Stores** - Use the dropdown to switch between different document collections

### Document Upload

1. **Choose File** - Click "Choose a file" and select a document
2. **Configure Upload** (optional) - Expand "Advanced Options" to:
   - Set a custom display name
   - Add custom metadata (e.g., author, year, category)
   - Adjust chunk size (default: 400 tokens)
   - Set chunk overlap (default: 40 tokens)
3. **Upload** - Click "Upload" and wait for processing to complete

### Document Inventory

1. **View Documents** - Go to the "Inventory" tab
2. **Filter** - Select status filter (All, Active, Pending, Failed)
3. **Search** - Use the search box to find documents by name
4. **Sort** - Choose sorting method (upload time, name, size)
5. **Expand Document** - Click on any document to view details
6. **Actions** - Use the Delete or Details buttons for each document

### Analytics

1. **Go to Analytics Tab** - View comprehensive store statistics
2. **Monitor Metrics** - Check total documents, active, pending, and failed counts
3. **Track Storage** - View storage usage and get warnings when approaching limits
4. **Store Info** - See when the store was created

### Chatting

1. **Select Mode** - Choose between File Search (your documents) or Google Search
2. **Ask Questions** - Type your question in the chat input
3. **View Response** - AI responds with citations from your documents
4. **Expand Citations** - Click to see which documents were used
5. **Clear History** - Use "Clear Chat" button to start fresh

## Configuration

Edit [.env](.env) to customize:

```bash
# Required: Your Google Gemini API Key
GEMINI_API_KEY=your_api_key_here

# Optional: Reuse an existing File Search store
# FILE_SEARCH_STORE_NAME=fileSearchStores/abc123

# Optional: Custom display name for new stores
FILE_SEARCH_DISPLAY_NAME=rag-streamlit-store
```

## File Lifecycle

The application manages the complete lifecycle of documents:

1. **Upload** - Document is uploaded to the File Search store
2. **Processing** - Document is chunked and embedded (`STATE_PENDING`)
3. **Active** - Document is fully processed and searchable (`STATE_ACTIVE`)
4. **Query** - Document chunks are searched during chat operations
5. **Manage** - View metadata, status, and document details
6. **Delete** - Remove documents and free up storage space

## Supported File Types

### Documents
- PDF (`.pdf`)
- Microsoft Word (`.doc`, `.docx`)
- Text files (`.txt`, `.md`)
- HTML (`.html`, `.htm`)

### Spreadsheets & Presentations
- CSV (`.csv`)
- Microsoft Excel (`.xlsx`, `.xls`)
- Microsoft PowerPoint (`.pptx`)

### Code Files
Python, JavaScript, TypeScript, Java, C++, Go, Rust, and many more

## API Limits & Quotas

| Resource | Limit |
|----------|-------|
| Maximum file size | 100 MB |
| Maximum stores per project | 10 |
| Recommended store size | < 20 GB |
| Maximum metadata entries | 20 per document |
| Maximum chunk size | 2043 tokens |
| Documents per page | 20 |

## Architecture

This is a **single-file Streamlit application** that:
- Uses **Google Gemini 2.5 Flash** for chat generation
- Uses **Gemini File Search API** for document retrieval and RAG
- Implements **complete file inventory management**
- Provides **store analytics and monitoring**
- Manages **document lifecycle** from upload to deletion
- Supports **custom metadata and chunking configurations**

No separate frontend/backend - everything runs in one Python file!

## Advanced Features

### Custom Metadata
Add key-value metadata to documents for better organization:
```
author: John Doe
year: 2024
category: research
department: engineering
```

### Chunking Configuration
Optimize chunking for your documents:
- **Chunk Size**: Controls how much text per chunk (100-2000 tokens)
- **Chunk Overlap**: Creates overlap between chunks for better context (0-200 tokens)

### Store Management
- Create multiple stores for different document collections
- Switch between stores seamlessly
- Monitor storage usage and document counts
- Track document processing status

### Document Filtering & Sorting
- Filter by status (Active, Pending, Failed)
- Search by document name
- Sort by upload time, name, or size
- View detailed metadata for each document

## Troubleshooting

**"GEMINI_API_KEY not found"**
- Make sure you created [.env](.env) file with your API key
- Check that the key is valid and not expired

**Upload fails or times out**
- Check your internet connection
- Verify file size is under 100 MB
- Ensure file type is supported
- Try reducing chunk size if processing times out

**Document stuck in PENDING state**
- Large documents may take several minutes to process
- Check the Analytics tab for failed document count
- Try re-uploading with smaller chunk size

**No response from chat**
- Ensure you have at least one document in ACTIVE state
- Check that the correct store is selected
- Try rephrasing your question
- Verify "Use Google Search" is toggled correctly

**Storage warning**
- Review and delete unused documents in the Inventory tab
- Consider creating a new store for new documents
- The recommended limit is 20 GB per store

## API Documentation

For complete API documentation, visit:
- [File Search Guide](https://ai.google.dev/gemini-api/docs/file-search)
- [File Search Stores API](https://ai.google.dev/api/file-search/file-search-stores)
- [Documents API](https://ai.google.dev/api/file-search/documents)
- [Google GenAI Python SDK](https://googleapis.github.io/python-genai/)

## Requirements

- Python 3.8 or higher
- Google Gemini API key
- Internet connection
- 3 Python packages (see [requirements.txt](requirements.txt))

## Notes

- Documents are stored indefinitely in Google's File Search service (unlike Files API which deletes after 48 hours)
- Your API key is used for all operations
- Chat history is stored locally in your browser session
- Document metadata and status are tracked in real-time
- Storage is free, but indexing costs $0.15 per 1M tokens
- Retrieved context is charged as input tokens to the model

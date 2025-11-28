#!/bin/bash

# Simple script to run the Streamlit RAG application

set -e

echo "🤖 Starting RAG with Gemini..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and add your GEMINI_API_KEY"
    echo "   Get your API key from: https://aistudio.google.com/app/apikey"
    exit 1
fi

# Check if GEMINI_API_KEY is set
if ! grep -q "GEMINI_API_KEY=your_api_key_here" .env; then
    echo "✅ API key configured"
else
    echo "❌ Error: Please edit .env and add your GEMINI_API_KEY"
    echo "   Get your API key from: https://aistudio.google.com/app/apikey"
    exit 1
fi

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "📦 Using uv to run Streamlit..."
    uv run streamlit run app.py
else
    echo "📦 Using python to run Streamlit..."
    streamlit run app.py
fi

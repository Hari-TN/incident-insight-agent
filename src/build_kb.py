"""
Build the vector knowledge base.

This script:
1. Loads the fake incidents from incidents.py
2. Converts each incident into a vector using Gemini's embedding model
3. Stores the vectors in a local ChromaDB instance
4. Persists the database to disk so we don't have to rebuild it every time

Run this ONCE to seed the knowledge base.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from incidents import INCIDENTS

# Load API key
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY not found. Did you create .env?")

# Where ChromaDB will save its files. Local directory, gets git-ignored.
PERSIST_DIR = "./chroma_db"

print("Loading embedding model (Gemini)...")
# This is the model that converts text -> vector
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL,
)

# Convert each incident into a LangChain Document.
# We embed only description + resolution (the searchable parts) and put
# title + id in metadata for retrieval.
print(f"Preparing {len(INCIDENTS)} incidents for embedding...")
documents = []
for inc in INCIDENTS:
    text_to_embed = (
        f"Problem: {inc['description']}\n"
        f"Resolution: {inc['resolution']}"
    )
    documents.append(
        Document(
            page_content=text_to_embed,
            metadata={
                "id": inc["id"],
                "title": inc["title"],
            },
        )
    )

# Build the ChromaDB collection. This call will:
# - call the Gemini embedding API for each document
# - store the resulting vectors locally
print("Generating embeddings and storing in ChromaDB...")
vector_store = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory=PERSIST_DIR,
    collection_name="incidents",
)

print(f"\n[OK] Knowledge base built: {len(documents)} incidents stored in {PERSIST_DIR}")
print("Ready to query. Next: run search_kb.py to find similar incidents.")
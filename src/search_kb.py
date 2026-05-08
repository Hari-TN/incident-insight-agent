"""
Search the vector knowledge base for incidents similar to a query.

This script:
1. Loads the existing ChromaDB knowledge base from disk
2. Takes a query (a new incident description)
3. Returns the top 3 most semantically similar past incidents

Run AFTER build_kb.py has been executed at least once.
"""

import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY not found. Did you create .env?")

PERSIST_DIR = "./chroma_db"

# Use the SAME embedding model that built the KB.
# Mismatching embedding models would give meaningless results because
# vectors from different models live in different "meaning spaces."
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
)

# Load the existing knowledge base from disk (does NOT re-embed everything)
vector_store = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=embeddings,
    collection_name="incidents",
)

def search(query: str, k: int = 3):
    """Return top-k incidents most similar to the query."""
    # similarity_search_with_score returns (Document, distance) tuples.
    # Lower distance = more similar (it's a cosine distance under the hood).
    results = vector_store.similarity_search_with_score(query, k=k)
    return results

# Allow running with a query from command-line, otherwise use a default
if len(sys.argv) > 1:
    query = " ".join(sys.argv[1:])
else:
    query = "Service is throwing 500 errors and customers can't checkout"

print("=" * 70)
print(f"QUERY: {query}")
print("=" * 70)

results = search(query, k=3)

for i, (doc, distance) in enumerate(results, start=1):
    print(f"\n[#{i}] {doc.metadata['id']} — {doc.metadata['title']}")
    print(f"     Distance: {distance:.4f}  (lower = more similar)")
    print(f"     Content snippet: {doc.page_content[:200]}...")

print("\n" + "=" * 70)
"""
Full RAG pipeline: Retrieval-Augmented Generation for incident resolution.

This module exposes:
  - get_rag_chain()      : returns the composed LangChain pipeline
  - get_retriever()      : returns the retriever for inspection
  - resolve_incident()   : convenience function used by the API and CLI

Run AFTER build_kb.py has seeded the knowledge base.
"""

import os
import sys
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY not found. Did you create .env?")

# Resolve the chroma_db path absolutely, relative to this file's location.
# This way the retriever works whether you run from project root,
# from inside src/, or as an imported module from a web server.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
# --- Configuration ---
# Model names live in environment variables so a deprecation is a one-line
# config change, not a code change. Defaults match what was tested.

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
PERSIST_DIR = os.path.join(_PROJECT_ROOT, "chroma_db")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash-lite")
TOP_K = int(os.getenv("TOP_K", "3"))


# --- Singletons (lazy-built once, reused by every call) ---

_embeddings = None
_vector_store = None
_retriever = None
_llm = None
_chain = None


def _format_docs(docs):
    """Turn a list of LangChain Documents into a string for the prompt."""
    formatted = []
    for i, doc in enumerate(docs, start=1):
        formatted.append(
            f"[{i}] {doc.metadata.get('id')} — {doc.metadata.get('title')}\n"
            f"    {doc.page_content}"
        )
    return "\n\n".join(formatted)


def get_retriever():
    """Return a LangChain retriever backed by the persisted ChromaDB store."""
    global _embeddings, _vector_store, _retriever
    if _retriever is None:
        _embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
        _vector_store = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=_embeddings,
            collection_name="incidents",
        )
        _retriever = _vector_store.as_retriever(search_kwargs={"k": TOP_K})
    return _retriever


def get_rag_chain():
    """Return the composed RAG chain (retriever | prompt | LLM | parser)."""
    global _llm, _chain
    if _chain is None:
        retriever = get_retriever()
        _llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0)

        prompt = ChatPromptTemplate.from_template(
            """You are a senior site reliability engineer helping a team
resolve a production incident. You have access to a small library of past
incidents that were resolved by your team.

Use the past incidents below to suggest a concrete, actionable first response.
If the past incidents don't seem relevant, say so honestly rather than inventing.

PAST INCIDENTS (most similar first):
---------------------------------
{context}
---------------------------------

NEW INCIDENT:
{question}

YOUR RESPONSE (be concise and technical, 3-5 sentences max):"""
        )

        _chain = (
            {"context": retriever | _format_docs, "question": RunnablePassthrough()}
            | prompt
            | _llm
            | StrOutputParser()
        )
    return _chain


def resolve_incident(query: str) -> dict:
    """
    Run the full RAG pipeline for a single query.
    Returns both the LLM resolution and the retrieved context (for transparency).
    """
    retriever = get_retriever()
    chain = get_rag_chain()

    retrieved_docs = retriever.invoke(query)
    resolution = chain.invoke(query)

    return {
        "query": query,
        "resolution": resolution,
        "retrieved_incidents": [
            {
                "id": doc.metadata.get("id"),
                "title": doc.metadata.get("title"),
            }
            for doc in retrieved_docs
        ],
    }


# --- CLI entry point (so the script still works standalone) ---

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Payment gateway is throwing 500s and customers can't check out"

    result = resolve_incident(query)

    print("=" * 70)
    print(f"NEW INCIDENT: {result['query']}")
    print("=" * 70)
    print("\nRETRIEVED CONTEXT:")
    for i, inc in enumerate(result["retrieved_incidents"], start=1):
        print(f"  [{i}] {inc['id']} — {inc['title']}")
    print("\nGENERATING RESOLUTION SUGGESTION...\n")
    print("-" * 70)
    print(result["resolution"])
    print("-" * 70)
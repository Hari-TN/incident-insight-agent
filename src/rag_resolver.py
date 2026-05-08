"""
Full RAG pipeline: Retrieval-Augmented Generation for incident resolution.

Flow:
1. User submits a new incident description (the QUERY)
2. RETRIEVAL: Find the top-K similar past incidents from ChromaDB
3. AUGMENTATION: Inject those incidents as context into the LLM prompt
4. GENERATION: Gemini drafts a resolution grounded in the retrieved history

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

PERSIST_DIR = "./chroma_db"

# --- 1. Set up the retriever (uses Phase 2's vector store) ---

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

vector_store = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=embeddings,
    collection_name="incidents",
)

# .as_retriever() converts the vector store into a LangChain Retriever object
# that accepts a query string and returns Documents. k=3 means "return top 3."
retriever = vector_store.as_retriever(search_kwargs={"k": 3})


# --- 2. Set up the LLM ---

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0,
)


# --- 3. Build the augmented prompt ---

# This prompt template has TWO variables:
#   {context}  — the retrieved past incidents (filled in by the retriever)
#   {question} — the new incident the user is asking about
#
# Notice how the prompt instructs the LLM to USE the past incidents.
# That's the whole "augmentation" idea: ground the model in your data,
# not its general training knowledge.
RAG_PROMPT_TEMPLATE = """You are a senior site reliability engineer helping a team
resolve a production incident. You have access to a small library of past incidents
that were resolved by your team.

Use the past incidents below to suggest a concrete, actionable first response.
If the past incidents don't seem relevant, say so honestly rather than inventing.

PAST INCIDENTS (most similar first):
---------------------------------
{context}
---------------------------------

NEW INCIDENT:
{question}

YOUR RESPONSE (be concise and technical, 3-5 sentences max):"""

prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)


# --- 4. Helper: format retrieved docs into a single string ---

def format_docs(docs):
    """Turn a list of LangChain Documents into a string for the prompt."""
    formatted = []
    for i, doc in enumerate(docs, start=1):
        formatted.append(
            f"[{i}] {doc.metadata.get('id')} — {doc.metadata.get('title')}\n"
            f"    {doc.page_content}"
        )
    return "\n\n".join(formatted)


# --- 5. The RAG chain itself ---
#
# This is LangChain Expression Language (LCEL). Read it like a pipeline:
#
#   {"context": retriever | format_docs, "question": RunnablePassthrough()}
#       |  prompt
#       |  llm
#       |  StrOutputParser()
#
# Step by step, when you invoke this chain with a question string:
#   - "context" key: the question goes to the retriever, which returns docs,
#     which then go to format_docs() to become a single string.
#   - "question" key: the question is passed through unchanged.
#   - The dict (context + question) feeds into the prompt template.
#   - The filled prompt feeds into the LLM.
#   - The LLM's response goes through StrOutputParser to extract plain text.
#
# This `|` chaining is one of the most-asked-about features in interviews.
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)


# --- 6. Run it ---

if len(sys.argv) > 1:
    query = " ".join(sys.argv[1:])
else:
    query = "Payment gateway is throwing 500s and customers can't check out"

print("=" * 70)
print(f"NEW INCIDENT: {query}")
print("=" * 70)

# First, show what got retrieved (so the RAG is transparent, not magic)
retrieved_docs = retriever.invoke(query)
print("\nRETRIEVED CONTEXT:")
for i, doc in enumerate(retrieved_docs, start=1):
    print(f"  [{i}] {doc.metadata.get('id')} — {doc.metadata.get('title')}")

print("\nGENERATING RESOLUTION SUGGESTION...\n")
print("-" * 70)
response = rag_chain.invoke(query)
print(response)
print("-" * 70)
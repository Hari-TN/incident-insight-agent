"""
Hello LangChain — first contact with the LangChain framework.

This script:
1. Loads the Gemini API key from .env
2. Wraps the Gemini model with LangChain's ChatGoogleGenerativeAI
3. Sends a single prompt and prints the response
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# Load the .env file so os.environ can see GOOGLE_API_KEY
load_dotenv()

# Sanity check — fail fast if the key isn't loaded
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY not found. Did you create .env?")

# Initialize the model. 'temperature=0' means deterministic output (good for testing).
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0,
)

# A PromptTemplate lets us parameterize prompts cleanly.
# This is the LangChain pattern: define the prompt once, fill it in per call.
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a senior site reliability engineer. Be concise and technical."),
    ("human", "Suggest one quick action for this incident: {incident}"),
])

# Build a chain: prompt -> llm. The | operator is LangChain's pipe pattern.
chain = prompt | llm

# Invoke the chain with our variable
response = chain.invoke({
    "incident": "API returning HTTP 500 errors at 30% rate, started 5 minutes ago"
})

# The response is a message object; .content gives us the text
print("=" * 60)
print("LANGCHAIN RESPONSE:")
print("=" * 60)
print(response.content)
print("=" * 60)
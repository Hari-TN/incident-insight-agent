"""
FastAPI service exposing the RAG-based incident resolver as a REST API.

Endpoints:
  GET  /              -> service info
  GET  /health        -> health check (for load balancers / monitoring)
  POST /resolve       -> run the RAG pipeline on an incident description
  GET  /docs          -> auto-generated OpenAPI docs (FastAPI built-in)

Run locally with:
  uvicorn src.api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .rag_resolver import resolve_incident


# --- Pydantic models for request/response validation ---

class IncidentRequest(BaseModel):
    """Request body for POST /resolve."""
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Free-text description of the production incident",
        examples=["Payment API is returning HTTP 500 errors at ~30% rate"],
    )


class RetrievedIncident(BaseModel):
    """One past incident returned alongside the LLM resolution."""
    id: str
    title: str


class IncidentResponse(BaseModel):
    """Response body for POST /resolve."""
    query: str
    resolution: str
    retrieved_incidents: list[RetrievedIncident]


class HealthResponse(BaseModel):
    status: str
    service: str


# --- FastAPI app ---

app = FastAPI(
    title="Incident Insight Agent",
    description=(
        "A RAG-based assistant that suggests resolutions for production "
        "incidents by retrieving similar past incidents from a vector "
        "store and grounding LLM output in that context."
    ),
    version="0.1.0",
)


@app.get("/", tags=["meta"])
def root():
    """Service landing endpoint."""
    return {
        "service": "Incident Insight Agent",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": ["/health", "/resolve"],
    }


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health():
    """Liveness/health probe for load balancers and monitoring."""
    return HealthResponse(status="ok", service="incident-insight-agent")


@app.post("/resolve", response_model=IncidentResponse, tags=["rag"])
def resolve(request: IncidentRequest):
    """
    Take a new incident description, retrieve similar past incidents from
    the vector store, and return an LLM-generated resolution suggestion
    grounded in that retrieved context.
    """
    try:
        result = resolve_incident(request.description)
        return IncidentResponse(
            query=result["query"],
            resolution=result["resolution"],
            retrieved_incidents=[
                RetrievedIncident(id=inc["id"], title=inc["title"])
                for inc in result["retrieved_incidents"]
            ],
        )
    except Exception as e:
        # Don't leak internal errors to the client; log them and return 500
        # In production this would go through a structured logger.
        print(f"[ERROR] /resolve failed: {e!r}")
        raise HTTPException(status_code=500, detail="Resolution failed")
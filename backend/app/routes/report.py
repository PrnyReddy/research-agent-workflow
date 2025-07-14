from fastapi import APIRouter, UploadFile, File, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Any, Dict, Union
import asyncio
import json
import docx
from PyPDF2 import PdfReader
import io
import logging
from app.agents.graph import graph
from app.utils.vector_store import VectorStore

logger = logging.getLogger("multiagent")

router = APIRouter()

# --- Request and Response Models ---

class AddDocumentsRequest(BaseModel):
    """Request model for adding documents to the vector store."""
    documents: List[str] = Field(..., description="List of document texts to add.")
    index_name: str = Field("research_docs", description="Name of the Elasticsearch index.")

class AddDocumentsResponse(BaseModel):
    """Response model for add-documents endpoint."""
    success: bool = Field(..., description="Whether the operation was successful.")
    message: str = Field(..., description="Status message.")
    error: Optional[str] = Field(None, description="Error message if any.")

class UploadFilesResponse(BaseModel):
    """Response model for upload-files endpoint."""
    success: bool = Field(..., description="Whether the operation was successful.")
    message: str = Field(..., description="Status message.")
    error: Optional[str] = Field(None, description="Error message if any.")

class GenerateReportRequest(BaseModel):
    """Request model for generating a research report."""
    task_description: str = Field(..., min_length=10, description="Detailed research task prompt.")

class GenerateReportEvent(BaseModel):
    """Event model for streaming report generation updates."""
    event: str = Field(..., description="Type of event: update, end, or error.")
    data: Dict[str, Any] = Field(..., description="Event data payload.")

class AddLinkRequest(BaseModel):
    url: HttpUrl
    index_name: str = Field("research_docs", description="Name of the Elasticsearch index.")

class AddLinkResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None

# --- Endpoints ---

@router.post("/add-documents", response_model=AddDocumentsResponse)
async def add_documents(request: AddDocumentsRequest):
    """Add a list of documents to the vector store."""
    vector_store = VectorStore()
    try:
        vector_store.add_documents(index_name=request.index_name, documents=request.documents)
        return AddDocumentsResponse(success=True, message=f"Successfully added {len(request.documents)} documents to index '{request.index_name}'.", error=None)
    except Exception as e:
        logger.error(f"Failed to add documents: {str(e)}")
        return AddDocumentsResponse(success=False, message="Failed to add documents.", error=str(e))

@router.post("/upload-files", response_model=UploadFilesResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload and process files (PDF, DOCX, TXT) and add their content to the vector store."""
    documents = []
    try:
        for file in files:
            content = await file.read()
            if file.filename.endswith(".pdf"):
                reader = PdfReader(io.BytesIO(content))
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                documents.append(text)
            elif file.filename.endswith(".docx"):
                doc = docx.Document(io.BytesIO(content))
                text = "\n".join([para.text for para in doc.paragraphs])
                documents.append(text)
            elif file.filename.endswith(".txt"):
                documents.append(content.decode("utf-8"))

        if documents:
            vector_store = VectorStore()
            vector_store.add_documents(index_name="research_docs", documents=documents)
            return UploadFilesResponse(success=True, message=f"Successfully processed and added {len(documents)} files.", error=None)
        else:
            return UploadFilesResponse(success=False, message="No supported files were processed.", error="No supported files.")
    except Exception as e:
        logger.error(f"Failed to process files: {str(e)}")
        return UploadFilesResponse(success=False, message="Failed to process files.", error=str(e))

# Utility for serializing agent output
def serialize_for_json(obj):
    if hasattr(obj, "content"):
        return obj.content
    if hasattr(obj, "type") and hasattr(obj, "content"):
        return {"type": getattr(obj, "type", None), "content": obj.content}
    if isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    return obj

async def run_graph_in_background(task_description: str, queue: asyncio.Queue):
    try:
        async for event in graph.astream({"task": task_description}):
            logger.info(f"GRAPH EVENT: {event}")
            for key, value in event.items():
                if key == '__end__':
                    final_report = value.get('report', 'No report generated.')
                    msg = f"event: end\ndata: {json.dumps(serialize_for_json({'report': final_report}))}\n\n"
                    logger.info(f"SENDING TO QUEUE: {msg}")
                    await queue.put(msg)
                else:
                    safe_value = serialize_for_json(value if value is not None else {})
                    msg = f"event: update\ndata: {json.dumps({key: safe_value})}\n\n"
                    logger.info(f"SENDING TO QUEUE: {msg}")
                    await queue.put(msg)
        await queue.put(None)
    except Exception as e:
        err_msg = f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        logger.error(f"SENDING TO QUEUE (ERROR): {err_msg}")
        await queue.put(err_msg)
        await queue.put(None)

@router.post("/generate-report", response_model=None)
async def generate_report(request: GenerateReportRequest):
    """Generate a research report for a given task. Streams events as Server-Sent Events (SSE)."""
    queue = asyncio.Queue()
    asyncio.create_task(run_graph_in_background(request.task_description, queue))

    async def stream_events():
        while True:
            item = await queue.get()
            if item is None:
                break
            if item.endswith("\n\n"):
                yield item
            queue.task_done()

    return StreamingResponse(stream_events(), media_type="text/event-stream")

@router.post("/add-link", response_model=AddLinkResponse)
async def add_link(request: AddLinkRequest):
    """Scrape a URL and add its content to the vector store."""
    from app.tools.web_scraper import scrape_website
    vector_store = VectorStore()
    try:
        result = scrape_website(str(request.url))
        if "error" in result:
            return AddLinkResponse(success=False, message="Failed to scrape link.", error=result["error"])
        content = result["content"]
        vector_store.add_documents(index_name=request.index_name, documents=[content])
        return AddLinkResponse(success=True, message="Link content added to knowledge base.")
    except Exception as e:
        logger.error(f"Failed to add link: {str(e)}")
        return AddLinkResponse(success=False, message="Failed to add link.", error=str(e)) 
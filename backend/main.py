from fastapi import FastAPI, File, UploadFile, HTTPException, Request, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import asyncio
import json
import docx
from PyPDF2 import PdfReader
import io
from app.agents import graph

# Universal serialization utility for custom objects (e.g., AIMessage)
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

app = FastAPI(
    title="Multi-Agent AI Platform",
    description="An AI platform for complex goal-oriented tasks using a multi-agent system.",
    version="0.1.0",
)

origins = [
    "http://localhost:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    task: str

class AddDocsRequest(BaseModel):
    documents: list[str]
    index_name: str = "research_docs"

@app.get("/")
async def root():
    return {"message": "Welcome to the Multi-Agent AI Platform! Use the /generate-report endpoint to start a task."}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/add-documents")
async def add_documents(request: AddDocsRequest):
    from app.vector_store import VectorStore
    vector_store = VectorStore()
    try:
        vector_store.add_documents(index_name=request.index_name, documents=request.documents)
        return {"message": f"Successfully added {len(request.documents)} documents to index '{request.index_name}'."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add documents: {str(e)}")

@app.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
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
            from app.vector_store import VectorStore
            vector_store = VectorStore()
            vector_store.add_documents(index_name="research_docs", documents=documents)
            return {"message": f"Successfully processed and added {len(documents)} files."}
        else:
            raise HTTPException(status_code=400, detail="No supported files were processed.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process files: {str(e)}")

async def run_graph_in_background(task: str, queue: asyncio.Queue):
    try:
        async for event in graph.astream({"task": task}):
            print("GRAPH EVENT:", event)
            for key, value in event.items():
                if key == '__end__':
                    final_report = value.get('report', 'No report generated.')
                    msg = f"event: end\ndata: {json.dumps(serialize_for_json({'report': final_report}))}\n\n"
                    print("SENDING TO QUEUE:", msg)
                    await queue.put(msg)
                else:
                    safe_value = serialize_for_json(value if value is not None else {})
                    msg = f"event: update\ndata: {json.dumps({key: safe_value})}\n\n"
                    print("SENDING TO QUEUE:", msg)
                    await queue.put(msg)
        await queue.put(None)
    except Exception as e:
        err_msg = f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        print("SENDING TO QUEUE (ERROR):", err_msg)
        await queue.put(err_msg)
        await queue.put(None)

@app.post("/generate-report")
async def generate_report(request: ResearchRequest):
    queue = asyncio.Queue()
    asyncio.create_task(run_graph_in_background(request.task, queue))

    async def stream_events():
        buffer = ""
        while True:
            item = await queue.get()
            if item is None:
                break
            if item.endswith("\n\n"):
                yield item
            queue.task_done()

    return StreamingResponse(stream_events(), media_type="text/event-stream")
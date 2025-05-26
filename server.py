from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
import google.generativeai as genai
import os
import uvicorn
from typing import List

from lib.tutor import TutorAgent
from lib.tools.util import QueryRequest, QueryResponse

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

app = FastAPI(title="AI Tutor Multi-Agent System")

if not api_key:
    raise ValueError("Please set the Gemini API Key in your .env file.")
genai.configure(api_key=api_key)

tutor = TutorAgent()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = Path("templates/home.html")
    html_content = html_path.read_text(encoding="utf-8")
    return html_content 

@app.get("/on-syllabus", response_class=HTMLResponse)
async def on_syllabus_page():
    html_path = Path("templates/on_syllabus.html")
    html_content = html_path.read_text(encoding="utf-8")
    return html_content

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    try:
        result = tutor.process(request.question, request.mode)
        return QueryResponse(
            answer=result["answer"],
            agent_used=result["agent_used"],
            tools_used=result.get("tools_used", []),
            sources=result.get("sources", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents():
    """List all available agents and their capabilities"""
    agents_info = []
    agents_info.append({
        "name": tutor.name,
        "description": tutor.description,
        "tools": []
    })
    
    for agent in tutor.specialized_agents:
        agents_info.append({
            "name": agent.name,
            "description": agent.description,
            "tools": [tool.name for tool in agent.tools]
        })
    
    return {"agents": agents_info}

@app.get("/check-books")
async def check_books_directory():
    """Check if books directory exists and list available files"""
    books_dir = Path("books")
    if not books_dir.exists():
        return {
            "exists": False,
            "message": "Books directory not found. Please create a 'books' directory and add your syllabus materials.",
            "files": []
        }
    
    files = []
    supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.doc'}
    
    for file_path in books_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            files.append({
                "name": file_path.name,
                "path": str(file_path.relative_to(books_dir)),
                "size": file_path.stat().st_size,
                "type": file_path.suffix.lower()
            })
    
    return {
        "exists": True,
        "message": f"Found {len(files)} supported files in books directory.",
        "files": files
    }

@app.post("/upload-books")
async def upload_books(files: List[UploadFile] = File(...)):
    """Upload files to the books directory"""
    try:
        books_dir = Path("books")
        books_dir.mkdir(exist_ok=True)
        
        uploaded_files = []
        skipped_files = []
        supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.doc'}
        
        for file in files:
            # Check file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in supported_extensions:
                skipped_files.append(f"{file.filename} (unsupported format)")
                continue
            
            # Check if file already exists
            file_path = books_dir / file.filename
            if file_path.exists():
                # Add timestamp to avoid overwriting
                import time
                timestamp = int(time.time())
                name_parts = Path(file.filename).stem, timestamp, Path(file.filename).suffix
                new_filename = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                file_path = books_dir / new_filename
            
            # Save the file
            try:
                content = await file.read()
                file_path.write_bytes(content)
                uploaded_files.append(file_path.name)
            except Exception as e:
                skipped_files.append(f"{file.filename} (error: {str(e)})")
        
        return {
            "success": True,
            "uploaded_files": uploaded_files,
            "skipped_files": skipped_files,
            "message": f"Successfully uploaded {len(uploaded_files)} files"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "uploaded_files": [],
            "skipped_files": []
        }

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
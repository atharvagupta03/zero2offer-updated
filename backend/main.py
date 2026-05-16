from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
from typing import Optional
from dotenv import load_dotenv
from backend.agent_app.agent import ask_agent
from backend.mcp_server.tools.profile import save_profile, read_resume

load_dotenv() # Load keys from .env

app = FastAPI()

# Configure CORS for Next.js (usually on 3000 or 3001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; refine for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "backend/mcp_server/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/auth/register")
async def register(req: LoginRequest):
    # For now, simple registration; returns a mock user_id
    # You would normally link this to Supabase
    user_id = req.email.replace("@", "_").replace(".", "_")
    return {"user_id": user_id, "status": "registered"}

@app.post("/auth/login")
async def login(req: LoginRequest):
    user_id = req.email.replace("@", "_").replace(".", "_")
    return {"user_id": user_id, "status": "logged_in"}

@app.post("/api/onboard")
async def onboard(
    user_id: str = Form(...),
    target_role: str = Form(...),
    extra_details: Optional[str] = Form(None),
    job_url: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    user_dir = os.path.join(UPLOAD_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process the resume
    try:
        resume_text = read_resume(file_path)
        
        analysis_prompt = f"Analyze my resume for the role of {target_role}. \nResume content: {resume_text}"
        if extra_details:
            analysis_prompt += f"\nAdditional Context: {extra_details}"
        if job_url:
            analysis_prompt += f"\nReference Job URL: {job_url}"
        
        analysis_prompt += "\n\nPlease provide a breakdown of my Strengths, Gaps/Weaknesses, and a Roadmap to success."
        
        analysis = await ask_agent(user_id, analysis_prompt)
        
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        response = await ask_agent(req.user_id, req.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{user_id}")
async def get_history(user_id: str):
    from backend.mcp_server.tools.profile import get_chat_history
    history = get_chat_history(user_id)
    return {"history": history}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

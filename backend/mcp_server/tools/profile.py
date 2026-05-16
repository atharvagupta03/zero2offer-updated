import os
import json
import PyPDF2
from supabase import create_client, Client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key) if url and key else None

LOCAL_DATA_DIR = "backend/mcp_server/data/uploads"

def get_profile(user_id: str) -> str:
    # Try Supabase first
    try:
        if supabase:
            res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
            if res.data:
                return json.dumps(res.data[0])
    except:
        pass

    # Fallback to local
    local_path = os.path.join(LOCAL_DATA_DIR, user_id, "profile_backup.json")
    if os.path.exists(local_path):
        with open(local_path, "r") as f:
            return f.read()
    
    return json.dumps({"error": "Profile not found", "user_id": user_id})

def save_profile(user_id: str, profile_json: str) -> str:
    data = json.loads(profile_json)
    data["user_id"] = user_id
    
    # Save to Supabase
    success = False
    try:
        if supabase:
            supabase.table("profiles").upsert(data).execute()
            success = True
    except:
        pass

    # Always save locally as backup
    user_dir = os.path.join(LOCAL_DATA_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    local_path = os.path.join(user_dir, "profile_backup.json")
    with open(local_path, "w") as f:
        f.write(profile_json)
        
    return "Profile saved successfully." if success else "Profile saved locally (Supabase unavailable)."

def read_resume(file_path: str) -> str:
    if not os.path.exists(file_path):
        return "Error: File not found."
    
    if file_path.endswith(".pdf"):
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    else:
        with open(file_path, "r") as f:
            return f.read()

def get_chat_history(user_id: str) -> list:
    """Fetches chat history from Supabase or local fallback."""
    try:
        if supabase:
            res = supabase.table("chat_history").select("*").eq("user_id", user_id).order("created_at").execute()
            if res.data:
                return res.data
    except:
        pass

    local_path = os.path.join(LOCAL_DATA_DIR, user_id, "chat_history.json")
    if os.path.exists(local_path):
        with open(local_path, "r") as f:
            return json.load(f)
    return []

def add_chat_message(user_id: str, role: str, content: str):
    """Adds a message to the chat history."""
    msg = {"user_id": user_id, "role": role, "content": content}
    
    try:
        if supabase:
            supabase.table("chat_history").insert(msg).execute()
    except:
        pass

    # Local backup
    user_dir = os.path.join(LOCAL_DATA_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    local_path = os.path.join(user_dir, "chat_history.json")
    
    history = []
    if os.path.exists(local_path):
        with open(local_path, "r") as f:
            history = json.load(f)
    
    history.append(msg)
    with open(local_path, "w") as f:
        json.dump(history, f)

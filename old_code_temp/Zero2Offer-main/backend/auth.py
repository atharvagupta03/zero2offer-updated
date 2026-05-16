import hashlib
import uuid
# Import both the connection and the initialization function
from backend.mcp_server.db import get_connection, init_db


init_db()

def hash_password(password: str) -> str:
    """Hashes a password for secure-ish storage (using SHA-256 )."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email: str, password: str) -> dict:
    """Creates a new user in the database."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Check if email already exists
    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cur.fetchone():
        conn.close()
        return {"success": False, "error": "Email already registered."}
        
    # Create unique ID and hash password
    user_id = f"student_{str(uuid.uuid4())[:8]}"
    hashed_pw = hash_password(password)
    
    try:
        cur.execute("INSERT INTO users (id, email, password) VALUES (?, ?, ?)", (user_id, email, hashed_pw))
        conn.commit()
        return {"success": True, "user_id": user_id}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def login_user(email: str, password: str) -> dict:
    """Verifies credentials against the database."""
    conn = get_connection()
    cur = conn.cursor()
    
    hashed_pw = hash_password(password)
    cur.execute("SELECT id FROM users WHERE email = ? AND password = ?", (email, hashed_pw))
    user = cur.fetchone()
    conn.close()
    
    if user:
        return {"success": True, "user_id": user["id"]}
    
    return {"success": False, "error": "Invalid email or password."}









import json
from db import get_connection

def save_profile(user_id: str, profile_json: str) -> str:
    """
    Save or replace the ENTIRE student profile for a specific user.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Ensure the user exists in the 'users' table so the Foreign Key doesn't fail
    cur.execute("INSERT OR IGNORE INTO users (id, email) VALUES (?, ?)", (user_id, f"{user_id}@test.com"))
    
    # 2. Upsert the profile data
    cur.execute("""
        INSERT INTO profiles (user_id, data) 
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET 
            data=excluded.data, 
            updated_at=CURRENT_TIMESTAMP
    """, (user_id, profile_json))
    
    conn.commit()
    conn.close()
    return f"Profile saved successfully for user {user_id}."

def get_profile(user_id: str) -> str:
    """Retrieve the profile data for a specific user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT data FROM profiles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    
    return row["data"] if row else json.dumps({"error": "No profile found."})

def update_skills(user_id: str, skills_json: str) -> str:
    """Update only the skills portion of a specific user's profile."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT data FROM profiles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    
    if not row:
        conn.close()
        return "No profile found to update."

    profile = json.loads(row["data"])
    profile["skills"] = json.loads(skills_json)

    cur.execute("""
        UPDATE profiles 
        SET data = ?, updated_at=CURRENT_TIMESTAMP 
        WHERE user_id = ?
    """, (json.dumps(profile), user_id))
    
    conn.commit()
    conn.close()
    return f"Skills updated for user {user_id}."





















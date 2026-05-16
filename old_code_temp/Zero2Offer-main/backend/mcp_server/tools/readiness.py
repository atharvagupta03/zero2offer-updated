import json
from pathlib import Path
from PyPDF2 import PdfReader
from .profile import get_profile


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

def evaluate_readiness(user_id: str, role_name: str, resume_file: str) -> str:
    """
    Aggregate profile + resume + role name for a specific user.
    """
    # 1. Get the user's profile
    profile_json = get_profile(user_id)
    try:
        profile_data = json.loads(profile_json)
    except json.JSONDecodeError:
        profile_data = {"error": "Could not parse profile data."}

    # 2. Find the resume in the user's specific secure folder
    user_folder = UPLOAD_DIR / user_id
    file_path = user_folder / resume_file
    
    if not file_path.exists():
        return json.dumps({"error": f"Resume file '{resume_file}' not found in user folder {user_id}."})

    # 3. Extract the text
    resume_text = ""
    if file_path.suffix.lower() == ".pdf":
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                resume_text += page.extract_text() or ""
        except Exception as e:
            return json.dumps({"error": f"Failed to read PDF: {str(e)}"})
    else:
        resume_text = file_path.read_text(errors="ignore")

    # 4. Return the aggregated data to the AI
    result = {
        "target_role": role_name,
        "profile": profile_data,
        "resume_text": resume_text
    }

    return json.dumps(result)































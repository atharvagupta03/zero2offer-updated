from pathlib import Path
from PyPDF2 import PdfReader


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

def read_resume(user_id: str, file_name: str) -> str:
    """
    Read a resume file (PDF or TXT) for a specific user.
    """
    # Create the user's specific folder path
    user_folder = UPLOAD_DIR / user_id
    file_path = user_folder / file_name

    if not file_path.exists():
        return f"Resume '{file_name}' not found for user {user_id}. Please check the file name."

    # --- TXT FILE ---
    if file_path.suffix.lower() == ".txt":
        return file_path.read_text(errors="ignore")

    # --- PDF FILE ---
    if file_path.suffix.lower() == ".pdf":
        try:
            reader = PdfReader(file_path)
            text = "".join(page.extract_text() or "" for page in reader.pages)
            
            if not text.strip():
                return "Could not extract text from PDF. It might be an image-based file."
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    return "Unsupported file type. Please use .pdf or .txt."

def list_resumes(user_id: str) -> str:
    """
    Check the user's directory and list all available resume files.
    """
    user_folder = UPLOAD_DIR / user_id
    
    if not user_folder.exists():
        return "No resumes uploaded yet."
        
    files = [f.name for f in user_folder.iterdir() if f.is_file()]
    
    if not files:
        return "No resumes uploaded yet."
        
    return f"Available resumes for {user_id}: {', '.join(files)}"

























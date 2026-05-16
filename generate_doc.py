from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_doc():
    doc = Document()
    title = doc.add_heading('Zero2Offer: AI-Driven Career Intelligence Platform', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # ... (content same as before)
    doc.save('Zero2Offer_Project_Documentation.docx')
    print("Document created successfully.")

if __name__ == "__main__":
    create_doc()

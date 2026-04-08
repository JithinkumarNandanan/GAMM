import os
import glob
from pypdf import PdfReader

def extract_text_from_pdfs():
    pdf_files = glob.glob(r"d:\Thesis_Antigravity\Documents\*.pdf") + glob.glob(r"d:\Thesis_Antigravity\EClass\**\*.pdf", recursive=True)
    
    with open(r"d:\Thesis_Antigravity\pdf_summaries.txt", "w", encoding="utf-8") as out_file:
        for i, pdf_path in enumerate(sorted(pdf_files), 1):
            out_file.write(f"--- [Source {i}] ---\n")
            out_file.write(f"File: {os.path.basename(pdf_path)}\n")
            out_file.write(f"Path: {pdf_path}\n\n")
            
            try:
                reader = PdfReader(pdf_path)
                # Extract first 3 pages to catch abstract and introduction
                num_pages = min(3, len(reader.pages))
                text = ""
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                # Keep it somewhat brief, maybe first 3000 chars
                out_file.write(text[:4000])
                out_file.write("\n\n" + "="*80 + "\n\n")
            except Exception as e:
                out_file.write(f"Error reading PDF: {e}\n\n")

if __name__ == "__main__":
    extract_text_from_pdfs()

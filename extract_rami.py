import os
from pypdf import PdfReader

def extract_text():
    pdf_path = r"d:\Thesis_Antigravity\Documents\GMA-Status-Report-RAMI-40-July-2015.pdf"
    
    with open(r"d:\Thesis_Antigravity\rami_summary.txt", "w", encoding="utf-8") as out_file:
        out_file.write(f"--- [Source 37] ---\n")
        out_file.write(f"File: {os.path.basename(pdf_path)}\n")
        out_file.write(f"Path: {pdf_path}\n\n")
        
        try:
            reader = PdfReader(pdf_path)
            # Extract first 5 pages to get a good summary of the standard
            num_pages = min(5, len(reader.pages))
            text = ""
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # Keep it somewhat brief, maybe first 5000 chars
            out_file.write(text[:5000])
        except Exception as e:
            out_file.write(f"Error reading PDF: {e}\n\n")

if __name__ == "__main__":
    extract_text()

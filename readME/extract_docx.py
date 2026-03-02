try:
    import docx
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    import docx

def extract_textFromDocx(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)

text = extract_textFromDocx(r"d:\Thesis_Antigravity\readME\Thesis_Draft.docx")
with open(r"d:\Thesis_Antigravity\readME\Thesis_Draft_extracted.txt", "w", encoding="utf-8") as f:
    f.write(text)
print("Extracted successfully.")

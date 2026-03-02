import re
import csv

def parse_summaries():
    input_file = r"d:\Thesis_Antigravity\pdf_summaries.txt"
    output_file = r"d:\Thesis_Antigravity\literature_discovery.csv"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    papers = []
    
    # Split by source marker
    sources = re.split(r'--- \[Source \d+\] ---', content)
    
    for idx, source in enumerate(sources):
        if not source.strip():
            continue
            
        file_match = re.search(r'File:\s*(.*?)\n', source)
        if not file_match:
            continue
            
        filename = file_match.group(1).strip()
        
        # Try to extract year from filename or text
        year_match = re.search(r'(201\d|202\d)', filename)
        year = year_match.group(1) if year_match else "Unknown"
        
        # Try to get title (heuristically the line after Path)
        path_match = re.search(r'Path:.*\n\n?(.*?\n.*?\n)', source, re.MULTILINE)
        if path_match:
            lines = [l.strip() for l in path_match.group(1).split('\n') if l.strip()]
            lines[0] if lines else "Unknown Title"
            # Some titles are split across lines, very rough heuristic
        else:
            pass
            
        # Determine relevance based on filenames
        if "AAS" in filename.upper() and "LLM" in filename.upper():
            relevance = "Highly Relevant: Application of LLMs for Automated AAS Mapping (Semantic Matching)"
        elif "AAS" in filename.upper() and ("OPC" in filename.upper() or "AML" in filename.upper()):
            relevance = "Relevant: AAS-to-OPC UA / AML Integration and Ontology alignment"
        elif "SEMANTIC" in filename.upper():
            relevance = "Relevant: Automated Semantic Mapping and Data Parsing"
        else:
            relevance = "Supporting Context: Industry 4.0, Digital Twins, or Standards (eCLASS, RAMI)"
            
        paper = {
            'Author': 'See full text / Extracted from PDF',
            'Year': year,
            'Paper Title': filename, # Use filename as proxy for title if we can't perfectly extract
            'Relevance to my Code': relevance,
            'Direct Download/DOI Link': f"Local File: {filename}"
        }
        papers.append(paper)
        
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Author', 'Year', 'Paper Title', 'Relevance to my Code', 'Direct Download/DOI Link'])
        writer.writeheader()
        writer.writerows(papers)
        
    print(f"Created {output_file} with {len(papers)} papers.")

if __name__ == "__main__":
    parse_summaries()

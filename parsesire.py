import pdfplumber
import re
import os
from pathlib import Path

# === CONFIG ===
PDF_PATH = "SIRE2FULL.pdf"   # <- put your big PDF here
OUTPUT_DIR = "sire_md"                   # folder for output .md files


def clean(text: str) -> str:
    if not text:
        return ""
    # Remove common footer patterns
    text = re.sub(r"SIRE 2\.0.*?Inspection Programme.*?\d+", "", text, flags=re.I)
    text = re.sub(r"\d+\s+SIRE 2\.0.*", "", text, flags=re.I)
    text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", text, flags=re.I)
    
    # normalize whitespace
    text = text.replace("\r", "\n")
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_sections(block: str) -> dict:
    """
    Extract:
    - paragraph_number
    - question
    - vessel_types
    - roviq_sequence
    - objective
    - suggested_inspector_actions
    - expected_evidence
    - potential_grounds

    Skips Industry guidance on purpose.
    """
    data = {}

    # Paragraph number: e.g. "2.1.1." or "4.1.1."
    m = re.match(r"\s*(\d+\.\d+\.\d+)\.", block)
    if not m:
        return None
    data["paragraph_number"] = m.group(1)

    # Question: from after paragraph number to "Vessel Types" (or "Short Question Text" if present)
    # We first trim off the leading "2.1.1."
    after_para = block[m.end():].strip()

    # Sometimes "Short Question Text ..." is in the middle; the question ends before that.
    # We stop question at "Short Question Text" or "Vessel Types" or "ROVIQ Sequence" (fallback).
    q_end = len(after_para)
    for marker in ["Short Question Text", "Vessel Types", "ROVIQ Sequence", "Objective"]:
        pos = after_para.find(marker)
        if pos != -1:
            q_end = min(q_end, pos)
    data["question"] = clean(after_para[:q_end])

    # Vessel Types
    m = re.search(r"Vessel Types\s*(.*?)\s*(ROVIQ Sequence|Objective|Industry guidance|Inspection Guidance)", 
                  block, re.S | re.I)
    data["vessel_types"] = clean(m.group(1)) if m else ""

    # ROVIQ Sequence
    m = re.search(r"ROVIQ Sequence\s*(.*?)\s*(Objective|Industry guidance|Inspection Guidance)", 
                  block, re.S | re.I)
    data["roviq_sequence"] = clean(m.group(1)) if m else ""

    # Objective - stop at "Industry guidance"
    m = re.search(r"Objective\s*(.*?)\s*(?:Industry guidance|Industry Guidance)", 
                  block, re.S | re.I)
    data["objective"] = clean(m.group(1)) if m else ""

    # Suggested Inspector Actions - appears after "Inspection Guidance" section
    # We need to skip both "Industry guidance" and "Inspection Guidance" sections
    m = re.search(r"Suggested Inspector Actions\s*(.*?)\s*(?:Expected Evidence|\n\s*\d+\.\d+\.\d+\.|$)", 
                  block, re.S | re.I)
    data["suggested_inspector_actions"] = clean(m.group(1)) if m else ""

    # Expected Evidence - comes after Suggested Inspector Actions
    m = re.search(r"Expected Evidence\s*(.*?)\s*(?:Potential Grounds for a Negative Observation|Potential Grounds|\n\s*\d+\.\d+\.\d+\.|$)", 
                  block, re.S | re.I)
    data["expected_evidence"] = clean(m.group(1)) if m else ""

    # Potential Grounds for a Negative Observation - comes after Expected Evidence
    m = re.search(r"Potential Grounds for a Negative Observation\s*(.*?)(?:\n\s*\d+\.\d+\.\d+\.|$)", 
                  block, re.S | re.I)
    if not m:
        # Try shorter version "Potential Grounds"
        m = re.search(r"Potential Grounds\s*(.*?)(?:\n\s*\d+\.\d+\.\d+\.|$)", 
                      block, re.S | re.I)
    data["potential_grounds"] = clean(m.group(1)) if m else ""

    return data


def make_markdown(data: dict) -> str:
    """
    Build the markdown string for one paragraph.
    """
    p = data["paragraph_number"]
    q = data["question"]
    vt = data["vessel_types"]
    rq = data["roviq_sequence"]
    obj = data["objective"]
    sia = data["suggested_inspector_actions"]
    ee = data["expected_evidence"]
    pg = data["potential_grounds"]

    md = []

    md.append(f"## Question {p}\n")
    md.append("**Paragraph Number:**")
    md.append(f"{p}\n")
    md.append("---\n")

    md.append("### **Question**")
    md.append(q + "\n")
    md.append("---\n")

    md.append("### **Vessel Types**")
    md.append(vt + "\n")
    md.append("---\n")

    md.append("### **ROVIQ Sequence**")
    md.append(rq + "\n")
    md.append("---\n")

    md.append("### **Objective**")
    md.append(obj + "\n")
    md.append("---\n")

   # if sia:
    md.append("### **Suggested Inspector Actions**")
    md.append(sia + "\n")
    md.append("---\n")

   # if ee:
    md.append("### **Expected Evidence**")
    md.append(ee + "\n")
    md.append("---\n")

    #if pg:
    md.append("### **Potential Grounds for a Negative Observation**")
    md.append(pg + "\n")

    return "\n".join(md).strip() + "\n"


def main():
    # Create output dir
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    print("Reading entire PDF...")
    
    # Step 1: Read all pages from page 8 onwards into one big text block
    full_text = ""
    with pdfplumber.open(PDF_PATH) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            if i < 8:  # Skip pages before page 8
                continue
            print(f"Reading page {i}...", end="\r")
            text = page.extract_text() or ""
            full_text += "\n" + text
    
    print(f"\nRead {len(full_text)} characters from PDF")
    print("Splitting into paragraphs...")
    
    # Step 2: Split by paragraph numbers to get complete paragraphs
    blocks = re.split(r'(\n\s*\d+\.\d+\.\d+\.(?=\s+\w))', full_text)
    
    print(f"Found {len(blocks)//2} potential paragraphs")
    print("Extracting sections and writing files...\n")
    
    # Step 3: Process each complete paragraph
    count = 0
    for j in range(1, len(blocks) - 1, 2):
        if j + 1 < len(blocks):
            block_text = blocks[j] + blocks[j + 1]
            data = extract_sections(block_text)
            if data:
                para = data["paragraph_number"]
                
                md_content = make_markdown(data)
                filename = f"{para.replace('.', '_')}.md"
                out_path = os.path.join(OUTPUT_DIR, filename)
                
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                
                count += 1
                if count % 50 == 0:
                    print(f"Processed {count} paragraphs...", end="\r")
    
    # Process the last paragraph if any
    if len(blocks) >= 2:
        block_text = blocks[-2] + blocks[-1] if len(blocks) % 2 == 0 else blocks[-1]
        data = extract_sections(block_text)
        if data:
            para = data["paragraph_number"]
            md_content = make_markdown(data)
            filename = f"{para.replace('.', '_')}.md"
            out_path = os.path.join(OUTPUT_DIR, filename)
            
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            
            count += 1

    print(f"\nDone. Wrote {count} markdown files into '{OUTPUT_DIR}'.")


if __name__ == "__main__":
    main()

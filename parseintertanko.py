import re
import fitz  # PyMuPDF
import easyocr
import numpy as np
from PIL import Image
import io

PDF_PATH = "intertanko - seafarers practical guide to sire 2.0 inspections - with full comments.pdf"
OUTPUT_SQL = "ecdis_inserts.sql"

# Initialize EasyOCR reader (will download model on first use)
reader = easyocr.Reader(['en'], gpu=False)

def clean(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text

def parse_page_text(text):
    """
    Parse ONE page based on the actual PDF structure.
    Returns a dict ready for INSERT or None if this page is irrelevant.
    """
    # Quick filter: only process pages that contain the key phrase
    if "Practical Guidelines" not in text:
        return None

    data = {}

    # Paragraph number like 2.1.1 - at the very start of the question
    m = re.search(r"(\d+\.\d+\.\d+)\.?\s*[A-Z]", text)
    data["paragraph_number"] = m.group(1) if m else ""

    # Question - from paragraph number until "Question Category" or table starts
    m = re.search(r"\d+\.\d+\.\d+\.?\s+(.*?)(?:Question Category|Objective)", text, re.S | re.I)
    data["question"] = clean(m.group(1)) if m else ""

    # Question category - look for Hardware-Human-Process pattern
    m = re.search(r"Question Category.*?Hardware[- ]Human[- ]Process", text, re.S | re.I)
    data["question_category"] = "Hardware-Human-Process" if m else ""

    # PIQ - look for PIQ indicator or icon
    data["piq"] = "Yes" if re.search(r"\bPIQ\b", text, re.I) else ""
    
    # Photograph - look for Photograph indicator
    data["photograph"] = "Yes" if re.search(r"\bPhotograph\b", text, re.I) else ""
    
    # Question type - Core, Rotational 1 or 2
    m = re.search(r"Question Type.*?\((.*?)\)", text, re.S | re.I)
    data["question_type"] = clean(m.group(1)) if m else ""

    # Objective - between "Objective" and "ROVIQ Sequence"
    # Also try capturing if text appears on same line after "Objective"
    m = re.search(r"Objective[:\s]+(.*?)(?:ROVIQ Sequence|Tagged Rank)", text, re.S | re.I)
    if not m:
        # Alternative: look for text after Objective until next known section
        m = re.search(r"Objective\s+(.*?)(?:ROVIQ|Tagged|Verification)", text, re.S | re.I)
    data["objective"] = clean(m.group(1)) if m else ""

    # ROVIQ sequence - between "ROVIQ Sequence" and "Tagged Rank"
    m = re.search(r"ROVIQ Sequence\s+(.*?)Tagged Rank", text, re.S | re.I)
    data["roviq_sequence"] = clean(m.group(1)) if m else ""

    # Tagged rank - between "Tagged Rank" and "Verification by"
    m = re.search(r"Tagged Rank\s+(.*?)(?:Verification by|Practical Guidelines)", text, re.S | re.I)
    data["tagged_rank"] = clean(m.group(1)) if m else ""

    # Verification by - between "Verification by" and "Practical Guidelines"
    m = re.search(r"Verification by\s+(.*?)Practical Guidelines", text, re.S | re.I)
    data["verification_by"] = clean(m.group(1)) if m else ""

    # Human requirements - after "Human" heading in Practical Guidelines section
    m = re.search(r"Practical Guidelines.*?Human\s+(.*?)(?:Process|Hardware|TMSA|Comments)", text, re.S | re.I)
    data["human_requirements"] = clean(m.group(1)) if m else ""

    # Process requirements - after "Process" heading
    m = re.search(r"Process\s+(.*?)(?:Hardware|TMSA|Comments)", text, re.S | re.I)
    data["process_requirements"] = clean(m.group(1)) if m else ""

    # Hardware requirements - after "Hardware" heading
    m = re.search(r"Hardware\s+(.*?)(?:TMSA|Comments/SMS Reference)", text, re.S | re.I)
    data["hardware_requirements"] = clean(m.group(1)) if m else ""

    # TMSA requirements - after "TMSA" heading
    m = re.search(r"TMSA\s+(.*?)(?:Comments/SMS Reference|$)", text, re.S | re.I)
    data["tmsa_requirements"] = clean(m.group(1)) if m else ""

    # Comments / SMS references - after "Comments/SMS Reference"
    m = re.search(r"Comments/SMS Reference\s+(.*?)(?:\d+\s+Seafarers|$)", text, re.S | re.I)
    data["comments_sms_reference"] = clean(m.group(1)) if m else ""

    return data

def dict_to_insert(d):
    cols = [
        "paragraph_number", "question", "question_category", "piq", "photograph",
        "question_type", "objective", "roviq_sequence", "tagged_rank",
        "verification_by", "human_requirements", "process_requirements",
        "hardware_requirements", "tmsa_requirements",
        "comments_sms_reference"
    ]

    values = []
    for c in cols:
        v = d.get(c, "")
        v = v.replace("'", "''")  # escape single quotes for SQL
        values.append(f"'{v}'")

    return f"INSERT INTO ecdis_procedures ({', '.join(cols)}) VALUES ({', '.join(values)});"

def main():
    inserts = []
    
    # Open output file for incremental writing
    print(f"Opening output file: {OUTPUT_SQL}")
    output_file = open(OUTPUT_SQL, "w", encoding="utf-8")
    
    print("Opening PDF and performing OCR...")
    pdf_document = fitz.open(PDF_PATH)
    total_pages = len(pdf_document)
    
    for page_num in range(total_pages):
        print(f"Processing page {page_num + 1}/{total_pages}...")
        
        # Stop at page 150
       # if page_num + 1 > 20:
        #    print(f"\n⚠️  Reached page 150 limit - stopping processing")
         #   break
        
        page = pdf_document[page_num]
        
        # Render page to image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
        img_data = pix.tobytes("png")
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(img_data))
        
        # Perform OCR using EasyOCR
        result = reader.readtext(np.array(image))
        
        # Combine all detected text
        text = " ".join([detection[1] for detection in result])
        
        # Debug: Show if page contains the filter phrase
        has_guidelines = "Practical Guidelines" in text
        print(f"  Page {page_num + 1} - Contains 'Practical Guidelines': {has_guidelines}")
        if has_guidelines:
            print(f"  Preview: {text[:150]}...")
        
        parsed = parse_page_text(text)
        if parsed:
            print(f"  ✓ Successfully parsed page {page_num + 1}")
            insert_stmt = dict_to_insert(parsed)
            inserts.append(insert_stmt)
            # Write immediately to file
            output_file.write(insert_stmt + "\n")
            output_file.flush()  # Force write to disk
            print(f"  → Written to file (total so far: {len(inserts)})")
        else:
            print(f"  ✗ Page {page_num + 1} did not match parsing criteria")
    
    pdf_document.close()
    output_file.close()

    print(f"\n{'='*60}")
    print(f"✓ Completed processing (stopped at page {min(page_num + 1, 150)})")
    
    # Verify the file was written
    import os
    if os.path.exists(OUTPUT_SQL):
        file_size = os.path.getsize(OUTPUT_SQL)
        print(f"✓ File created: {OUTPUT_SQL}")
        print(f"✓ File size: {file_size:,} bytes")
        print(f"✓ Total INSERT statements: {len(inserts)}")
        
        # Show a sample of the first INSERT statement
        if inserts:
            print(f"\nFirst INSERT statement preview:")
            print(inserts[0][:200] + "..." if len(inserts[0]) > 200 else inserts[0])
    else:
        print(f"✗ ERROR: File was not created!")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

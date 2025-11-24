# Maritime SIRE and Intertanko Parser

This project parses maritime inspection documents (SIRE and Intertanko) and stores them in a PostgreSQL database for cross-referencing with company procedures.

## Project Structure

- `parsesire.py` - Parses SIRE 2.0 PDF and generates markdown files
- `parseintertanko.py` - OCR-based parser for Intertanko PDF  
- `insert_sire_md.py` - Inserts SIRE markdown files into PostgreSQL
- `sire_postgres.sql` - Database schema for SIRE data
- `intertanko_postgres.sql` - Database schema for Intertanko data
- `sire_md/` - Generated markdown files (388 SIRE questions)
- `ecdis_inserts.sql` - Generated INSERT statements for Intertanko data

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/LiaProjects/Maritime.git
cd Maritime
```

### 2. Create Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

### 3. Install dependencies
```bash
pip install pymupdf easyocr numpy pillow pdfplumber psycopg2-binary python-docx
```

### 4. Start PostgreSQL with Docker
```bash
docker run -d \
  --name maritime-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=maritime \
  -p 5432:5432 \
  postgres:16-alpine
```

### 5. Create database schema
```bash
# For SIRE data
docker exec -i maritime-postgres psql -U postgres -d maritime < sire_postgres.sql

# For Intertanko data  
docker exec -i maritime-postgres psql -U postgres -d maritime < intertanko_postgres.sql
```

### 6. Insert data into database
```bash
# Insert SIRE markdown files
python insert_sire_md.py

# Insert Intertanko data
docker exec -i maritime-postgres psql -U postgres -d maritime < ecdis_inserts_fixed.sql
```

## Running the Parsers

### Parse SIRE PDF
```bash
python parsesire.py
```
This generates 388 markdown files in `sire_md/` directory.

### Parse Intertanko PDF (OCR)
```bash
python parseintertanko.py
```
This generates `ecdis_inserts.sql` with INSERT statements.

## Database Access

Connect to the database:
```bash
docker exec -it maritime-postgres psql -U postgres -d maritime
```

Query examples:
```sql
-- View SIRE questions
SELECT paragraph_number, LEFT(sire_md_file, 100) 
FROM intertanko.sire_md_files 
LIMIT 10;

-- View Intertanko procedures with SMS references
SELECT paragraph_number, LEFT(question, 80), LEFT(comments_sms_reference, 60)
FROM intertanko.ecdis_procedures 
WHERE comments_sms_reference != ''
LIMIT 10;

-- Search SIRE questions
SELECT paragraph_number 
FROM intertanko.sire_md_files 
WHERE to_tsvector('english', sire_md_file) @@ to_tsquery('english', 'ECDIS');
```

## Data Mapping

The project maintains a three-way mapping:

1. **Intertanko ECDIS Procedures** (`intertanko.ecdis_procedures`)
   - Contains questions from Intertanko training guide
   - `comments_sms_reference` column links to company procedures

2. **Company Procedures Manual** (Word document)
   - Contains actual implementation procedures
   - References both Intertanko and SIRE

3. **SIRE Inspection Questions** (`intertanko.sire_md_files`)
   - Contains official inspection checklist
   - Used by inspectors during vessel audits

## Stopping/Restarting

Stop Docker container:
```bash
docker stop maritime-postgres
```

Restart Docker container:
```bash
docker start maritime-postgres
```

Remove Docker container:
```bash
docker stop maritime-postgres
docker rm maritime-postgres
```

## Git Workflow

Push changes:
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

Pull latest changes:
```bash
git pull origin main
```

## Notes

- The Intertanko PDF uses OCR (EasyOCR) because it's image-based
- The SIRE PDF uses text extraction (pdfplumber)
- PostgreSQL uses GIN indexes for full-text search
- All text fields use TEXT datatype to handle long content

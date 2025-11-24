import os
import psycopg2

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'maritime',
    'user': 'postgres',
    'password': 'postgres'
}

MD_DIR = "sire_md"

def main():
    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get all .md files
    md_files = sorted([f for f in os.listdir(MD_DIR) if f.endswith('.md')])
    print(f"Found {len(md_files)} markdown files")
    
    inserted = 0
    for filename in md_files:
        # Extract paragraph number from filename (e.g., "2_1_1.md" -> "2.1.1")
        paragraph_number = filename.replace('.md', '').replace('_', '.')
        
        # Read file content
        filepath = os.path.join(MD_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Insert into database
        try:
            cursor.execute(
                "INSERT INTO intertanko.sire_md_files (paragraph_number, sire_md_file) VALUES (%s, %s)",
                (paragraph_number, content)
            )
            inserted += 1
            if inserted % 50 == 0:
                print(f"Inserted {inserted} files...", end='\r')
        except Exception as e:
            print(f"\nError inserting {filename}: {e}")
            conn.rollback()
            continue
    
    # Commit all inserts
    conn.commit()
    print(f"\nDone! Inserted {inserted} markdown files into database")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM intertanko.sire_md_files")
    count = cursor.fetchone()[0]
    print(f"Total rows in table: {count}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()

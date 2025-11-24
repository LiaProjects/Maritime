-- PostgreSQL version - connect to maritime database first

CREATE TABLE intertanko.sire_md_files (
    id SERIAL PRIMARY KEY,
    paragraph_number VARCHAR(20) NOT NULL,
    sire_md_file TEXT NOT NULL
);

-- Helpful indexes
CREATE INDEX idx_sire_md_paragraph_number
    ON intertanko.sire_md_files (paragraph_number);

-- GIN index for full-text search on markdown content
CREATE INDEX idx_sire_md_file_gin 
    ON intertanko.sire_md_files USING GIN (to_tsvector('english', sire_md_file));

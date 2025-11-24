-- PostgreSQL version of intertanko schema

-- 1. Create database (run this separately if database doesn't exist)
-- CREATE DATABASE maritime;

-- 2. Connect to the maritime database first in DBeaver, then run:

-- 3. Create schema
CREATE SCHEMA IF NOT EXISTS intertanko;

-- 4. Create the table inside the intertanko schema
CREATE TABLE intertanko.ecdis_procedures (
    id SERIAL PRIMARY KEY,

    paragraph_number TEXT,
    question TEXT,
    question_category TEXT,
    piq TEXT,
    photograph TEXT,
    question_type TEXT,
    objective TEXT,
    roviq_sequence TEXT,
    tagged_rank TEXT,
    verification_by TEXT,

    human_requirements TEXT,
    process_requirements TEXT,
    hardware_requirements TEXT,
    tmsa_requirements TEXT,

    comments_sms_reference TEXT
);

-- 5. Create indexes for full-text search using GIN indexes

CREATE INDEX idx_paragraph_number_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', paragraph_number));

CREATE INDEX idx_question_category_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', question_category));

CREATE INDEX idx_piq_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', piq));

CREATE INDEX idx_photograph_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', photograph));

CREATE INDEX idx_question_type_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', question_type));

CREATE INDEX idx_roviq_sequence_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', roviq_sequence));

CREATE INDEX idx_tagged_rank_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', tagged_rank));

CREATE INDEX idx_verification_by_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', verification_by));

CREATE INDEX idx_question_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', question));

CREATE INDEX idx_objective_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', objective));

CREATE INDEX idx_human_req_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', human_requirements));

CREATE INDEX idx_process_req_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', process_requirements));

CREATE INDEX idx_hardware_req_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', hardware_requirements));

CREATE INDEX idx_tmsa_req_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', tmsa_requirements));

CREATE INDEX idx_comments_sms_gin 
    ON intertanko.ecdis_procedures USING gin(to_tsvector('english', comments_sms_reference));

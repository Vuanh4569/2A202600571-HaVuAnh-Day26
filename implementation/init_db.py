import sqlite3
import os


SCHEMA_SQL = """
-- Create students table
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cohort TEXT NOT NULL,
    score REAL
);

-- Create courses table
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL
);

-- Create enrollments table
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    grade REAL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
"""

SEED_SQL = """
-- Insert sample students
INSERT INTO students (name, email, cohort, score) VALUES
    ('Alice Johnson', 'alice@example.com', 'A1', 85.5),
    ('Bob Smith', 'bob@example.com', 'A1', 92.0),
    ('Carol Davis', 'carol@example.com', 'A2', 78.5),
    ('David Wilson', 'david@example.com', 'A2', 88.0),
    ('Eva Brown', 'eva@example.com', 'B1', 95.5);

-- Insert sample courses
INSERT INTO courses (code, title, credits) VALUES
    ('CS101', 'Introduction to Programming', 3),
    ('CS201', 'Data Structures', 4),
    ('CS301', 'Algorithms', 4),
    ('MATH101', 'Calculus I', 4),
    ('MATH201', 'Linear Algebra', 3);

-- Insert sample enrollments
INSERT INTO enrollments (student_id, course_id, grade) VALUES
    (1, 1, 90.0),
    (1, 2, 85.0),
    (2, 1, 95.0),
    (2, 3, 88.0),
    (3, 2, 82.0),
    (3, 4, 75.0),
    (4, 3, 90.0),
    (4, 5, 85.0),
    (5, 1, 98.0),
    (5, 3, 94.0);
"""


def create_database(db_path="lab_database.db"):
    """
    Create and initialize the SQLite database with schema and seed data.
    
    Args:
        db_path: Path to the database file (default: lab_database.db)
    
    Returns:
        str: Absolute path to the created database
    """
    # Get absolute path
    abs_path = os.path.abspath(db_path)
    
    # Connect to database (creates file if it doesn't exist)
    conn = sqlite3.connect(abs_path)
    cursor = conn.cursor()
    
    try:
        # Execute schema
        cursor.executescript(SCHEMA_SQL)
        
        # Execute seed data
        cursor.executescript(SEED_SQL)
        
        # Commit changes
        conn.commit()
        
        print(f"Database created successfully at: {abs_path}")
        return abs_path
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    create_database()

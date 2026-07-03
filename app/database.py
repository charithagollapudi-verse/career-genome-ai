import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "career_genome.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_role TEXT NOT NULL,
        skills TEXT NOT NULL,
        interests TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_market_trends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        skill TEXT NOT NULL,
        demand_index REAL NOT NULL,
        projected_growth REAL NOT NULL,
        year INTEGER NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roadmaps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER NOT NULL,
        roadmap_json TEXT NOT NULL,
        FOREIGN KEY (profile_id) REFERENCES profiles (id)
    )
    """)
    
    conn.commit()
    
    # Seed job market trends if empty
    cursor.execute("SELECT COUNT(*) FROM job_market_trends")
    if cursor.fetchone()[0] == 0:
        seed_data = [
            # Machine Learning Engineer
            ("Machine Learning Engineer", "Python", 0.95, 15.0, 2026),
            ("Machine Learning Engineer", "Python", 0.96, 16.5, 2027),
            ("Machine Learning Engineer", "Python", 0.98, 18.0, 2028),
            ("Machine Learning Engineer", "Deep Learning", 0.90, 20.0, 2026),
            ("Machine Learning Engineer", "Deep Learning", 0.92, 22.0, 2027),
            ("Machine Learning Engineer", "Deep Learning", 0.95, 25.0, 2028),
            ("Machine Learning Engineer", "MLOps", 0.85, 28.0, 2026),
            ("Machine Learning Engineer", "MLOps", 0.88, 30.0, 2027),
            ("Machine Learning Engineer", "MLOps", 0.92, 32.0, 2028),
            ("Machine Learning Engineer", "Docker", 0.80, 12.0, 2026),
            ("Machine Learning Engineer", "Docker", 0.82, 11.5, 2027),
            ("Machine Learning Engineer", "Docker", 0.84, 10.0, 2028),
            ("Machine Learning Engineer", "Model Deployment", 0.82, 18.0, 2026),
            ("Machine Learning Engineer", "Model Deployment", 0.85, 20.0, 2027),
            ("Machine Learning Engineer", "Model Deployment", 0.88, 22.0, 2028),
            
            # Cloud Engineer
            ("Cloud Engineer", "Python", 0.85, 8.0, 2026),
            ("Cloud Engineer", "Python", 0.86, 7.5, 2027),
            ("Cloud Engineer", "Python", 0.87, 7.0, 2028),
            ("Cloud Engineer", "Cloud (AWS/GCP)", 0.95, 14.0, 2026),
            ("Cloud Engineer", "Cloud (AWS/GCP)", 0.96, 15.0, 2027),
            ("Cloud Engineer", "Cloud (AWS/GCP)", 0.98, 16.5, 2028),
            ("Cloud Engineer", "DevOps", 0.90, 12.0, 2026),
            ("Cloud Engineer", "DevOps", 0.92, 13.0, 2027),
            ("Cloud Engineer", "DevOps", 0.94, 14.0, 2028),
            ("Cloud Engineer", "Docker", 0.85, 10.0, 2026),
            ("Cloud Engineer", "Docker", 0.87, 10.5, 2027),
            ("Cloud Engineer", "Docker", 0.89, 11.0, 2028),
            ("Cloud Engineer", "Kubernetes", 0.88, 18.0, 2026),
            ("Cloud Engineer", "Kubernetes", 0.91, 19.5, 2027),
            ("Cloud Engineer", "Kubernetes", 0.93, 21.0, 2028),
        ]
        
        cursor.executemany("""
        INSERT INTO job_market_trends (role, skill, demand_index, projected_growth, year)
        VALUES (?, ?, ?, ?, ?)
        """, seed_data)
        conn.commit()
    
    conn.close()

# Initialize when imported/run
init_db()

import os
import sys
import mysql.connector

# Add parent directory to path to import db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import get_conn, execute

def run_migration():
    print("Connecting to database and running migrations...")
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        
        # Check if columns already exist
        cur.execute("SHOW COLUMNS FROM loan_applications")
        columns = [row['Field'] for row in cur.fetchall()]
        
        if 'ml_default_probability' not in columns:
            print("Adding ml_default_probability column...")
            cur.execute("ALTER TABLE loan_applications ADD COLUMN ml_default_probability DECIMAL(5,2) DEFAULT NULL")
            
        if 'ml_risk_band' not in columns:
            print("Adding ml_risk_band column...")
            cur.execute("ALTER TABLE loan_applications ADD COLUMN ml_risk_band ENUM('Low', 'Medium', 'High') DEFAULT NULL")
            
        conn.commit()
        cur.close()
        conn.close()
        print("Schema updated successfully!")
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == "__main__":
    run_migration()

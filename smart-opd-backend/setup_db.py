import psycopg2
import os

def setup():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found!")
        return

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Read and execute the SQL file
    with open('database/init.sql', 'r') as f:
        sql = f.read()
        cursor.execute(sql)
        
    print("Database tables created successfully!")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    setup()
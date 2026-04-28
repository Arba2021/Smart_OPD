import psycopg2
import os

print("Connecting to Render Database...")
conn = psycopg2.connect("postgresql://smart_opd_db_user:LqiCcxqz8bl78x3ICI4mVtLxXOmP797J@dpg-d7o99t3eo5us739olbog-a.singapore-postgres.render.com/smart_opd_db")
conn.autocommit = True
cursor = conn.cursor()

print("Reading init.sql...")
with open(r"C:\Users\arun0\Videos\hackathon\smart-opd\database\init.sql", "r", encoding="utf-8") as f:
    sql = f.read()

print("Creating tables...")
cursor.execute(sql)

print("SUCCESS! All database tables created!")
cursor.close()
conn.close()

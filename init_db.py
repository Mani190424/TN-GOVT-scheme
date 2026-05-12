import os
import pymysql
import ssl

with open('database.sql', 'r') as f:
    sql_script = f.read()

# remove 'USE tn_scheme_bot;' and 'CREATE DATABASE tn_scheme_bot;' if exists
sql_script = sql_script.replace('CREATE DATABASE IF NOT EXISTS tn_scheme_bot;', '')
sql_script = sql_script.replace('USE tn_scheme_bot;', '')

try:
    conn = pymysql.connect(
        host="gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
        port=4000,
        user="2EHyFqUU4Gbz7E5.root",
        password="QG7YVcAWoj4VD4zy",
        database="test",
        ssl={'cert_reqs': ssl.CERT_NONE}
    )
    cursor = conn.cursor()
    
    # Split the script by ';'
    statements = sql_script.split(';')
    for statement in statements:
        if statement.strip():
            cursor.execute(statement)
            conn.commit()
    print("Database initialization successful.")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")

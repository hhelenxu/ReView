import psycopg2
import databaseconfig as dbconfig

# connect to zoom_app database
try:
    conn = psycopg2.connect("dbname={} user={} password={}".format(dbconfig.database["db"], dbconfig.database["user"], dbconfig.database["password"]))
    print("Connected to the database.")
except:
    print("Unable to connect to database.")

cur = conn.cursor()

# create users table
try:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        name VARCHAR,
        id VARCHAR UNIQUE,
        email VARCHAR UNIQUE
    );
    """)
    conn.commit()
    print("Created table.")
except:
    print("Failed to create table.")

# create zoom recordings table
try:
    # text type
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recordings (
        id SERIAL,
        visible BOOLEAN,
        topic VARCHAR,
        start_time VARCHAR,
        video VARCHAR,
        transcript VARCHAR,
        text VARCHAR,
        summary VARCHAR,
        tokens TSVECTOR,
        tags JSONB,
        zoom_id varchar UNIQUE
    );
    """)
    conn.commit()
    print("Created table.")
except:
    print("Failed to create table.")
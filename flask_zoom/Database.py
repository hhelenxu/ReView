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
    print("Created users table.")
except:
    print("Failed to create users table.")

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
        zoom_id varchar UNIQUE,
        unformat_time TIMESTAMP,
        notes TEXT[],
        summary_approved BOOLEAN
    );
    """)
    conn.commit()
    print("Created recordings table.")
except:
    print("Failed to create recordings table.")

# create activity table
try:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity (
        time VARCHAR,
        name VARCHAR,
        email VARCHAR,
        recording_id INTEGER,
        action VARCHAR,
        notes VARCHAR,
        recording_title VARCHAR,
        unformat_time TIMESTAMP
    );
    """)
    conn.commit()
    print("Created activity table.")
except:
    print("Failed to create activity table.")
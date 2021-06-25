import psycopg2

# connect to zoom_app database
try:
    conn = psycopg2.connect("dbname='zoom_app' user='hzx' password='password'")
    print("Connected to the database.")
except:
    print("Unable to connect to database.")

cur = conn.cursor()

# create users table
try:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        name varchar,
        id varchar UNIQUE,
        email varchar UNIQUE
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
        id varchar UNIQUE,
        topic varchar,
        start_time varchar,
        video varchar,
        transcript varchar,
        text varchar,
        summary varchar
    );
    """)
    conn.commit()
    print("Created table.")
except:
    print("Failed to create table.")
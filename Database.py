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
        name varchar(100),
        id varchar(500) UNIQUE,
        email varchar(100) UNIQUE
    );
    """)
    conn.commit()
    print("Created table.")
except:
    print("Failed to create table.")

# create zoom recordings table
try:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recordings (
        id varchar(1000) UNIQUE,
        topic varchar(100),
        start_time varchar(50),
        video varchar(1000),
        transcript varchar(1000),
        text varchar,
        summary varchar(1000)
    );
    """)
    conn.commit()
    print("Created table.")
except:
    print("Failed to create table.")
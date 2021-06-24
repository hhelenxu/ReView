import sqlite3

connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO posts (title, recordingURL, tags, summary, transcription) VALUES (?, ?, ?, ?, ?)",
            ('First Recording', 'recording1.com', 'Code, Plus', 'Summary of first recording', 'Transcription of first recording')
            )

cur.execute("INSERT INTO posts (title, recordingURL, tags, summary, transcription) VALUES (?, ?, ?, ?, ?)",
            ('Second Recording', 'recording2.com', 'Math, Science', 'Summary of second recording', 'Transcription of second recording')
            )

connection.commit()
connection.close()
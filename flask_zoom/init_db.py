import sqlite3

connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO posts (title, recordingURL, tags, summary, transcription) VALUES (?, ?, ?, ?, ?)",
            ('First Recording', 'https://www.recording1.com', 'Code, Plus', 'Summary of first recording', 'Transcription of first recording')
            )

cur.execute("INSERT INTO posts (title, recordingURL, tags, summary, transcription) VALUES (?, ?, ?, ?, ?)",
            ('Second Recording', 'https://www.recording2.com', 'Math, Science', 'Summary of second recording', 'Transcription of second recording')
            )

cur.execute("INSERT INTO posts (title, recordingURL, tags, summary, transcription) VALUES (?, ?, ?, ?, ?)",
            ('Zoom App Development Project', 'https://zoom.us/rec/play/AUYE48YN7hblx6YRpz8t5KpIaqSM2q70fWcjTvi4UGIKV3z42fbUy8SpPwqt6Qtfh0EEPGipEMqTuY2s.mZFeY_9YZZAf7hSg?autoplay=true&amp;startTime=1624289693000', 'Daily stand up, Cod+', 'Over the past year, Zoom has played an integral role in everyday communications at Duke and across the globe. Utilizing mobile technology and the Zoom Developer Platform, a team of students work with Duke’s Office of Information Technology and other partners across campus to develop a tool or suite of tools that will further assist in evolving Zoom’s presence and capabilities within higher education. The students will develop an educational app that further enhances the collaborative efforts between instructors and students, as well as opens the door to new resources supporting education. With almost a full year of hindsight available, we can begin to fill in the gaps of where Zoom can be improved to meet Duke’s needs of providing a hybrid/remote teaching and learning experience that rivals that of an in-person offering.', 'Transcription of recording')
            )

connection.commit()
connection.close()
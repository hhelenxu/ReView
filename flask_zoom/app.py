from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort

# db imports
import psycopg2
import databaseconfig as dbconfig
import zoomconfig
from zoom import *


def get_db_connection():
    conn = psycopg2.connect("dbname={} user={} password={}".format(dbconfig.database["db"], dbconfig.database["user"], dbconfig.database["password"]))
    return conn

def get_recording(recording_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM recordings WHERE id=%s',(recording_id,))
    recording = cur.fetchone()
    conn.close()
    if recording is None:
        abort(404)
    return recording


app = Flask(__name__)
app.config['SECRET_KEY'] = 'NlcPJLmeyeXMn4KpISh0hGQ3cWQIQbbnE0WwfpeZxjiftirfP2sCNI0GA6P96kCP'  # used to secure sessions, which allow Flask to remember information from one request to another


@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    # get recordings
    cur.execute("SELECT * FROM recordings WHERE visible=TRUE")
    recordings = cur.fetchall()

    # testing
    # print(recordings[0][9])
    # recordings[0][9]["test"] = 0
    # print(recordings[0][9])
    cur.close()
    conn.close()

    return render_template('index.html', recordings=recordings)

@app.route('/card')
def card():
    conn = get_db_connection()
    cur = conn.cursor()

    # get recordings
    cur.execute("SELECT * FROM recordings WHERE visible=TRUE")
    recordings = cur.fetchall()

    # testing
    # print(recordings[0][9])
    # recordings[0][9]["test"] = 0
    # print(recordings[0][9])
    cur.close()
    conn.close()

    return render_template('card.html', recordings=recordings)


@app.route('/<string:recording_id>')
def recording(recording_id):
    recording = get_recording(recording_id)
    return render_template('recording.html', recording=recording)


@app.route('/<string:recording_id>/edit', methods=('GET', 'POST'))
def edit(recording_id):
    recording = get_recording(recording_id)
    originalTags = recording[9]

    if request.method == 'POST':
        title = request.form['title']
        summary = request.form['summary']
        transcription = request.form['transcription']
        tags = request.form['tags'].split(',')

        # remove leading and trailing whitespaces
        for i in range(len(tags)):
            tags[i] = tags[i].strip()

        # adding new tags
        for tag in tags:
            if tag not in originalTags:
                recording[9][tag] = 0

        newDict = recording[9]
        # deleting tags
        toDelete = []
        for tag in recording[9]:
            if tag not in tags:
                toDelete.append(tag)

        for s in toDelete:
            del newDict[s]

        # newDict = {tag: value for (tag, value) in recording[9] if tag in tags}
        # {key: value for (key, value) in iterable}

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE recordings SET topic = %s, summary = %s, text = %s, tags = %s where id = %s', (title, summary, transcription, json.dumps(newDict), recording_id))
            cur.close()
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('edit.html', recording=recording)


@app.route('/<string:recording_id>/delete', methods=('POST',))
def delete(recording_id):
    conn = get_db_connection()
    cur = conn.cursor()
    change_visibility(conn, cur, recording_id)
    conn.commit()
    cur.close()
    conn.close()
    flash('"{}" was successfully deleted!'.format(recording_id))
    return redirect(url_for('index'))
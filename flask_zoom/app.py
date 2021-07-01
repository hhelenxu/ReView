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
    cur.close()
    conn.close()

    return render_template('index.html', recordings=recordings)


@app.route('/<string:recording_id>')
def recording(recording_id):
    recording = get_recording(recording_id)
    return render_template('recording.html', recording=recording)


@app.route('/<string:recording_id>/edit', methods=('GET', 'POST'))
def edit(recording_id):
    recording = get_recording(recording_id)

    if request.method == 'POST':
        title = request.form['title']
        # tags = request.form['tags']
        summary = request.form['summary']
        transcription = request.form['transcription']
        tags = "{" + request.form['tags'] + "}"
        # newTags = request.form['newTags']
        # print(tags, newTags)

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE recordings SET topic = %s, summary = %s, text = %s, tags = %s where id = %s', (title, summary, transcription, tags, recording_id))
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
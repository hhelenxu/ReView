from flask import Flask, render_template, request, url_for, flash, redirect, session
from flask_session import Session
from werkzeug.exceptions import abort
import jwt
from jwt import PyJWKClient
import psycopg2
from zoom import *
import databaseconfig as dbconfig
import zoomconfig
import vcmconfig
from datetime import datetime
import pytz

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

def authenticate(token):
    # jwks = "https://go.fuqua.duke.edu/auth/jwks"
    # jwks_client = PyJWKClient(jwks)
    # signing_key = jwks_client.get_signing_key_from_jwt(token)
    public_key = b"-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsenb4+ybQKRQk75rCK9o\n8c9Yfd1NusBxnXeWPqL6mEoL8FOnJwC+emHxOh6G4sBFF3wADFq0tsZdm3k5E1nG\nrFe6Z6r0aYmFjXjBWNaOGACekQe0/m5wlKOn24c7QjiPxLb22vCSCHKM/P2meuf5\n0Gb4DfcXIFzmUoNYiEEbUyJ326meNeXQJBPq/UuZyBrwh4T7VmFGhCcfWOZ9i2Ho\ndldJHva5IzKjfF+VjPcNlAymbumjL7PlzOsjhTmOlyc9fEesINOuCctaNQUqE4nH\n6cPh7fO1CYlJMaxULzqvltazeHuCX4B14FM9/EJKdr677M5qFFqMPOuHQw3guzdd\nXwIDAQAB\n-----END PUBLIC KEY-----"
    data = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience="Shibboleth",
        options={"require": ["exp", "iss", "sub"]})
    return data


app = Flask(__name__)
# app.config['SECRET_KEY'] = 'NlcPJLmeyeXMn4KpISh0hGQ3cWQIQbbnE0WwfpeZxjiftirfP2sCNI0GA6P96kCP'  # used to secure sessions, which allow Flask to remember information from one request to another
app.secret_key = 'NlcPJLmeyeXMn4KpISh0hGQ3cWQIQbbnE0WwfpeZxjiftirfP2sCNI0GA6P96kCP'
# app.config['SESSION_TYPE'] = 'redis'
# Session(app)

@app.route('/')
def index():
    # authentication and determine permissions
    if not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('auth_redirect'))
    
    token = request.cookies.get('_FSB_SHIB')
    try:
        auth = authenticate(token)
        print(auth)
    except jwt.exceptions.DecodeError as e:
        print("Error decoding JWT "+token)
        return redirect(url_for('auth_redirect'))
    except jwt.exceptions.ExpiredSignatureError as e:
        return redirect(url_for('auth_redirect'))

    session['user'] = auth['cn']
    session['dukeid'] = auth['dukeid']
    session['email'] = auth['sub']
    if "staff@duke.edu" in auth['eduPersonScopedAffiliation'] or "faculty@duke.edu" in auth['eduPersonScopedAffiliation']:
        session['permission'] = True
    else:
        session['permission'] = False

    print(session.get('user'))
    print(session.get('permission'))

    conn = get_db_connection()
    cur = conn.cursor()

    # get recordings
    cur.execute("SELECT * FROM recordings WHERE visible=TRUE")
    recordings = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('index.html', recordings=recordings, selected_tag="")

@app.route('/auth_redirect')
def auth_redirect():
    auth_url = "https://go.fuqua.duke.edu/auth/shibboleth?service="+vcmconfig.VCM
    return redirect(auth_url, 302)


@app.route('/admin/activity')
def admin_activity():
    if not session.get('permission'):
        return redirect(url_for('index'))
    else:
        conn = get_db_connection()
        cur = conn.cursor()

        # get activity
        cur.execute("SELECT * FROM activity")
        activities = cur.fetchall()
        cur.close()
        conn.close()

        return render_template('admin_activity.html', activities=activities)


@app.route('/admin/hidden_recordings')
def admin_hidden_recordings():
    if not session.get('permission'):
        return redirect(url_for('index'))
    else:
        conn = get_db_connection()
        cur = conn.cursor()

        # get recordings
        cur.execute("SELECT * FROM recordings WHERE visible=FALSE")
        hiddenRecordings = cur.fetchall()
        cur.close()
        conn.close()

        return render_template('admin_activity.html', hiddenRecordings=hiddenRecordings)

@app.route('/card')
def card():
    conn = get_db_connection()
    cur = conn.cursor()

    # get recordings
    cur.execute("SELECT * FROM recordings WHERE visible=TRUE")
    recordings = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('card.html', recordings=recordings)


@app.route('/<string:recording_id>')
def recording(recording_id):
    recording = get_recording(recording_id)
    return render_template('recording.html', recording=recording)


@app.route('/<string:recording_id>/edit', methods=('GET', 'POST'))
def edit(recording_id):
    conn = get_db_connection()
    cur = conn.cursor()
    recording = get_recording(recording_id)
    originalTags = recording[9]

    if request.method == 'POST':
        cur_time = str(datetime.now(pytz.timezone('America/New_York')).strftime("%m/%d/%Y %H:%M:%S"))

        title = request.form['title']
        # add to activity log if title changed
        if title != recording[2]:
            cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes) VALUES (%s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Changed title", ""))
            conn.commit()

        summary = request.form['summary']
        # add to activity log if summary changed
        if summary != recording[7]:
            cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes) VALUES (%s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Changed summary", ""))
            conn.commit()

        transcription = request.form['transcription']
        # add to activity log if transcript changed
        if transcription != recording[6]:
            cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes) VALUES (%s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Changed transcript", ""))
            conn.commit()

        tags = request.form['tags'].split(',')

        # remove leading and trailing whitespaces
        for i in range(len(tags)):
            tags[i] = tags[i].strip()

        # deleting tags
        new_dict = {tag: value for (tag, value) in recording[9].items() if tag in tags}
        for tag in [x for x in recording[9] if x not in new_dict]:
            if tag!="":
                print("Deleted tag: "+tag+" end")
                # add to activity log if tag deleted
                cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes) VALUES (%s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Deleted tag", "Deleted tag: \""+tag+"\""))
                conn.commit()

        # adding new tags
        for tag in tags:
            if tag not in originalTags and tag!="":
                print("Added tag: "+ tag+ " end")
                new_dict[tag] = 0
                # add to activity log if tag added
                cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes) VALUES (%s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Added tag", "Added tag: \""+tag+"\""))
                conn.commit()

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE recordings SET topic = %s, summary = %s, text = %s, tags = %s where id = %s', (title, summary, transcription, json.dumps(new_dict), recording_id))
            cur.close()
            conn.commit()
            conn.close()
            return redirect(url_for('.recording', recording_id=recording_id))
    return render_template('edit.html', recording=recording, permission=session.get('permission'))


@app.route('/<string:recording_id>/hide', methods=('POST','GET'))
def hide(recording_id):
    conn = get_db_connection()
    cur = conn.cursor()
    recording = get_recording(recording_id)
    change_visibility(conn, cur, recording_id, session.get('user'), session.get('email'))
    conn.commit()
    cur.close()
    conn.close()
    flash('"{}" was successfully hidden!'.format(recording[2]))
    return redirect(url_for('index'))


@app.route('/<string:recording_id>/show', methods=('POST','GET'))
def show(recording_id):
    conn = get_db_connection()
    cur = conn.cursor()
    recording = get_recording(recording_id)
    change_visibility(conn, cur, recording_id, session.get('user'), session.get('email'), visible='TRUE')
    conn.commit()
    cur.close()
    conn.close()
    flash('"{}" was successfully shown!'.format(recording[2]))
    return redirect(url_for('index'))


@app.route('/tagFilter/<string:tag>')
def tagFilter(tag):
    conn = get_db_connection()
    cur = conn.cursor()

    # get recordings
    cur.execute('SELECT * FROM recordings WHERE tags::jsonb ? %s',(tag,))
    recordings = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', recordings=recordings, selected_tag=tag)


@app.route('/<string:id>/<string:tag>/upvote', methods=('POST','GET'))
def upvote_tag(id, tag):  
    conn = get_db_connection()
    cur = conn.cursor()
    vote_tags(conn, cur, id, tag, 1, session.get('user'), session.get('email'))
    cur.close()
    conn.close()

    recording = get_recording(id)
    return redirect(url_for('.recording', recording_id=id))
    

@app.route('/<string:id>/<string:tag>/downvote', methods=('POST','GET'))
def downvote_tag(id, tag):  
    conn = get_db_connection()
    cur = conn.cursor()
    vote_tags(conn, cur, id, tag, -1, session.get('user'), session.get('email'))
    cur.close()
    conn.close()

    recording = get_recording(id)
    return redirect(url_for('.recording', recording_id=id))

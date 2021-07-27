from flask import Flask, render_template, request, url_for, flash, redirect, session, make_response
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

def searchForKeyword(keyword, tag="", view="index"):
    if view == "index":
        file = 'index.html'
    else:
        file = 'card.html'
    if keyword == "":
        conn = get_db_connection()
        cur = conn.cursor()
        # get recordings
        if tag:
            cur.execute('SELECT * FROM recordings WHERE tags::jsonb ? %s ORDER BY unformat_time DESC',(tag,))
        else:
            cur.execute("SELECT * FROM recordings WHERE visible=TRUE ORDER BY unformat_time DESC")
        recordings = cur.fetchall()
        cur.close()
        conn.close()
        return render_template(file, recordings=recordings, selected_tag=tag, username=session.get('user'), permission=session.get('permission'))
    conn = get_db_connection()
    cur = conn.cursor()
    recordings = search(conn, cur, keyword)
    cur.close()
    conn.close()
    return render_template(file, recordings=recordings, selected_tag=tag, username=session.get('user'), permission=session.get('permission'))


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


@app.route('/', methods=('GET', 'POST'))
def index():
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))
    # if not request.cookies.get('_FSB_SHIB'):
    #     return redirect(url_for('auth_redirect'))
    # login()
    # token = request.cookies.get('_FSB_SHIB')
    # try:
    #     auth = authenticate(token)
    #     print(auth)
    # except jwt.exceptions.DecodeError as e:
    #     print("Error decoding JWT "+token)
    #     return redirect(url_for('auth_redirect'))
    # except jwt.exceptions.ExpiredSignatureError as e:
    #     return redirect(url_for('auth_redirect'))

    # session['user'] = auth['cn']
    # session['dukeid'] = auth['dukeid']
    # session['email'] = auth['sub']
    # if "staff@duke.edu" in auth['eduPersonScopedAffiliation'] or "faculty@duke.edu" in auth['eduPersonScopedAffiliation']:
    #     session['permission'] = True
    # else:
    #     session['permission'] = False

    # print(session.get('user'))
    # print(session.get('permission'))

    # search
    if request.method == 'POST':
        return searchForKeyword(request.form['keyword'])

    conn = get_db_connection()
    cur = conn.cursor()
    cur_sort_order = 'date_desc'

    # get recordings
    cur.execute("SELECT * FROM recordings WHERE visible=TRUE ORDER BY unformat_time DESC")
    recordings = cur.fetchall()
    # print(request.args['sort'])
    if request.args and request.args['sort']=='date_asc':
        # cur.execute("SELECT * FROM recordings WHERE visible=TRUE ORDER BY unformat_time ASC")
        # recordings = cur.fetchall()
        recordings.reverse()
        print("date asc")
        cur_sort_order = 'date_asc'
    elif request.args and request.args['sort']=='date_desc':
        # cur.execute("SELECT * FROM recordings WHERE visible=TRUE ORDER BY unformat_time DESC")
        # recordings = cur.fetchall()
        cur_sort_order = 'date_desc'
        print("date desc")
    cur.close()
    conn.close()

    return render_template('index.html', recordings=recordings, selected_tag="", username=session.get('user'), sort_order=cur_sort_order, permission=session.get('permission'))


@app.route('/auth_redirect')
def auth_redirect():
    auth_url = "https://go.fuqua.duke.edu/auth/shibboleth?service="+vcmconfig.VCM+"/login"
    return redirect(auth_url, 302)


@app.route('/login')
def login():
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
        print("Expired JWT")
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

    return redirect(url_for('index'))


@app.route('/admin/activity')
def admin_activity():
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

    if not session.get('permission'):
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()

    # get activity
    cur.execute("SELECT * FROM activity ORDER BY unformat_time DESC")
    activities = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin_activity.html', activities=activities, username=session.get('user'), permission=session.get('permission'))


@app.route('/admin/hidden_recordings')
def admin_hidden_recordings():
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

    if not session.get('permission'):
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()

    # get recordings
    cur.execute("SELECT * FROM recordings WHERE visible=FALSE ORDER BY unformat_time DESC")
    hiddenRecordings = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin_hidden.html', hiddenRecordings=hiddenRecordings, username=session.get('user'), permission=session.get('permission'))


@app.route('/card', methods=('GET', 'POST'))
def card():
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

    # search
    if request.method == 'POST':
        return searchForKeyword(keyword=request.form['keyword'], view="card")

    conn = get_db_connection()
    cur = conn.cursor()
    cur_sort_order = 'date_desc'

    # get recordings
    cur.execute("SELECT * FROM recordings WHERE visible=TRUE ORDER BY unformat_time DESC")
    recordings = cur.fetchall()
    if request.args and request.args['sort']=='date_asc':
        recordings.reverse()
        cur_sort_order = 'date_asc'
    elif request.args and not request.args['sort']=='date_desc':
        cur_sort_order = 'date_desc'
        print("date desc")
    
    cur.close()
    conn.close()

    return render_template('card.html', recordings=recordings, selected_tag="", username=session.get('user'), permission=session.get('permission'), sort_order=cur_sort_order)


@app.route('/<string:recording_id>', methods=('GET', 'POST'))
def recording(recording_id):
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE recordings SET summary_approved = NOT summary_approved WHERE id=%s', (recording_id,))
        conn.commit()
        cur.close()
        conn.close()

    recording = get_recording(recording_id)
    return render_template('recording.html', recording=recording, username=session.get('user'), permission=session.get('permission'))


@app.route('/<string:recording_id>/edit', methods=('GET', 'POST'))
def edit(recording_id):
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    recording = get_recording(recording_id)
    originalTags = recording[9]

    if request.method == 'POST':
        cur_time = str(datetime.now(pytz.timezone('America/New_York')).strftime("%b %d, %Y %I:%M %p"))

        title = request.form['title']
        # add to activity log if title changed
        if title != recording[2]:
            cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes, recording_title, unformat_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Changed title", "Changed title to \""+title+"\"", recording[2], datetime.now()))
            conn.commit()

        summary = request.form['summary']
        # add to activity log if summary changed
        if summary != recording[7]:
            cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes, recording_title, unformat_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Changed summary", "", recording[2], datetime.now()))
            conn.commit()

        vid_notes = request.form['notes'].splitlines()
        # add to activity log if notes changed
        if recording[12] and vid_notes != recording[12]:
            cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes, recording_title, unformat_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Changed video notes", "", recording[2], datetime.now()))
            conn.commit()

        # transcription = request.form['transcription']
        # # add to activity log if transcript changed
        # if transcription != recording[6]:
        #     cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes) VALUES (%s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Changed transcript", ""))
        #     conn.commit()

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
                cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes, recording_title, unformat_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Deleted tag", "Deleted tag: \""+tag+"\"", recording[2], datetime.now()))
                conn.commit()

        # adding new tags
        for tag in tags:
            if tag not in originalTags and tag!="":
                print("Added tag: "+ tag+ " end")
                new_dict[tag] = 0
                # add to activity log if tag added
                cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes, recording_title, unformat_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Added tag", "Added tag: \""+tag+"\"", recording[2], datetime.now()))
                conn.commit()

        yvidurl = request.form['yvidurl']
        vidurl = request.form['vidurl']
        new_vid = recording[4]
        if yvidurl:
            new_vid = yvidurl.replace("https://youtu.be/", "https://www.youtube.com/embed/")
        elif vidurl:
            new_vid = vidurl
        # add to activity log if video link changed
        if new_vid!=recording[4]:
            cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes, recording_title, unformat_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Changed video url", vidurl, recording[2], datetime.now()))
            conn.commit()

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE recordings SET topic = %s, summary = %s, tags = %s, video = %s, notes=%s where id = %s', (title, summary, json.dumps(new_dict), new_vid, vid_notes, recording_id))
            cur.close()
            conn.commit()
            conn.close()
            return redirect(url_for('.recording', recording_id=recording_id))
    return render_template('edit.html', recording=recording, permission=session.get('permission'), username=session.get('user'))

@app.route('/create', methods=('GET', 'POST'))
def create():
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

    if not session.get('permission'):
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        cur_time = str(datetime.now(pytz.timezone('America/New_York')).strftime("%b %d, %Y %I:%M %p"))

        title = request.form['title']
        summary = request.form['summary']
        transcription = request.form['transcription']
        vid_notes = request.form['notes'].splitlines()
        tags = {tag.strip(): 0 for tag in request.form['tags'].split(',')}

        recordingURL = request.form['recordingURL']
        if "https://youtu.be/" in recordingURL:
            recordingURL = recordingURL.replace("https://youtu.be/", "https://www.youtube.com/embed/")        

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("INSERT INTO recordings(topic, start_time, video, transcript, text, tags, summary, visible, unformat_time, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s)", (title, cur_time, recordingURL, "", transcription, json.dumps(tags), summary, cur_time, vid_notes))
            conn.commit()

            cur.execute("SELECT id FROM recordings WHERE topic=%s and start_time=%s", (title, cur_time))
            recording_id = cur.fetchone()[0]
            cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes, recording_title, unformat_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (cur_time, session.get('user'), session.get('email'), recording_id, "Created recording", "", title, datetime.now()))
            conn.commit()
            
            cur.close()
            conn.close()
            return redirect(url_for('index'))
    return render_template('create.html', permission=session.get('permission'), username=session.get('user'))


@app.route('/<string:recording_id>/hide', methods=('POST','GET'))
def hide(recording_id):
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

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
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    recording = get_recording(recording_id)
    change_visibility(conn, cur, recording_id, session.get('user'), session.get('email'), visible='TRUE')
    conn.commit()
    cur.close()
    conn.close()
    flash('"{}" was successfully shown!'.format(recording[2]))
    return redirect(url_for('index'))


@app.route('/index/<string:tag>', methods=('POST','GET'))
def indexTagFilter(tag):
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

    # search
    if request.method == 'POST':
        return searchForKeyword(request.form['keyword'], tag)
    conn = get_db_connection()
    cur = conn.cursor()

    # get recordings
    cur.execute('SELECT * FROM recordings WHERE tags::jsonb ? %s ORDER BY unformat_time DESC',(tag,))
    recordings = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', recordings=recordings, selected_tag=tag, username=session.get('user'), permission=session.get('permission'))


@app.route('/card/<string:tag>', methods=('GET', 'POST'))
def cardTagFilter(tag):
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        return searchForKeyword(keyword=request.form['keyword'], tag=tag, view="card")

    conn = get_db_connection()
    cur = conn.cursor()

    # get recordings
    cur.execute('SELECT * FROM recordings WHERE tags::jsonb ? %s ORDER BY unformat_time DESC',(tag,))
    recordings = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('card.html', recordings=recordings, selected_tag=tag, username=session.get('user'), permission=session.get('permission'))


@app.route('/<string:id>/<string:tag>/upvote', methods=('POST','GET'))
def upvote_tag(id, tag):  
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    vote_tags(conn, cur, id, tag, 1, session.get('user'), session.get('email'))
    cur.close()
    conn.close()

    recording = get_recording(id)
    return redirect(url_for('.recording', recording_id=id))
    

@app.route('/<string:id>/<string:tag>/downvote', methods=('POST','GET'))
def downvote_tag(id, tag):  
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    vote_tags(conn, cur, id, tag, -1, session.get('user'), session.get('email'))
    cur.close()
    conn.close()

    recording = get_recording(id)
    return redirect(url_for('.recording', recording_id=id))


@app.route('/logout')
def logout():
    # authentication and determine permissions
    if not session or not request.cookies.get('_FSB_SHIB'):
        return redirect(url_for('login'))
    
    resp = make_response(render_template('index.html'))
    resp.delete_cookie('_FSB_SHIB')
    resp.delete_cookie('session')
    session.clear()
    return redirect('https://shib.oit.duke.edu/cgi-bin/logout.pl')
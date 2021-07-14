# imports for zoom integration + database
import requests
import nltk
from nltk import tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
from nltk.tokenize import sent_tokenize
# nltk.download('stopwords')
# nltk.download('cosine_distance')
# nltk.download('punkt')
import numpy as np
import networkx as nx
import psycopg2
import databaseconfig as dbconfig
import zoomconfig
from datetime import date, datetime
from dateutil import tz
import pytz
from sklearn.feature_extraction.text import CountVectorizer
import json

name = "Test User1" # "testuser1.zoom@gmail.com"
# TOKEN stored in zoomconfig file (hidden by .gitignore)
stop_words = set(stopwords.words('english'))
now = datetime.now()

def get_users(conn, cur, headers):
    url = "https://api.zoom.us/v2/users"
    response = requests.get(url=url, headers=headers)
    json = response.json()

    for u in json["users"]:
        # add to database
        cur.execute("INSERT INTO users (name, id, email) VALUES (%s , %s, %s) ON CONFLICT (id) DO NOTHING", (u["first_name"]+" "+u["last_name"], u["id"], u["email"]))
        conn.commit()


def get_meetings(conn, cur, user, headers, start=None, end=None, num_sentences=1):
    # get meetings
    url = "https://api.zoom.us/v2/users/" + user + "/recordings"
    if start != None and end != None:
        url += "?from=" + start + "&to=" + end
    elif start != None:
        url += "?from=" + start
    elif end != None:
        url += "?to=" + end
    response = requests.request("GET", url, headers=headers)
    meetings_json = response.json()

    # get useful info
    for meeting in meetings_json["meetings"]:
        print("Processing meeting")
        cur.execute("SELECT EXISTS(SELECT zoom_id FROM recordings WHERE zoom_id=%s)", (meeting["uuid"],))
        
        # if recording already exists in database
        if cur.fetchone()[0]:
            continue

        # format date and start time    
        date = format_date(meeting["start_time"]) 

        transcript_link = ""
        for file in meeting["recording_files"]:
            # video link
            if file["file_type"] == "MP4":
                video_link = file["play_url"]
            # transcript download link
            elif file["file_type"] == "TRANSCRIPT":
                transcript_link = file["download_url"]
    
        # transcript text
        text = parse_transcripts(transcript_link)

        # create list of tokens for text search
        cur.execute("SELECT to_tsvector(%s)", (text,))
        tokens = cur.fetchone()[0]

        # calculate keywords for tags
        keywords = find_keywords(text)
        keywords_dict = {tag: 0 for tag in keywords}

        # generate summary
        summary = generate_summary(text, num_sentences)

        # add to database
        cur.execute("INSERT INTO recordings(topic, start_time, video, transcript, text, tokens, tags, summary, visible, zoom_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s) ON CONFLICT (zoom_id) DO NOTHING", (meeting["topic"], date, video_link, transcript_link, text, tokens, json.dumps(keywords_dict), summary, meeting["uuid"]))
        conn.commit()


def format_date(date_str):
    # time originally in UTC
    utc_time = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
    utc_time = utc_time.replace(tzinfo=tz.gettz('UTC'))

    # convert time zones and format
    # to_zone = tz.tzlocal() # convert to local time
    to_zone = tz.gettz('America/New_York') # convert to ET
    time = utc_time.astimezone(to_zone)
    return time.strftime("%b %d, %Y %I:%M %p")


def parse_transcripts(transcript_link):
    # get transcript text
    if transcript_link == "":
        return ""
    t_url = transcript_link+"?access_token="+zoomconfig.TOKEN
    t_response = requests.request("GET", t_url)

    # process transcripts to remove unnecessary info (time, speaker)
    lines = []
    for string in t_response.text.split(": ")[1:]:
        lines.append(string.split("\r")[0])
    return " ".join(lines)


# get keywords from transcript
dict_idf = {}
sentences = []
def find_keywords(text, num_tags=5):
    if text=="":
        return []
    words = text.split()
    word_len = len(words)
    sentences.extend(tokenize.sent_tokenize(text))
    sent_len = len(sentences)
    for word in words:
        word = word.replace('.','')
        if word not in stop_words:
            if word in dict_idf:
                final = [all([w in x for w in word]) for x in sentences] 
                dict_idf[word] = len([sentences[i] for i in range(0, len(final)) if final[i]])
            else:
                dict_idf[word] = 1
    vectorizer = CountVectorizer()
    tf = vectorizer.fit_transform([text.lower()]).toarray()
    tf = np.log(tf+1)
    tfidf = tf.copy()
    tags = np.array(vectorizer.get_feature_names())
    for k in dict_idf.keys():
        if k in tags:
            tfidf[:, tags==k] = tfidf[:, tags==k] * dict_idf[k]
    return list(tags[tfidf[0, :].argsort()[-1*num_tags:][::-1]])


# summarize
def sentence_similarity(sent1, sent2):

    sent1 = [w.lower() for w in sent1]
    sent2 = [w.lower() for w in sent2]

    all_words = list(set(sent1 + sent2))

    vector1 = [0] * len(all_words)
    vector2 = [0] * len(all_words)

    # build the vector for the first sentence
    for w in sent1:
        if w in stop_words:
            continue
        vector1[all_words.index(w)] += 1

    # build the vector for the second sentence
    for w in sent2:
        if w in stop_words:
            continue
        vector2[all_words.index(w)] += 1

    return 1 - cosine_distance(vector1, vector2)


def build_similarity_matrix(sentences):
    # Create an empty similarity matrix
    similarity_matrix = np.zeros((len(sentences), len(sentences)))

    for idx1 in range(len(sentences)):
        for idx2 in range(len(sentences)):
            if idx1 == idx2:  # ignore if both are same sentences
                continue
            similarity_matrix[idx1][idx2] = sentence_similarity(
                sentences[idx1], sentences[idx2])
    return similarity_matrix


def generate_summary(text, top_n=5):
    if text == "":
        return ""

    summarize_text = []

    # Read text and split it
    sentences = sent_tokenize(text)

    # Generate Similary Matrix across sentences
    sentence_similarity_martix = build_similarity_matrix(sentences)
    # Rank sentences in similarity matrix
    sentence_similarity_graph = nx.from_numpy_array(sentence_similarity_martix)
    scores = nx.pagerank(sentence_similarity_graph)

    # Sort the rank and pick top sentences
    ranked_sentence = sorted(
        ((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
    # print("Indexes of top ranked_sentence order are ", ranked_sentence)

    for i in range(top_n):
        summarize_text.append("".join(ranked_sentence[i][1]))

    # Output the summarize text
    summarized = " ".join(summarize_text)
    return summarized


def search(conn, cur, words):
    words = words.split()

    # search for phrase
    phrase = " <-> ".join(words)
    cur.execute("SELECT id FROM recordings WHERE tokens @@ to_tsquery(%s)", (phrase,)) 
    results = cur.fetchall()
    if len(results) > 0: # if results found
        return results

    # search for all words
    and_search = " & ".join(words)
    cur.execute("SELECT id FROM recordings WHERE tokens @@ to_tsquery(%s)", (and_search,)) 
    results = cur.fetchall()
    if len(results) > 0: # if results found
        return results

    # search for any word
    or_search = " | ".join(words)
    cur.execute("SELECT id FROM recordings WHERE tokens @@ to_tsquery(%s)", (or_search,)) 
    return cur.fetchall()


def change_visibility(conn, cur, meeting_id, user, email, visible='FALSE'):
    cur.execute("UPDATE recordings SET visible=%s WHERE id=%s", (visible, meeting_id))
    conn.commit()

    if visible == 'FALSE':
        cur_action = "Hid recording"
    else:
        cur_action = "Made recording visible"
    cur_time = str(datetime.now(pytz.timezone('America/New_York')).strftime("%m/%d/%Y %H:%M:%S"))

    # add to activity log
    cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes) VALUES (%s, %s, %s, %s, %s, %s)", (cur_time, user, email, meeting_id, cur_action, ""))
    conn.commit()
    

# upvote or downvote tags
def vote_tags(conn, cur, id, tag, vote, user, email):
    # vote should either be 1 for upvote or -1 for downvote
    cur.execute("SELECT tags FROM recordings WHERE id=%s", (id,))
    tags_dict = cur.fetchone()[0]
    tags_dict[tag] = tags_dict[tag] + vote
    tags_dict = dict(sorted(tags_dict.items(), key=lambda item: item[1]))
    print(json.dumps(tags_dict))
    cur.execute("UPDATE recordings SET tags=%s WHERE id=%s", (json.dumps(tags_dict), id))
    conn.commit()
    cur.execute("SELECT tags FROM recordings WHERE id=%s", (id,))
    print(cur.fetchone())

    if vote==1:
        vote_type = "upvote"
    else:
        vote_type = "downvote"
    cur_time = str(datetime.now(pytz.timezone('America/New_York')).strftime("%m/%d/%Y %H:%M:%S"))

    # add to activity log
    cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes) VALUES (%s, %s, %s, %s, %s, %s)", (cur_time, user, email, id, vote_type, "Tag modified: " + tag))
    conn.commit()


def main():
    print(stop_words)
    # add additional stopwords
    with open('stopwords.txt') as f:
        words = f.read().splitlines()
        for word in words:
            stop_words.add(word)

    # connect to database
    conn = psycopg2.connect("dbname={} user={} host='localhost' password={}".format(dbconfig.database["db"], dbconfig.database["user"], dbconfig.database["password"]))
    cur = conn.cursor()

    # get users
    headers = {
        'Authorization': "Bearer " + zoomconfig.TOKEN,
    }
    get_users(conn, cur, headers)

    # get user "test user 1"
    cur.execute("SELECT email FROM users WHERE name=%s", (name,))
    user = cur.fetchone()[0]
    print(user)
    print()

    today = date.today().strftime("%Y-%m-%d")
    start_date = "2021-06-01"
    # end_date = today
    end_date="2021-06-17"
    num_sentences = 3
        
    # get meetings and summarize transcripts
    get_meetings(conn, cur, user, headers, start_date, end_date, num_sentences)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
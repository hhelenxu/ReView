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
from sklearn.feature_extraction.text import CountVectorizer
import json

name = "Test User1" # "testuser1.zoom@gmail.com"
# TOKEN stored in zoomconfig file (hidden by .gitignore)
stop_words = set(stopwords.words('english'))

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
        cur.execute("SELECT EXISTS(SELECT zoom_id FROM recordings WHERE zoom_id=%s)", (meeting["uuid"],))
        # if recording already exists in database
        if cur.fetchone()[0]:
            continue

        # format date and start time    
        date = format_date(meeting["start_time"]) 

        transcript_link = ""
        for file in meeting["recording_files"]:
            if file["file_type"] == "MP4":
                video_link = file["play_url"]
            elif file["file_type"] == "TRANSCRIPT":
                transcript_link = file["download_url"]

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
def sentence_similarity(sent1, sent2, stopwords=None):
    if stopwords is None:
        stopwords = []

    sent1 = [w.lower() for w in sent1]
    sent2 = [w.lower() for w in sent2]

    all_words = list(set(sent1 + sent2))

    vector1 = [0] * len(all_words)
    vector2 = [0] * len(all_words)

    # build the vector for the first sentence
    for w in sent1:
        if w in stopwords:
            continue
        vector1[all_words.index(w)] += 1

    # build the vector for the second sentence
    for w in sent2:
        if w in stopwords:
            continue
        vector2[all_words.index(w)] += 1

    return 1 - cosine_distance(vector1, vector2)


def build_similarity_matrix(sentences, stop_words):
    # Create an empty similarity matrix
    similarity_matrix = np.zeros((len(sentences), len(sentences)))

    for idx1 in range(len(sentences)):
        for idx2 in range(len(sentences)):
            if idx1 == idx2:  # ignore if both are same sentences
                continue
            similarity_matrix[idx1][idx2] = sentence_similarity(
                sentences[idx1], sentences[idx2], stop_words)
    return similarity_matrix


def generate_summary(text, top_n=5):
    if text == "":
        return ""

    stop_words = stopwords.words('english')
    summarize_text = []

    # Read text and split it
    sentences = sent_tokenize(text)

    # Generate Similary Matrix across sentences
    sentence_similarity_martix = build_similarity_matrix(sentences, stop_words)

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


# def get_summaries(conn, cur, num_sentences=3):
#     cur.execute("SELECT * FROM recordings")
#     for recording in cur.fetchall():
#         # check if summary already exists in database
#         if recording[6] == None:
#             # add to recordings table in database
#             cur.execute("UPDATE recordings SET summary = %s where id = %s", (generate_summary(recording[5], num_sentences), recording[0]))
#             conn.commit()


def search(conn, cur, words):
    words = words.split()

    # search for phrase
    phrase = " <-> ".join(words)
    cur.execute("SELECT zoom_id FROM recordings WHERE tokens @@ to_tsquery(%s)", (phrase,)) 
    results = cur.fetchall()
    if len(results) > 0: # if results found
        return results

    # search for all words
    and_search = " & ".join(words)
    cur.execute("SELECT zoom_id FROM recordings WHERE tokens @@ to_tsquery(%s)", (and_search,)) 
    results = cur.fetchall()
    if len(results) > 0: # if results found
        return results

    # search for any word
    or_search = " | ".join(words)
    cur.execute("SELECT zoom_id FROM recordings WHERE tokens @@ to_tsquery(%s)", (or_search,)) 
    return cur.fetchall()


def change_visibility(conn, cur, meeting_id, visible='FALSE'):
    cur.execute("UPDATE recordings SET visible=%s WHERE zoom_id=%s", (visible, meeting_id))
    conn.commit()


def vote_tags(conn, cur, zoom_id, tag, vote):
    # vote should either be 1 for upvote or -1 for downvote
    cur.execute("SELECT tags FROM recordings WHERE zoom_id=%s", (zoom_id,))
    tags_dict = cur.fetchone()[0]
    tags_dict[tag] = tags_dict[tag] + vote
    cur.execute("UPDATE recordings SET tags=%s WHERE zoom_id=%s", (json.dumps(tags_dict), zoom_id))
    conn.commit()
     
text = """
now that we know how to complete the
Square, we can apply that a process to under to
better understand definiteness.
so if we complete the square for a
generic quadratic form, 
again that means we represent the
quadratic form with a real symmetric
matrix.
we find a spectral factorization and
write the quadratic form
as lambda times our change of variable
y1 squared
plus lambda 2 times our change of
variable y2 squared,
and then we keep going until we get to
our last eigenvalue
multiplied by yn squared.
the thing to point out here, is that
when we do this process, what we're doing
is we're taking a linear combination
of square terms. so if we if we care
about the sign of the quadratic form,
what we really care about are the signs
of the eigenvalues. here
so the eigenvalues of the symmetric
matrix representing the quadratic form
controls the definiteness of the
quadratic form.
explicitly what we're saying is that
being
positive definite is the same thing as
saying that the eigenvalues are all
positive numbers. being positive
semi-definite
is the same thing as saying that the
eigenvalues are all non-negative.
negative definite means the eigenvalues
are all strictly negative.
negative semi-definite means that the
eigenvalues are all non-positive,
and indefinite means there is at least
one positive eigenvalue,
and at least one negative eigenvalue.
so if you know the eigenvalues of the
symmetric matrix representing your
quadratic form
you immediately know the definiteness of
your quadratic form.
and the reason you know your
definiteness is because of the method of
completing the square.
so here's an example here we're looking
at the quadratic form
represented by this real symmetric
matrix.
s i bothered to find the eigenvalues
and i found that the eigenvalues of s
here are negative 2
negative 1 and what does that tell me
well the eigenvalues here are all
non-positive.
they're all not positive numbers um but
i do have zero on the list of
eigenvalues so they're not
strictly negative. so this tells me that
my quadratic form
is negative semi-definite but not
negative definite.
so if you know your eigenvalues you know
the definiteness of your quadratic form.
"""

print(generate_summary(text, 1))

# # connect to database
# conn = psycopg2.connect("dbname={} user={} password={}".format(dbconfig.database["db"], dbconfig.database["user"], dbconfig.database["password"]))
# cur = conn.cursor()

# # get users
# headers = {
#     'Authorization': "Bearer " + zoomconfig.TOKEN,
# }
# get_users(conn, cur, headers)

# # get user "test user 1"
# cur.execute("SELECT email FROM users WHERE name=%s", (name,))
# user = cur.fetchone()[0]
# print(user)
# print()

# start_date = "2021-06-01"
# end_date = "2021-06-17"
# num_sentences = 1
    
# # get meetings and summarize transcripts
# get_meetings(conn, cur, user, headers, start_date, end_date, num_sentences)
# # get_summaries(conn, cur, num_sentences)

# # cur.execute("SELECT * FROM recordings")
# # for recording in cur.fetchall():
# #     change_visibility(conn, cur, recording[0], 'FALSE')

# # print info
# cur.execute("SELECT * FROM recordings WHERE visible=TRUE")
# for recording in cur.fetchall():
#     print(recording[0]) # id
#     print(recording[1]) # visible (T/F)
#     print(recording[2]) # topic
#     print(recording[3]) # start time and date
#     print(recording[4]) # video link
#     # print(recording[5]) # transcript link
#     # print(recording[6]) # processed text of transcript
#     print(recording[7]) # summary
#     # print(recording[8]) # token
#     print(recording[9]) # tags
#     print(recording[10]) # meeting id
#     print()

# # search for phrase in transcript
# search_phrase = "zoom app"
# search_results = search(conn, cur, search_phrase)
# print('Search results for "{}":'.format(search_phrase))
# print(search_results)

# # upvote tag
# print()
# vote_tags(conn, cur, "qTVdsPJiRLSeIAPFachU/g==", "yeah", 1)
# cur.execute("SELECT tags FROM recordings WHERE zoom_id=%s", ("qTVdsPJiRLSeIAPFachU/g==",))
# print(cur.fetchall())

# cur.close()
# conn.close()
# imports for zoom integration + database
import requests
import nltk
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
from datetime import date
from rake_nltk import Rake

name = "Test User1" # "testuser1.zoom@gmail.com"
# TOKEN stored in zoomconfig file (hidden by .gitignore)

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
    json = response.json()

    # get useful info
    for meeting in json["meetings"]:
        print("Processing meeting")
        cur.execute("SELECT EXISTS(SELECT id FROM recordings WHERE id=%s)", (meeting["uuid"],))
        # if recording already exists in database
        if cur.fetchone()[0]:
            continue

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

        # generate summary
        summary = generate_summary(text, num_sentences)

        # add to database
        cur.execute("INSERT INTO recordings(id, topic, start_time, video, transcript, text, tokens, tags, summary) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING", (meeting["uuid"], meeting["topic"], meeting["start_time"], video_link, transcript_link, text, tokens, keywords, summary))
        conn.commit()


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


# get keywords using Rapid Automatic Keyword Extraction algorithm
def find_keywords(text):
    r = Rake(min_length=1, max_length=3)
    r.extract_keywords_from_text(text)
    return r.get_ranked_phrases()[:5]


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


def change_visibility(conn, cur, meeting_id, visible='FALSE'):
    cur.execute("UPDATE recordings SET visible=%s WHERE id=%s", (visible, meeting_id))
    conn.commit()


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

# today = date.today().strftime("%Y-%m-%d")
start_date = "2021-06-01"
# end_date = today
end_date = "2021-06-25"
num_sentences = 1
    
# get meetings and summarize transcripts
get_meetings(conn, cur, user, headers, start_date, end_date, num_sentences)
# get_summaries(conn, cur, num_sentences)


cur.close()
conn.close()
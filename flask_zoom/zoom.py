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
from datetime import date, datetime
import pytz
from dateutil import tz
from sklearn.feature_extraction.text import CountVectorizer
import json
import os

stop_words = set(stopwords.words('english'))

def get_meetings(conn, cur, start=None, end=None, num_sentences=1):
    os.chdir("../sample_transcripts")
    print(os.getcwd())
    day = 1
    available_files = ["definiteness.txt", "diagonalization.txt", "digraphs.txt", "linear_independence.txt", "Gauss_Jordan_Elimination.txt", "dimension_geometric_multiplicity.txt", "eigenvalues.txt", "eigenvalues_properties.txt", "linear_systems.txt", "null_spaces.txt"]
    video_links = {"definiteness.txt": "https://www.youtube.com/embed/6fD1aYzIubE", 
                   "diagonalization.txt": "https://www.youtube.com/embed/EgXxUKOcXSA", 
                   "digraphs.txt": "https://www.youtube.com/embed/ZNfBLl4HL9M",
                   "dimension_geometric_multiplicity.txt": "https://www.youtube.com/embed/XbckQx68kAA",
                   "eigenvalues_properties.txt": "https://www.youtube.com/embed/4axGfLRLRs8",
                   "eigenvalues.txt": "https://www.youtube.com/embed/m3p5-7lfi0Y",
                   "Gauss_Jordan_Elimination.txt": "https://www.youtube.com/embed/ZUYckj1zolc",
                   "linear_independence.txt": "https://www.youtube.com/embed/JQ2xpZWDtGs",
                   "linear_systems.txt": "https://www.youtube.com/embed/F2oN6GyG_rA",
                   "null_spaces.txt": "https://www.youtube.com/embed/rFy6xAe_l3w"
                }
    for file in os.listdir():
        id = file
        # print(str(file))
        if file.endswith(".txt") and str(file) in available_files:
            title = str(file)[:-4].replace("_", " ").title()
            print(title)
            date = "Jan " + str(day) + ", 2021 12:00 AM"
            day+=1
            # video_link = video_link_arr[0]
            with open(file, 'r') as f:
                text = f.read().replace("\n"," ")

            # create list of tokens for text search
            cur.execute("SELECT to_tsvector(%s)", (text,))
            tokens = cur.fetchone()[0]

            # calculate keywords for tags
            keywords = find_keywords(text)
            keywords_dict = {tag: 0 for tag in keywords}

            # generate summary
            # *** summary doesn't work if there are no periods in the transcript
            summary = generate_summary(text, 1)
            print(summary)

            # cur_time = str(datetime.now(pytz.timezone('America/New_York')).strftime("%b %d, %Y %I:%M %p"))

            # add to database
            cur.execute("INSERT INTO recordings(topic, start_time, video, transcript, text, tokens, tags, summary, visible, zoom_id, unformat_time, summary_approved, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, FALSE, %s) ON CONFLICT (zoom_id) DO NOTHING", (title, date, video_links[str(file)], "", text, tokens, json.dumps(keywords_dict), summary, id, date, []))
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
    cur.execute("SELECT * FROM recordings WHERE tokens @@ to_tsquery(%s)", (phrase,)) 
    results = cur.fetchall()
    if len(results) > 0: # if results found
        return results

    # search for all words
    and_search = " & ".join(words)
    cur.execute("SELECT * FROM recordings WHERE tokens @@ to_tsquery(%s)", (and_search,)) 
    results = cur.fetchall()
    if len(results) > 0: # if results found
        return results

    # search for any word
    or_search = " | ".join(words)
    cur.execute("SELECT * FROM recordings WHERE tokens @@ to_tsquery(%s)", (or_search,)) 
    return cur.fetchall()

def change_visibility(conn, cur, meeting_id, user, email, visible='FALSE'):
    cur.execute("UPDATE recordings SET visible=%s WHERE id=%s", (visible, meeting_id))
    conn.commit()
    
    cur.execute("SELECT topic FROM recordings WHERE id=%s", (meeting_id))
    title = cur.fetchone()[0]

    if visible == 'FALSE':
        cur_action = "Hid recording"
    else:
        cur_action = "Made recording visible"
    cur_time = str(datetime.now(pytz.timezone('America/New_York')).strftime("%b %d, %Y %I:%M %p"))

    # add to activity log
    cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes, recording_title, unformat_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (cur_time, user, email, meeting_id, cur_action, "", title, datetime.now()))
    conn.commit()


# upvote or downvote tags
def vote_tags(conn, cur, id, tag, vote, user, email):
    print(tag)
    print(id)
    # vote should either be 1 for upvote or -1 for downvote
    cur.execute("SELECT tags FROM recordings WHERE id=%s", (id,))
    tags_dict = cur.fetchone()[0]
    tags_dict[tag] = tags_dict[tag] + vote
    tags_dict = dict(sorted(tags_dict.items(), key=lambda item: item[1]))
    # print(json.dumps(tags_dict))
    cur.execute("UPDATE recordings SET tags=%s WHERE id=%s", (json.dumps(tags_dict), id))
    conn.commit()
    # cur.execute("SELECT tags FROM recordings WHERE id=%s", (id,))
    # print(cur.fetchone())

    cur.execute("SELECT topic FROM recordings WHERE id=%s", (id))
    title = cur.fetchone()[0]

    if vote==1:
        vote_type = "Upvote"
    else:
        vote_type = "Downvote"
    cur_time = str(datetime.now(pytz.timezone('America/New_York')).strftime("%b %d, %Y %I:%M %p"))

    # add to activity log
    cur.execute("INSERT INTO activity(time, name, email, recording_id, action, notes, recording_title, unformat_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (cur_time, user, email, id, vote_type, "Tag modified: \"" + tag+"\"", title, datetime.now()))
    conn.commit()



def main():
    # print(stop_words)
    # add additional stopwords
    with open('stopwords.txt') as f:
        words = f.read().splitlines()
        for word in words:
            stop_words.add(word)

    # connect to database
    conn = psycopg2.connect("dbname={} user={} host='localhost' password={}".format(dbconfig.database["db"], dbconfig.database["user"], dbconfig.database["password"]))
    cur = conn.cursor()
    get_meetings(conn, cur)
    cur.close()
    conn.close()
    

if __name__ == "__main__":
    main()

import requests
import nltk
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
from nltk.tokenize import sent_tokenize
import numpy as np
import networkx as nx

USER = "testuser1.zoom@gmail.com"
TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6ImRfNi1wakk3UzE2XzR4UnFmX2tUMkEiLCJleHAiOjE2MjQzNjk2MTMsImlhdCI6MTYyNDI4MzIxM30.c5spgu0dRhfITlGVOfyDxPKAoi5WD9RL0imczo8UQuo"

def get_meetings(url, headers, start = None, end = None):
    # get meetings
    if start != None and end != None:
        url += "?from=" + start + "&to=" + end
    elif start != None:
        url += "?from=" + start
    elif end != None:
        url += "?to=" + end
    response = requests.request("GET", url, headers=headers)
    json = response.json()

    # get video links and transcripts
    videos = {}
    transcripts = {}
    for meeting in json["meetings"]:
        for file in meeting["recording_files"]:
            if file["file_type"] == "MP4":
                videos[meeting["uuid"]] = file["play_url"]
            elif file["file_type"] == "TRANSCRIPT":
                transcripts[meeting["uuid"]] = file["download_url"]
    return videos, transcripts

def parse_transcripts(transcripts):
    text = {}
    print(type(transcripts))
    for key, value in transcripts.items():
        # get transcript text
        t_url = value+"?access_token="+TOKEN
        t_response = requests.request("GET", t_url)

        # process transcripts to remove unnecessary info (time, speaker)
        lines = []
        for string in t_response.text.split(": ")[1:]:
            lines.append(string.split("\r")[0])
        text[key] = " ".join(lines)
    return text

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
            if idx1 == idx2: #ignore if both are same sentences
                continue 
            similarity_matrix[idx1][idx2] = sentence_similarity(sentences[idx1], sentences[idx2], stop_words)

    return similarity_matrix

def generate_summary(text, top_n=5):
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
    ranked_sentence = sorted(((scores[i],s) for i,s in enumerate(sentences)), reverse=True)    
    # print("Indexes of top ranked_sentence order are ", ranked_sentence)    

    for i in range(top_n):
        summarize_text.append("".join(ranked_sentence[i][1]))

    # Output the summarize text
    summarized = ". ".join(summarize_text)
    return summarized

def get_summaries(text, num_sentences = 3):
    summaries = {}
    for key, value in text.items():
        summaries[key] = generate_summary(value, num_sentences)
    return summaries


url = "https://api.zoom.us/v2/users/" + USER + "/recordings"
headers = {
    'Authorization': "Bearer " + TOKEN,
    'content-type': "application/json"
}
start_date = "2021-06-01"
end_date = "2021-06-20"
videos, transcripts = get_meetings(url, headers, start_date, end_date)
text = parse_transcripts(transcripts)
summaries = get_summaries(text, 2)
print(summaries)
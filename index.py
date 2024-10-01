# -*- coding: utf-8 -*-
"""
@author: Shujjat Ali
This is a single-file Flask application serving as the main processor for this project.
It reads PDF files, processes the content, and populates an index for future access.

"""
# Importing necessary libraries
from datetime import datetime
import copy
from flask import Flask, request
import sys
import os
import pymysql
import pandas as pd
import PyPDF2
import json
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import tokenize
from operator import itemgetter
import math

# Downloading necessary datasets
nltk.download('punkt')
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

app = Flask(__name__)  # Flask Initializer


@app.route('/')  # Index route
def index():
    """
    Main route to process the PDF file specified by report_id.
    It connects to the database, retrieves the PDF file, processes its content,
    and updates the database with the processed text and associated scores.
    """
    entry_id = request.args.get('report_id')

    # Connecting to the Database
    print('Connecting to the database...')
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        passwd='',
        db='library_access_system',
        charset='utf8mb4'
    )
    mycursor = conn.cursor()

    # Location of source files
    path = f"D:/wamp/www/library_access_system/files/{entry_id}.pdf"

    # Reading the PDF file
    print(f"+++++++++ Reading file from {path} +++++++++")
    source_doc = ''
    try:
        with open(path, 'rb') as pdfFileObj:
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            total_pages = pdfReader.numPages
            for x in range(total_pages):
                pageObj = pdfReader.getPage(x)
                source_doc += pageObj.extractText()
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return f"Error reading PDF file: {e}"

    # Clean and prepare the document for processing
    print('++++++++++ The Document ++++++++++')
    print(source_doc)
    print('++++++++++ The Document End ++++++++++')

    # Update the database with the OCR output
    print('++++++++++ Updating database for OCR ++++++++++')
    query = f"UPDATE books_and_reports SET ocr_output='{source_doc}' WHERE id='{entry_id}'"
    mycursor.execute(query)
    conn.commit()

    # Removing noise from the document
    source_doc = source_doc.replace("\n", "").strip()
    punctuations = '''!()-[]{};:'"\<>/?@#$%^&*_~'''
    source_doc = ''.join(char for char in source_doc if char not in punctuations)

    # Processing the text for term frequency (TF) scoring
    total_words = source_doc.split()
    total_word_length = len(total_words)
    tf_score = {}

    print('++++++++++ Processing the TF score ++++++++++')
    for each_word in total_words:
        each_word = each_word.replace('.', '')
        if each_word.lower() not in stop_words and len(each_word) >= 3 and not each_word.isnumeric():
            tf_score[each_word] = tf_score.get(each_word, 0) + 1

    try:
        # Normalize TF scores
        tf_score.update((x, y / total_word_length) for x, y in tf_score.items())
    except Exception as exception:
        query = f"UPDATE books_and_reports SET error='error in tf_score: {exception}' WHERE id='{entry_id}'"
        mycursor.execute(query)
        conn.commit()
        print('Error during TF score update:', exception)

    print('++++++++++ TF score processing complete ++++++++++')

    # Processing the inverse document frequency (IDF) scoring
    print('++++++++++ Processing the IDF score ++++++++++')
    idf_score = {}
    for each_word in total_words:
        each_word = each_word.replace('.', '')
        if each_word.lower() not in stop_words and len(each_word) >= 3 and not each_word.isnumeric():
            idf_score[each_word] = check_sent(each_word, total_sentences)

    # Filter out empty or unwanted IDF scores
    idf_score = {x: y for x, y in idf_score.items() if y > 0}

    try:
        # Calculate IDF scores
        idf_score.update((x, math.log(total_sent_len / y)) for x, y in idf_score.items())
    except Exception as exception:
        query = f"UPDATE books_and_reports SET error='error in idf_score: {exception}' WHERE id='{entry_id}'"
        mycursor.execute(query)
        conn.commit()

    # Calculate TF-IDF scores
    tf_idf_score = {key: tf_score[key] * idf_score.get(key, 0) for key in tf_score.keys()}

    # Update TF-IDF scores in the database
    print('++++++++++ Updating TF-IDF scores in database ++++++++++')
    score_in_text = json.dumps(tf_idf_score).replace("'", " ")
    query = f"UPDATE books_and_reports SET tags_score='{score_in_text}' WHERE id='{entry_id}'"
    mycursor.execute(query)
    conn.commit()

    # Fetching top tags
    print('++++++++++ Processing top tags ++++++++++')
    top_tags = get_top_n(tf_idf_score, 40)
    top_tags_json = json.dumps(top_tags).replace("'", " ")
    print('++++++++++ Updating top tags in database ++++++++++')
    query = f"UPDATE books_and_reports SET top_tags='{top_tags_json}' WHERE id='{entry_id}'"
    mycursor.execute(query)
    conn.commit()

    # Giving success message
    response = "File processed successfully."
    print(response)
    return response


def check_sent(word, sentences):
    """
    Count the number of sentences containing the specified word.
    """
    final = [all([w in x for w in word]) for x in sentences]
    return int(sum(final))


def get_top_n(dict_elem, n):
    """
    Get the top n items from a dictionary based on values.
    """
    return dict(sorted(dict_elem.items(), key=itemgetter(1), reverse=True)[:n])


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=40)  # Running the Flask application

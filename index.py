# -*- coding: utf-8 -*-
"""
@author: Shujjat Ali
This is single file flask applocaion. It is used as main processor for this project. It reads the PDF, processes it, 
and populates the index for future accesses. 

"""
#Importing necessary libraries
from datetime import datetime
import copy
from flask import Flask
from flask import request
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
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
#downloading necessary datasets 
nltk.download('punkt')
stop_words=nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

app = Flask(__name__) #Flask Initializer



@app.route('/') #index function
def index():
    # The web UI reads the PDF files folder and lists them. From DB, it get next ID to use and sends it this flask application to start working
    #on the files.
    entry_id = request.args.get('report_id')
    
    #Initiating DB Connect
    print('Connecting to the DB')
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        passwd='',
        db='library_access_system',
        charset='utf8mb4')
    
    
    mycursor = conn.cursor()
    
    
    #Location of source Files
    path="D:/wamp/www/library_access_system/files/"+str(entry_id)+".pdf"
    # Reading the files 
    print("+++++++++Reading file from"+str(path)+'+++++++++'
    print('Reading the  OCR from PDF')
    source_doc=''
    pdfFileObj = open(path, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    total_pages=pdfReader.numPages
    for x in range(total_pages):
        pageObj = pdfReader.getPage(x)
        source_doc=source_doc+(pageObj.extractText())  
    pdfFileObj.close()
    #Close the file after reading
    
    #Some information for better processing 
    total_sentences = tokenize.sent_tokenize(source_doc)
    total_sent_len = len(total_sentences)
    #print('total_sent_len: '+str(total_sent_len))
    
    
    #Processing the Text
    source_doc=source_doc.replace("'"," ") #Some cleansing
    #Print the source doc on console
    print('++++++++++ The Document+++++++++++++++++')
    print(source_doc)
    print('++++++++++ The Document End+++++++++++++++++')
    
    #Send complete doc to the DB
    print('++++++++++ updating DB for OCR+++++++++++++++++')
    query="UPDATE books_and_reports SET ocr_output=\'"+source_doc+"\'  WHERE id='"+str(entry_id)+"'"
    
    mycursor.execute(query)
    conn.commit()
    
    #Now processing the document
    
    #Removing noise from the doc
    source_doc=source_doc.strip()
    source_doc=source_doc.replace('\n','')
    punctuations = '''!()-[]{};:'"\<>/?@#$%^&*_~'''
    
    
    no_punct = ""
    for char in source_doc:
        if char not in punctuations:
            no_punct = no_punct + char
    source_doc=no_punct 
    
    #Processing the data for text score
    total_words = source_doc.split()
    total_word_length = len(total_words)
    
    
    
    tf_score = {}
    print('++++++++++ Processing the tf score+++++++++++++++++')
   
    for each_word in total_words:
        each_word = each_word.replace('.','')
        if not ((each_word.lower()  in stop_words ) or len(each_word)<3 or each_word.isnumeric()):
            if each_word in tf_score:
                tf_score[each_word] += 1
                #print(str(tf_score[each_word]))
            else:
                tf_score[each_word] = 1
                #print(str(tf_score[each_word]))
    
    print('++++++++++ Processing tf score Update+++++++++++++++++')
    try:
        tf_score.update((x, y/int(total_word_length)) for x, y in tf_score.items())
    
    except Exception as exception:
        query="UPDATE books_and_reports SET error=\'error in tf_score:"+exception+"\'  WHERE id='"+str(entry_id)+"'"
        print(query)
        print('++++++++++ updating DB for OCR End+++++++++++++++++')
        mycursor.execute(query)
        conn.commit()    
        
    print('++++++++++ Processing tf scores End+++++++++++++++++')
    
    print('++++++++++ Processing the idf score+++++++++++++++++')
    
    
    count=0
    idf_score = {}
    for each_word in total_words:
        each_word = each_word.replace('.','')
        if not ((each_word.lower()  in stop_words ) or len(each_word)<3 or each_word.isnumeric()):
            if each_word in idf_score:
                idf_score[each_word] = check_sent(each_word, total_sentences)
            else:
                idf_score[each_word] = 1
        count=count+1
    #Display idf score contents
    print("+++++++++++++++++++++(idf_score.items())+++++++++++++++++++++")
    #print(str(idf_score.items()))
    idf_score_copy = copy.copy(idf_score)
    for x in idf_score_copy.keys():
        if x == "model":
            del idf_score["model"]
    try:
        for x, y in idf_score.items():  
            if y == 0:
                print(str(x)+"==>"+str(y))  
                del idf_score[x]
    except: 
        print("Excepting")        
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++') 
    #Updating DB Index
    print('++++++++++ Processing idf score Update+++++++++++++++++') 
    
    try:
        idf_score.update((x, math.log(int(total_sent_len)/y)) for x, y in idf_score.items())
    except Exception as exception:
        query="UPDATE books_and_reports SET error=\'error in idf_score:"+exception+"\'  WHERE id='"+str(entry_id)+"'"
        print(query)
        print('++++++++++ updating DB for OCR End+++++++++++++++++')
        mycursor.execute(query)
        conn.commit()    
    tf_idf_score = {key: tf_score[key] * idf_score.get(key, 0) for key in tf_score.keys()}
    print('++++++++++ Processing the idf score end+++++++++++++++++')
    
    score_in_text = json.dumps(tf_idf_score).replace("'"," ")
    print('++++++++++ Udpating tf idf in DB+++++++++++++++++')
    query="Update books_and_reports set tags_score=\'"+score_in_text+"\'  where id='"+str(entry_id)+"'"
    mycursor.execute(query)
    conn.commit()
    # Fetching top tags (40 in number)
    print('++++++++++ Processing top tags+++++++++++++++++')
    top_tags=get_top_n(tf_idf_score, 40)
    print('++++++++++ Top Tags+++++++++++++++++')
    print(top_tags)
    top_tags=json.dumps(top_tags).replace("'"," ")
    print('++++++++++ Updating top tags in db+++++++++++++++++')
    query="Update books_and_reports set top_tags=\'"+top_tags+"\'  where id='"+str(entry_id)+"'"
    mycursor.execute(query)
    conn.commit()
    #Giving success message
    response=("File Processed")
    print(response)
    return response
def check_sent(word, sentences): 
    final = [all([w in x for w in word]) for x in sentences] 
    sent_len = [sentences[i] for i in range(0, len(final)) if final[i]]
    return int(len(sent_len))
def get_top_n(dict_elem, n):
    result = dict(sorted(dict_elem.items(), key = itemgetter(1), reverse = True)[:n]) 
    return result
app.run(host='127.0.0.1', port=40)
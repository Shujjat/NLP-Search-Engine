# PDF Processing Flask Application

## Introduction
This is a single-file Flask application designed to process PDF documents. The application reads a specified PDF file, extracts text using Optical Character Recognition (OCR), and populates a database with the processed information. It also calculates term frequency (TF) and inverse document frequency (IDF) scores for the words in the document, allowing for advanced text analysis and tagging.

## Code Explanation
The application consists of several key components:

- **Flask Setup**: The app is initialized with Flask and configured to run on a local server.
  
- **Database Connection**: The application connects to a MySQL database using `pymysql`, which is used to store and retrieve information about the processed PDFs.

- **PDF Reading and Text Extraction**: The app reads the PDF file specified by the `report_id` passed in the request, extracts the text using the `PyPDF2` library, and performs some basic text cleansing.

- **Text Processing**:
  - **Term Frequency (TF)**: The application calculates the frequency of each word in the document after removing punctuation and stop words.
  - **Inverse Document Frequency (IDF)**: It calculates how important a word is by determining how often it appears across sentences in the document.
  - **TF-IDF Score Calculation**: The TF and IDF scores are combined to produce a TF-IDF score for each word, which is then saved to the database.

- **Top Tags Extraction**: The application retrieves the top N tags based on the TF-IDF scores and updates the database accordingly.

## Installation

To run this application, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone (https://github.com/Shujjat/NLP-Search-Engine.git)
   cd NLP-Search-Engine
2. Install requirements
   pip install -r requirements.txt
3. Run app
   python index.py

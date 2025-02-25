#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import bs4
from bs4 import BeautifulSoup
import csv
import requests
import os
import glob
import re
import warnings
warnings.filterwarnings('ignore')

print('pandas version: {}'.format(pd.__version__))
print('bs4 version: {}'.format(bs4.__version__))
print('requests version: {}'.format(requests.__version__))
print('csv version: {}'.format(csv.__version__))

## Data Extraction
df=pd.read_excel('Input.xlsx')

titles = []
content = []
for i in range(len(df)):    
    url = df['URL'][i]
    response = requests.get(url)
#     print(response.status_code)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string
    titles.append(title[:-23])
    scraped_content = soup.find_all('div',class_="td-post-content tagdiv-type")
    for x in scraped_content:
        x = x.get_text(separator = " ").replace('\n',' ').replace('\xa0',' ').strip()
    content.append(x)

data = pd.DataFrame()
data['Title'] = titles
data['Content'] = content
data.head()

result = pd.concat([df, data], axis=1)
# result

folder_name = "articles"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)
for index, row in result.iterrows():
    url_id = row['URL_ID']  
    title = row['Title']
    content = row['Content']  

    # Generate the file name based on URL_ID
    file_name = f"{url_id}.txt"
    file_path = os.path.join(folder_name, file_name)

    # Write the article text to the text file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(title)
        file.write("\n")
        file.write(content)

## Data Analysis
def extract_words_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]
    
words = []
# Use glob to find all .txt files recursively in the root_directory
for file_path in glob.glob(os.path.join("StopWords\\StopWords", '**', '*.txt'), recursive=True):
    words_in_file = extract_words_from_file(file_path)
    words.extend(words_in_file)

stop_words = []
for word in words:
    if '|' in word:
        stop_words.extend([w.strip() for w in word.split('|')])  # Split and strip spaces
    else:
        stop_words.append(word)

with open("MasterDictionary\\MasterDictionary\\positive-words.txt", 'r') as file:
    positive_words = [line.strip() for line in file]
    
with open("MasterDictionary\\MasterDictionary\\negative-words.txt", 'r') as file:
    negative_words = [line.strip() for line in file]

def read_text_file(file_name):
    file_path = os.path.join("articles", file_name + ".txt")
    try:
        with open(file_path, 'r', encoding="utf8") as file:
            return file.read()
    except FileNotFoundError:
        return f"{file_name}.txt not found."

def count_syllables(word):
    word = word.lower()
    syllable_pattern = re.compile(r'[aeiouy]+')
    syllables = syllable_pattern.findall(word)
    if word.endswith("es") or word.endswith("ed"):
        if len(syllables) > 1:
            syllables = syllables[:-1]
    
    if word.endswith('e') and len(syllables) > 1:
        syllables = syllables[:-1]
    return max(1, len(syllables))  # Ensure at least 1 syllable

# Function to calculate the number of complex words and syllables per word
def analyze_text(text):
    words = re.findall(r'\b\w+\b', text)
    complex_word_count = 0
    syllable_count_per_word = {}
    total_syllables = 0
    # Analyze each word
    for word in words:
        syllable_count = count_syllables(word)
        syllable_count_per_word[word] = syllable_count
        total_syllables += syllable_count
        if syllable_count > 2:
            complex_word_count += 1
    return complex_word_count, syllable_count_per_word, total_syllables

def file_operation(file_name):
    file_path = os.path.join("articles", file_name + ".txt")  # Add .txt extension
    try:
        with open(file_path, 'r', encoding="utf8") as file:
            text = file.read()
            text_len = len(text)

            words = text.split()
            filtered_words = [word for word in words if word not in stop_words]
            filtered_text = " ".join(filtered_words)
            total_words = len(filtered_text)

            positive = []
            negative = []
            sentence_count = 0
            no_pronoun = 0
            punctuation = [".","!","?"]
            personal_pronouns = [ "I","my","you","he","she","it","we","they","them","us","him","her","his","hers","its","theirs","ours","our","your"]
            words = filtered_text.split()
            for word in words:
                word = word.lower()
                if word in positive_words:
                    positive.append(word)
                elif word in negative_words:
                    negative.append(word)
                if word[-1] in punctuation:
                    sentence_count +=1
                sentence_count = max(1, sentence_count)
                if word in personal_pronouns:        
                    no_pronoun += 1
                total_characters = sum(len(word) for word in words)

            complex_word_count, syllable_count_per_word, total_syllables = analyze_text(text)

            #CALCULATIONS
            positive_score = len(positive)
            negative_score = len(negative)
            polarity_score = (positive_score - negative_score)/ ((positive_score + negative_score) + 0.000001)
            subjectivity_score = (positive_score + negative_score)/ ((total_words) + 0.000001)
            avg_sentence_len = text_len/ sentence_count
            complex_words_percentage = complex_word_count/text_len
            Fog_Index = 0.4 * (avg_sentence_len + complex_words_percentage)
            Average_Number_of_Words_Per_Sentence = avg_sentence_len
            average_word_len = total_characters/ total_words

            return positive_score, negative_score, polarity_score, subjectivity_score, avg_sentence_len, complex_words_percentage, Fog_Index, Average_Number_of_Words_Per_Sentence, complex_word_count, text_len, total_syllables, no_pronoun, average_word_len

    except FileNotFoundError:
        return None, None, None, None, None, None, None, None, None, None, None, None, None

df1 = df
df1['POSITIVE SCORE'] = ''
df1['NEGATIVE SCORE'] = ''
df1['POLARITY SCORE'] = ''
df1['SUBJECTIVITY SCORE'] = ''
df1['AVG SENTENCE LENGTH'] = ''
df1['PERCENTAGE OF COMPLEX WORDS'] = ''
df1['FOG INDEX'] = ''
df1['AVG NUMBER OF WORDS PER SENTENCE'] = ''
df1['COMPLEX WORD COUNT'] = ''
df1['WORD COUNT'] = ''
df1['SYLLABLE PER WORD'] = ''
df1['PERSONAL PRONOUNS'] = ''
df1['AVG WORD LENGTH'] = ''

df1['POSITIVE SCORE'], df1['NEGATIVE SCORE'], df1['POLARITY SCORE'], df1['SUBJECTIVITY SCORE'], df1['AVG SENTENCE LENGTH'], df1['PERCENTAGE OF COMPLEX WORDS'], df1['FOG INDEX'], df1['AVG NUMBER OF WORDS PER SENTENCE'], df1['COMPLEX WORD COUNT'], df1['WORD COUNT'], df1['SYLLABLE PER WORD'], df1['PERSONAL PRONOUNS'], df1['AVG WORD LENGTH'] = zip(*df1['URL_ID'].apply(file_operation))
# print(df1)

df1.to_excel("output.xlsx")
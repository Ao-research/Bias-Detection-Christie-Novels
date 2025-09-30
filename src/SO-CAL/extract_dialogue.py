import spacy
import os
import re

nlp = spacy.load('en_core_web_sm')
nlp.max_length = 2000000

def read_document(file_path):
    with open(file_path, 'r', encoding='utf-8') as infile:
        return infile.read()

def extract_sentences_with_characters(text):
    doc = nlp(text)
    character_names = set(ent.text for ent in doc.ents if ent.label_ == "PERSON")
    character_sentences = {name: [] for name in character_names}

    for sent in doc.sents:
        for ent in sent.ents:
            if ent.label_ == "PERSON" and ent.text in character_names:
                character_sentences[ent.text].append(sent.text)
                break

    return character_sentences

def sanitize_filename(name):
    return re.sub(r'[^A-Za-z0-9 _]+', '', name)

def write_sentences(character_sentences, index):
    output_dir = 'output_sentences'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for character, sentences in character_sentences.items():
        sanitized_character = sanitize_filename(character)
        file_name = f'{output_dir}/{index}_{sanitized_character}.txt'
        with open(file_name, 'a', encoding='utf-8') as file:
            for sentence in sentences:
                file.write(sentence + '\n')

def process_documents(start_index, end_index):
    for index in range(start_index, end_index + 1):
        file_path = f'/Users/denggeyileao/Desktop/new/21-36/{index}.txt'
        content = read_document(file_path)
        character_sentences = extract_sentences_with_characters(content)
        write_sentences(character_sentences, index)

# Processing documents from 21 to 36
process_documents(21, 36)

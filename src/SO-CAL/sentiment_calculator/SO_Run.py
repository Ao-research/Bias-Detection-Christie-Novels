#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import csv
from collections import OrderedDict
import argparse

def get_command_arguments():
    '''
    Read command line input and set values to arguments.
    :return: a list of arguments
    '''
    parser = argparse.ArgumentParser(description='SFU Sentiment Calculator')
    parser.add_argument('--input', '-i', type=str, dest='input', action='store',
                        default='../Sample/output/Preprocessed_Output/BOOKS/no1.txt',
                        help="The input file or folder, and the file should be SO_CAL preprocessed text")

    parser.add_argument('--output', '-o', type=str, dest='output', action='store',
                        default='',
                        help="The output folder")

    parser.add_argument('--config', '-c', type=str, dest='config', action='store',
                        default='../Resources/config_files/en_SO_Calc.ini',
                        help="The configuration file for SO-CAL")

    parser.add_argument('--cutoff', '-cf', type=float, dest='cutoff', action='store',
                        default=0.0,
                        help="The cutoff value")

    parser.add_argument('--gold', '-g', type=str, dest='gold', action='store',
                        default='',
                        help="The gold file for comparison")

    args = parser.parse_args()
    return args

def create_gold_file(input_path):
    # Implement the function to create gold file
    return ""

def read_gold_file(gold_file):
    # Implement the function to read gold file
    return {}

def generate_file_sentiment(basicout_path, cutoff, file_sentiment_path):
    sentiments = []
    with open(basicout_path, 'r') as infile:
        current_file = ""
        for line in infile:
            if line.startswith("Processed"):
                current_file = line.split("Processed ")[1].strip().split('/')[-1]
            elif line.startswith("Text length"):
                text_length = int(line.split(": ")[1])
                # Example sentiment calculation based on text length (for demonstration)
                sentiment_score = text_length % 100  # Example score calculation
                sentiment = "positive" if sentiment_score >= cutoff else "negative"
                sentiments.append((current_file, sentiment_score, sentiment))
    
    with open(file_sentiment_path, 'w', newline='') as csvfile:
        fieldnames = ['File_Name', 'Sentiment_Score', 'Sentiment']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for filename, score, sentiment in sentiments:
            writer.writerow({'File_Name': filename, 'Sentiment_Score': score, 'Sentiment': sentiment})
            print(f"Wrote sentiment for {filename}: score={score}, sentiment={sentiment}")

def generate_richoutJSON(richout_path, richout_json):
    # Implement the function to generate rich output JSON
    pass

def main():
    pos_mark = "positive"
    neg_mark = "negative"

    args = get_command_arguments()
    input_path = args.input
    output_folder = args.output
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    config_file = args.config
    cutoff = args.cutoff
    gold_file = args.gold
    if gold_file == "":
        gold_file = create_gold_file(input_path)

    basicout_path = os.path.abspath(output_folder) + "/output.txt"
    richout_path = os.path.abspath(output_folder) + "/richout.txt"
    file_sentiment_path = os.path.abspath(output_folder) + "/file_sentiment.csv"
    prediction_accuracy_path =  os.path.abspath(output_folder) + "/prediction_accuracy.txt"
    richout_json = os.path.abspath(output_folder) + "/rich_output.json"

    open(basicout_path, "w").close()
    open(richout_path, "w").close()
    open(file_sentiment_path, 'w').close()
    open(prediction_accuracy_path, 'w').close()

    if os.path.isfile(input_path):  # 1 single file
        print("Processing " + "...")
        cmd = f"python3 sentiment_calculator/SO_Calc.py -i \"{input_path}\" -bo \"{basicout_path}\" -ro \"{richout_path}\" -c \"{config_file}\""
        os.system(cmd)
    elif os.path.isdir(input_path):   # an input folder, only reads files
        for f_name in os.listdir(input_path):
            print("Processing " + f_name + "...")
            file_path = os.path.abspath(input_path) + "/" + f_name
            if not os.path.isfile(file_path): continue
            cmd = f"python3 sentiment_calculator/SO_Calc.py -i \"{file_path}\" -bo \"{basicout_path}\" -ro \"{richout_path}\" -c \"{config_file}\""

            os.system(cmd)

    generate_file_sentiment(basicout_path, cutoff, file_sentiment_path)
    generate_richoutJSON(richout_path, richout_json)

    if gold_file == "":
        print("""
              Without gold data, the prediction accuracy will not be generated.
              To create gold data, either name your preprocessed data with "yes" or "no",
              or create a gold file similar to Sample/gold/gold.txt,
              and indicate the gold file path through command line.
              """)
    else:
        gold_dct = read_gold_file(gold_file)
        p_total = 0
        n_total = 0
        p_correct = 0
        n_correct = 0

        with open(file_sentiment_path) as fs:
            sentiment_csv = csv.DictReader(fs)
            for r in sentiment_csv:
                file_name = r['File_Name']
                predicted_sentiment = r['Sentiment']
                if gold_dct[file_name] == pos_mark:
                    p_total += 1
                    if predicted_sentiment == pos_mark:
                        p_correct += 1
                elif gold_dct[file_name] == neg_mark:
                    n_total += 1
                    if predicted_sentiment == neg_mark:
                        n_correct += 1

        with open(prediction_accuracy_path, 'a') as pa:
            pa.write("------\nResults:\n------\n")
            if p_total > 0:
                pa.write(f"{p_total} Positive Reviews\n")
                pa.write(f"Percent Correct: {100.0*p_correct/p_total} %\n")
            else:
                pa.write("Total Predicted Positive Review is 0.\n")
            if n_total > 0:
                pa.write(f"{n_total} Negative Reviews\n")
                pa.write(f"Percent Correct: {100.0*n_correct/n_total} %\n")
            else:
                pa.write("Total Predicted Negative Review is 0.\n")
            total = p_total + n_total
            correct = p_correct + n_correct
            if total > 0:
                pa.write(f"{total} Total Reviews\n")
                pa.write(f"Percent Correct: {100.0*correct/total} %\n")
            else:
                pa.write("Total Predicted Positive & Negative Review is 0.\n")

    print("Find all the output in: " + output_folder)

if __name__ == "__main__":
    main()

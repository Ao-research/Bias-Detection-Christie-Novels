import argparse
import os
import csv
from collections import OrderedDict
import json

def get_command_arguments():
    parser = argparse.ArgumentParser(description='SFU Sentiment Calculator')
    parser.add_argument('--input', '-i', type=str, dest='input', action='store',
                        default='/Users/denggeyileao/Library/CloudStorage/OneDrive-UniversitätZürichUZH/SO-CAL/Sample/output/Preprocessed_Output/BOOKS',
                        help="The input file or folder, and the file should be SO_CAL preprocessed text")
    parser.add_argument('--output', '-o', type=str, dest='output', action='store',
                        default='/Users/denggeyileao/Library/CloudStorage/OneDrive-UniversitätZürichUZH/SO-CAL/Sample/output/SO_CAL_Output/BOOKS',
                        help="The output folder")
    parser.add_argument('--config', '-c', type=str, dest='config', action='store',
                        default='/Users/denggeyileao/Library/CloudStorage/OneDrive-UniversitätZürichUZH/SO-CAL/Resources/config_files/en_SO_Calc.ini',
                        help="The configuration file for SO-CAL")
    parser.add_argument('--dic_folder', '-d', type=str, dest='dic_folder', action='store',
                        default='/Users/denggeyileao/Library/CloudStorage/OneDrive-UniversitätZürichUZH/SO-CAL/Resources/dictionaries/English',
                        help="The folder containing all dictionary files")
    parser.add_argument('--cutoff', '-cf', type=float, dest='cutoff', action='store',
                        default=0.0,
                        help="The threshold for sentiment distinction")
    args = parser.parse_args()
    return args

def generate_file_sentiment(basicout_path, cutoff, file_sentiment_path):
    dct_lst = []

    with open(basicout_path) as basic_output:
        for r in basic_output:
            file_score = r.strip().split()
            file = file_score[0]
            score = float(file_score[1])
            if score < cutoff:
                sentiment = "negative"
            elif score > cutoff:
                sentiment = "positive"
            else:
                sentiment = "neutral"
            dct_lst.append({"File_Name": file, "Sentiment": sentiment, "Score": score})

    with open(file_sentiment_path, 'w', newline='') as csv_out:
        fieldnames = ['File_Name', 'Sentiment', 'Score']
        writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
        writer.writeheader()
        for dct in dct_lst:
            writer.writerow(dct)

def main():
    args = get_command_arguments()
    input_path = args.input
    output_folder = args.output

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    config_file = args.config
    dic_folder = args.dic_folder
    cutoff = args.cutoff

    basicout_path = os.path.join(output_folder, "output.txt")
    file_sentiment_path = os.path.join(output_folder, "file_sentiment.csv")

    # Ensure files are created
    open(basicout_path, "w").close()
    open(file_sentiment_path, 'w').close()

    script_path = "/Users/denggeyileao/Library/CloudStorage/OneDrive-UniversitätZürichUZH/SO-CAL/sentiment_calculator.py"
    
    if os.path.isfile(input_path):
        print(f"Processing {os.path.basename(input_path)}...")
        cmd = f"python3 {script_path} --input \"{input_path}\" --output \"{output_folder}\" --bo \"{basicout_path}\" --c \"{config_file}\" --d \"{dic_folder}\""
        print(f"Running command: {cmd}")
        os.system(cmd)
    elif os.path.isdir(input_path):
        for f_name in os.listdir(input_path):
            file_path = os.path.join(input_path, f_name)
            if os.path.isfile(file_path):
                print(f"Processing {f_name}...")
                cmd = f"python3 {script_path} --input \"{file_path}\" --output \"{output_folder}\" --bo \"{basicout_path}\" --c \"{config_file}\" --d \"{dic_folder}\""
                print(f"Running command: {cmd}")
                os.system(cmd)

    generate_file_sentiment(basicout_path, cutoff, file_sentiment_path)

    print(f"Find all the output in: {output_folder}")

if __name__ == "__main__":
    main()

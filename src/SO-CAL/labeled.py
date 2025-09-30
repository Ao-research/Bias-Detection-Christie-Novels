import pandas as pd

def label_scores_to_excel(input_file_path, output_file_path):
    data = []
    
    with open(input_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        for line in lines:
            filename, score = line.strip().split('\t')
            score = float(score)
            
            if score > 0:
                sentiment = 'positive'
                label = 1
            else:
                sentiment = 'negative'
                label = 0
            
            data.append([filename, score, sentiment, label])
    
    df = pd.DataFrame(data, columns=['Filename', 'Score', 'Sentiment', 'Label'])
    
    df.to_excel(output_file_path, index=False)

input_file_path = '/Users/denggeyileao/Library/CloudStorage/OneDrive-UniversitätZürichUZH/SO-CAL/Sample/output/SO_CAL_Output/BOOKS/output.txt'
output_file_path = '/Users/denggeyileao/Library/CloudStorage/OneDrive-UniversitätZürichUZH/SO-CAL/labeled_scores.xlsx'
label_scores_to_excel(input_file_path, output_file_path)

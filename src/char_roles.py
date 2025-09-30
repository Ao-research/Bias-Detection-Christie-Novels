import spacy

nlp = spacy.load('en_core_web_md')

positive_adj = ["good","amazing","happy","trustworthy","friendly"]
negative_adj = ['bad','angry','evil','stubborn','disgusting']


def main():
    char_adjectives = {}
    results = []

    with open("Working_Class.txt", "r") as file:
        for line in file:
            parts = line.strip().split(":")
            char, adjectives = parts[0], parts[1].split()
            char_adjectives[char] = adjectives

    for char, adjectives in char_adjectives.items():
        similarity_p_sum = 0
        similarity_n_sum = 0

        for adj in adjectives:
            for p_word in positive_adj:
                similarity_p_sum += nlp(adj).similarity(nlp(p_word))
            average_p_similarity = similarity_p_sum / len(positive_adj)

            for n_word in negative_adj:
                similarity_n_sum += nlp(adj).similarity(nlp(n_word))
            average_n_similarity = similarity_n_sum / len(negative_adj)

        sentiment = "Positive" if average_p_similarity > average_n_similarity else "Negative"
        results.append((char, sentiment, adjectives[:3])) 

    return results

def pretty_print(character, sentiment, adjectives):
    print(f"{character} is a {sentiment.capitalize()}. Adjectives: {adjectives}")

if __name__ == "__main__":
    results = main()
    for result in results:
        pretty_print(*result)
        
        
        

import json
import os
from transformers import pipeline
import spacy

class WordSenseDisambiguation:
    
    # must be init with pytorch backend to avoid keras version conflict issues
    # this is because keras is used in the Model_Owner.py file
    # and transformers uses keras as well, so we need to use pytorch backend
    def __init__(self):
        """Initialize the word sense disambiguation with the ambiguous dictionary."""
        self.ambiguous_dict = self._load_ambiguous_dict()
        self.classifier = pipeline("zero-shot-classification", 
                                 model="facebook/bart-large-mnli",
                                 framework="pt")
        """Load spaCy with only lemmatization capabilities."""
        self.nlp = spacy.load("en_core_web_sm", disable=["parser", "ner", "tagger"])
        
    
    def _load_ambiguous_dict(self):
        """Load the ambiguous words dictionary from JSON file."""
        dict_path = os.path.join(os.path.dirname(__file__), 
                                "ambiguous_dict_lowercase.json")
        try:
            with open(dict_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Warning: Ambiguous dictionary not found at {dict_path}")
            return {}

    def disambiguate_words(self, sentence):
        """Disambiguates words in a sentence based on context.

        Args:
            sentence (str): The input sentence containing words to disambiguate.

        Returns:
            list: A list of words with their senses disambiguated based on context.
        """
        
        # dictionary of disambiguated words that have been disambiguated
        disambiguated_words = {}
        
        # Check if sentence contains any words that need disambiguation
        # split sentence into list of individual words
        words = sentence.lower().split()

        print("(WordSenseDisambig) Starting word sense disambiguation with words..." + str(words))

        for word in words:

            # check json file dictionary for words and their senses
            if word in self.ambiguous_dict:
                # disambiguate words based on context using zero-shot classification model
                print(f"Disambiguating word: {word}")
                
                # Get the possible senses for the word
                senses = self.ambiguous_dict[word]
                print(f"Possible senses for '{word}': {senses}")
                
                if len(senses) > 1:
                    # feed json values to the model as labels and get the most probable sense
                    result = self.classifier(sentence, senses)
                    best_sense = result['labels'][0]  # Most probable sense
                    print(f"Best sense for '{word}': {best_sense} with confidence {result['scores'][0]}")
                    disambiguated_words[word] = best_sense
                else:
                    # Only one sense available
                    disambiguated_words[word] = senses[0]
        
        return disambiguated_words
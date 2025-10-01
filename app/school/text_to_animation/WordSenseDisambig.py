import json
import os
# Set environment variable to disable tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import spacy

class WordSenseDisambiguation:
    
    def __init__(self):
        """Initialize the word sense disambiguation with the ambiguous dictionary."""
        self.ambiguous_dict = self._load_ambiguous_dict()
        
        # Load custom trained model - point to model directory, not the safetensors file
        model_path = os.path.join(os.path.dirname(__file__), 
                                 "wsd_models", "model")
        try:
            self.model = SentenceTransformer(model_path)
            print(f"SUCCESS - Loaded custom MPNet model from: {model_path}")
        except Exception as e:
            print(f"FAILURE - Failed to load custom model: {e}")
            print("Falling back to base model...")
            self.model = SentenceTransformer('all-mpnet-base-v2')
        
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
        """Disambiguates words in a sentence based on context using semantic similarity.

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
                # disambiguate words based on context using semantic similarity
                print(f"Disambiguating word: {word}")
                
                # Get the possible senses for the word
                senses = self.ambiguous_dict[word]
                print(f"Possible senses for '{word}': {senses}")
                
                if len(senses) > 1:
                    # Encode sentence and all possible senses
                    sentence_embedding = self.model.encode([sentence])
                    sense_embeddings = self.model.encode(senses)
                    
                    # Calculate cosine similarities
                    similarities = cosine_similarity(sentence_embedding, sense_embeddings)[0]
                    
                    # Get the sense with highest similarity
                    best_sense_idx = np.argmax(similarities)
                    best_sense = senses[best_sense_idx]
                    confidence = similarities[best_sense_idx]
                    
                    print(f"Best sense for '{word}': {best_sense} with similarity {confidence}")
                    disambiguated_words[word] = best_sense
                else:
                    # Only one sense available
                    disambiguated_words[word] = senses[0]
        
        return disambiguated_words
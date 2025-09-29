import os
import json
from transformers import AutoTokenizer, T5ForConditionalGeneration
import torch
from dotenv import load_dotenv
from app.school.text_to_animation.WordSenseDisambig import WordSenseDisambiguation

import spacy # Import spaCy for lemmatization mock

load_dotenv(override=True)

class GrammarParser:
    
    def __init__(self):
        """Initialize the GrammarParser with WordSenseDisambiguation instance and text-to-text model."""
        self.wsd = WordSenseDisambiguation()
        
        # Load the text-to-text model and tokenizer
        model_path = os.path.join(os.path.dirname(__file__), "final_auslan_t5_model")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = T5ForConditionalGeneration.from_pretrained(model_path)
        self.prefix = "translate English to Auslan gloss: "

    def lemmatize(self, sentence):
        """
        Convert words in a sentence to their base/root forms using spaCy.
        
        Args:
            sentence (str): Input sentence to lemmatize
            
        Returns:
            str: Sentence with words converted to their lemma forms
            
        Example:
            "I am running to the stores" → "I be run to the store"
        """
        try:
            # Load English language model for natural language processing
            nlp = spacy.load("en_core_web_sm")
            
            # Process the sentence to extract linguistic features
            doc = nlp(sentence)
            
            # Extract the lemma (base form) of each word and join them
            lemmatized_sentence = " ".join([token.lemma_ for token in doc])

            return lemmatized_sentence
        

        except OSError:
            # Handle case where spaCy model is not installed
            print("Error: spaCy English model not found. Please install with: pip install spacy, or run pip install -r requirements.txt.")
            print("If missing, install the model with: python -m spacy download en_core_web_sm")
            return sentence  # Return original sentence as fallback
        except Exception as e:
            # Handle any other unexpected errors
            print(f"Error during lemmatization: {e}")
            return sentence  # Return original sentence as fallback

    def parse_text_to_auslan_grammar(self, t2s_input):
        # takes a regular sentence and converts it to Auslan grammar

        if not t2s_input:
            return {"error": "Invalid input from user"}

        if len(t2s_input.split()) > 2:

            # 1. Lemmatise words using spaCy
            lemmatized_sentence = self.lemmatize(t2s_input)
            
            print(f"(GrammarParser.py): Lemmatized sentence: {lemmatized_sentence}")

            # 2. Use WSD to disambiguate words if necessary
            
            disambiguated_words = {}
            
            disambiguated_words = self.wsd.disambiguate_words(lemmatized_sentence)

            print(f"(GrammarParser.py): Disambiguated words: {disambiguated_words}")

            # 3. Use text-to-text model for grammar parsing
            input_text = self.prefix + lemmatized_sentence
            inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
            
            # Generate the translation
            outputs = self.model.generate(
                **inputs,
                max_length=512,
                num_beams=4,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )
            
            # Decode the output
            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # from the result string, create a list of words
            sentence = result.split()
            
            # loop over the sentence and clarify ambiguous words
            for i, word in enumerate(sentence):
                word_lower = word.lower()
                if word_lower in disambiguated_words:
                    # If the word is ambiguous, replace it with its disambiguated form
                    print(f"(GrammarParser.py): Clarifying word '{word}' to '{disambiguated_words[word_lower]}'")
                    sentence[i] = disambiguated_words[word_lower].upper()

        else:
            sentence = t2s_input.split()


        print(f"(GrammarParser.py): Final parsed result: {sentence}")
        return sentence

    def save_as_json(self, parsed_result, output_filename="parsed_input.json"):
        with open(output_filename, 'w') as outfile:
            json.dump(parsed_result, outfile, indent=4)
            # print(f"Saved parsed result to {output_filename}")
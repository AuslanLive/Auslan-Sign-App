import os
import json
import time
from transformers import AutoTokenizer, T5ForConditionalGeneration
import torch
from dotenv import load_dotenv
from app.school.text_to_animation.WordSenseDisambig import WordSenseDisambiguation

import spacy # Import spaCy for lemmatization mock

load_dotenv(override=True)

class GrammarParser:
    def time() -> float: ...
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
        start = time.time()
        
        print(f"(GrammarParser.py): Starting parse with input: '{t2s_input}'")
        
        if not t2s_input:
            print("(GrammarParser.py): ERROR - Empty or invalid input received")
            return {"error": "Invalid input from user"}

        if len(t2s_input.split()) > 1:
            print(f"(GrammarParser.py): Processing multi-word sentence ({len(t2s_input.split())} words)")

            # 1. Lemmatise words using spaCy
            print("(GrammarParser.py): STAGE 1 - Starting lemmatization...")
            lemmatized_sentence = self.lemmatize(t2s_input)
            print(f"(GrammarParser.py): Original: '{t2s_input}' → Lemmatized: '{lemmatized_sentence}'")

            # 2. Use WSD to disambiguate words if necessary
            print("(GrammarParser.py): STAGE 2 - Starting word sense disambiguation...")
            disambiguated_words = {}
            disambiguated_words = self.wsd.disambiguate_words(lemmatized_sentence)
            print(f"(GrammarParser.py): Found {len(disambiguated_words)} disambiguated words: {disambiguated_words}")

            # 3. Use text-to-text model for grammar parsing
            print("(GrammarParser.py): STAGE 3 - Starting T5 model translation...")
            input_text = self.prefix + lemmatized_sentence
            print(f"(GrammarParser.py): Model input: '{input_text}'")
            
            inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
            print(f"(GrammarParser.py): Tokenized input shape: {inputs['input_ids'].shape}")
            
            # Generate the translation
            print("(GrammarParser.py): Generating translation with T5 model...")
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
            print(f"(GrammarParser.py): Raw model output: '{result}'")
            
            # from the result string, create a list of words
            sentence = result.split()
            print(f"(GrammarParser.py): Split into words: {sentence}")
            
            # loop over the sentence and clarify ambiguous words
            print("(GrammarParser.py): STAGE 4 - Applying word sense disambiguation...")
            original_sentence = sentence.copy()  # Keep a copy for comparison
            for i, word in enumerate(sentence):
                # Check if the word is in the disambiguated words dictionary (squash to lowercase for matching)
                word_lower = word.lower()
                if word_lower in disambiguated_words:
                    # If the word is ambiguous, replace it with its disambiguated form
                    old_word = sentence[i]
                    sentence[i] = disambiguated_words[word_lower]
                    print(f"(GrammarParser.py): Position {i}: '{old_word}' → '{sentence[i]}'")
            
            if original_sentence != sentence:
                print(f"(GrammarParser.py): Before disambiguation: {original_sentence}")
                print(f"(GrammarParser.py): After disambiguation: {sentence}")
            else:
                print("(GrammarParser.py): No words were disambiguated in final sentence")

        else:
            print(f"(GrammarParser.py): Short sentence ({len(t2s_input.split())} words) - skipping processing")
            sentence = t2s_input.split()
            print(f"(GrammarParser.py): Direct word split: {sentence}")
            
        # Convert sentence array to lowercase string for display
        # Example: ['TOON', 'GOD', 'SOUP'] -> "toon god soup"
        lowercase_sentence = ' '.join(word.lower() for word in sentence)
        print(f"(GrammarParser.py): Lowercase string: '{lowercase_sentence}'")
        
        print(f"(GrammarParser.py): FINAL RESULT: {sentence}")
        print(f"(GrammarParser.py): Processing completed in {time.time()-start:.4f} seconds")
        return sentence

    def save_as_json(self, parsed_result, output_filename="parsed_input.json"):
        with open(output_filename, 'w') as outfile:
            json.dump(parsed_result, outfile, indent=4)
            # print(f"Saved parsed result to {output_filename}")
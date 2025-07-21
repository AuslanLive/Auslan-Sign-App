import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from app.school.text_to_animation.WordSenseDisambig import WordSenseDisambiguation

import spacy # Import spaCy for lemmatization mock

load_dotenv(override=True)

genai_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure()

class GrammarParser:
    
    def __init__(self):
        """Initialize the GrammarParser with WordSenseDisambiguation instance."""
        self.wsd = WordSenseDisambiguation()

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
            print(f"Lemmatized sentence: {lemmatized_sentence}")  # Debug print
            return lemmatized_sentence
        

        except OSError:
            # Handle case where spaCy model is not installed
            print("Error: spaCy English model not found. Please install with: pip install spacy, or use requirements.txt.")
            print("Install the model with: python -m spacy download en_core_web_sm")
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
            
            print(f"(GrammarParser): Lemmatized sentence: {lemmatized_sentence}")  # Debug print

            # 2. Use WSD to disambiguate words if necessary
            disambiguated_sentence = self.wsd.disambiguate_words(lemmatized_sentence)
            
            # 3. Use model for grammar parsing here
            model = genai.GenerativeModel("gemini-1.5-flash")

            response = model.generate_content(
                """You are a professional Auslan linguist and translator. Your task is to convert written English sentences into their Auslan equivalent using correct Auslan grammar, not word-for-word translation.

                Rules to follow:
                Use Topic-Comment or Time-Topic-Comment structure, as appropriate for Auslan.
                E.g., place time or topic elements at the beginning.
                Simplify function words (like "is," "are," "the")—these are often omitted in Auslan.
                Use all capital letters to represent Auslan signs (gloss format).
                Maintain the meaning, not the exact English structure.
                If relevant, use facial expressions or body shifts to indicate questions or contrast (annotate this in brackets).
                
                Examples:
                
                -- START OF EXAMPLES --
                
                English: "I am going to the shop."
                Auslan gloss: SHOP I GO
                
                English: “She is studying at university today.”
                Auslan gloss: TODAY UNIVERSITY SHE STUDY

                English: “Do you want coffee?”
                Auslan gloss: COFFEE YOU WANT (q)
                (q = yes/no question facial expression)

                English: “He didn't go home yesterday.”
                Auslan gloss: YESTERDAY HOME HE GO NOT

                English: “After lunch, we will walk to the park.”
                Auslan gloss: LUNCH FINISH PARK WE WALK
                
                -- END OF EXAMPLES --
                
                If there is no other explanation, simply return the original input sentence.
                
                If it can be translated, please make sure to return only the Auslan gloss without any additional text or explanation.
                
                Now, convert the following sentence into Auslan grammar using gloss:

                """ + t2s_input
            )

            response_dict = response.to_dict()

            result = (
                response_dict["candidates"][0]["content"]["parts"][0]["text"].strip().replace(
                    "\n", "").replace("\"", "")
                if response_dict["candidates"]
                else "No valid response"
            )

        else:
            result = t2s_input

        return result

    def save_as_json(self, parsed_result, output_filename="parsed_input.json"):
        with open(output_filename, 'w') as outfile:
            json.dump(parsed_result, outfile, indent=4)
            # print(f"Saved parsed result to {output_filename}")
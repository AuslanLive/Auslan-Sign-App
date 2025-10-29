import os
import json
import time
import google.generativeai as genai
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

            # 3. Use model for grammar parsing here
            # start timer to count gemini processing time
            start_time = time.time()
            print("(GrammarParser.py): STAGE 3 - Generating Auslan grammar using GEMINI 2.5 FLASH model...")
            model = genai.GenerativeModel("gemini-2.5-flash-lite")

            response = model.generate_content(
                """You are a professional Auslan linguist and translator. Convert written English sentences into their Auslan-style English equivalent using correct Auslan grammar — not word-for-word translation.

                Output rules:
                - Output must contain English letters and spaces only. Do NOT include any symbols, punctuation, brackets, or capitalization markers.
                - Use natural lowercase English words only.
                - Do not add explanations or extra text.

                Grammar rules to follow:
                - Use Topic–Comment or Time–Topic–Comment structure. Place time or topic elements at the beginning.
                - Omit function words that Auslan typically drops (e.g., is, are, was, were, the, a, to when showing motion).
                - Use simple base verbs (go, want, see) — avoid tense inflections.
                - Put “not” at the end of a clause for negation (e.g., yesterday he go home not).
                - Use “finish” to indicate a completed action (e.g., lunch finish we walk park).
                - For yes or no questions, end with a question mark (no symbols other than this).
                - For wh-questions, put the wh-word (who, what, where, when, why) at the end.
                - Keep names, places, and numbers as normal English words.
                - If translation is unclear, return the input unchanged.
                
                - The word “has” changes meaning depending on context:
                • If it shows **possession**, keep HAVE or use a possessive (“my/your/his/her”).
                    Example: “She has a car.” → “She have car” or “Her car.”
                • If it marks **completed action**, replace with FINISH.
                    Example: “He has eaten.” → “He eat finish.”
                • If it shows **obligation**, use MUST or NEED.
                    Example: “He has to go.” → “He must go.”
                • If it only supports the sentence (no meaning change), remove it entirely.
                
                NOTE: Input text will be LEMMATIZED (base forms). Do not assume English tense from verb forms.

                • HAVE disambiguation (input may show 'have' for has/had):
                - Possession: if 'have' is followed by a noun phrase (optionally with quantifier/number), keep as 'have' or convert to possessive.
                    Example: she have car  →  she have car  /  her car
                - Obligation: if pattern 'have to' (or OBLIGATION tag present), use 'must' or 'need'.
                    Example: he have to go  →  he must go
                - Completed action (perfect): use 'finish' ONLY if explicit evidence exists:
                    time words (yesterday, before, already, just, earlier) or COMPLETED tag.
                    Example: already he eat  →  he eat finish
                - Otherwise, remove supportive 'have' that adds no meaning.

                • Negation: map any 'do not/does not/did not' to clause-final 'not'.
                Example: he do not go home  →  home he go not

                Return only the translated sentence.

                Examples:
                English: I am going to the shop.
                Output: shop I go

                English: She is studying at university today.
                Output: today university she study

                English: Do you want coffee?
                Output: coffee you want?

                English: He didn't go home yesterday.
                Output: yesterday he go home not

                English: After lunch, we will walk to the park.
                Output: lunch finish we walk park

                English: Where are you meeting them?
                Output: you meet them where?

                Now, convert the following sentence into Auslan-style English:
                
                """ + lemmatized_sentence
            )
            
            response_dict = response.to_dict()

            result = (
                response_dict["candidates"][0]["content"]["parts"][0]["text"].strip().replace(
                    "\n", "").replace("\"", "")
                
                # if no response, set result to a default value
                if response_dict["candidates"]
                else "No valid response"
            )
            
            time_taken = time.time() - start_time
            print(f"(GrammarParser.py): COMPLETE GEMINI response received in {time_taken:.4f} seconds")
            
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
            
            # Check for 'finish' and replace with 'finish (complete)'
            for i, word in enumerate(sentence):
                if word.lower() == 'finish':
                    sentence[i] = 'finish (complete)'
                    print(f"(GrammarParser.py): Position {i}: 'finish' → 'finish (complete)'")
            
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
        lowercase_sentence = ' '.join(word.lower() for word in sentence)
        print(f"(GrammarParser.py): Lowercase string: '{lowercase_sentence}'")
        
        # print(f"(GrammarParser.py): FINAL RESULT: {sentence}")
        print(f"(GrammarParser.py): Processing completed in {time.time()-start:.4f} seconds")
        return sentence

    def save_as_json(self, parsed_result, output_filename="parsed_input.json"):
        with open(output_filename, 'w') as outfile:
            json.dump(parsed_result, outfile, indent=4)
            # print(f"Saved parsed result to {output_filename}")
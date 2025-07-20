import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv(override=True)

genai_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure()

class TextToAnimation:

    def parse_text_to_sign(self, t2s_input):
        if not t2s_input:
            return {"error": "Invalid input from user"}

        if len(t2s_input.split()) > 2:
            # print("Contacting Gemini")

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
                
                Example:
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
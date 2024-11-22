import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
from flask import Flask, jsonify, request
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

load_dotenv(override=True)

genai_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure()


class ResultsParser:
    # Only create model once
    def __init__(self, connectinator):
        self.model = None
        self.connectinator = connectinator

    # Function for lazy loading for efficiency
    def _initialize_model(self):
        if self.model is None:
            self.model = genai.GenerativeModel("gemini-1.5-flash")

    def parse_model_output(self, model_output):
        executor = ThreadPoolExecutor()
        print(model_output)
        if len(model_output) == 0:
            # return {"error": "No output from model"}
            return

        best_model_phrase = ""
        for model_output_single in model_output:
            best_phrase, best_confidence = max(
                model_output_single, key=lambda item: item[1])
            best_model_phrase = ", ".join([best_model_phrase, best_phrase])

        # print(best_model_phrase)
        if len(best_model_phrase.split()) > 2:
            # print("contacting gemini")
            self.connectinator.geminiFlag = True
            # print(self.connectinator.geminiFlag)

            # Create model if it does not exist
            self._initialize_model()

            # print("GETTING RESULT")
            response = self.model.generate_content(
                "Convert these words into a correct English sentence, each of the words are separated by a comma and wrap the phrase in **: " + best_model_phrase
                )

            # Parse the response
            response_dict = response.to_dict()
            full_result = response_dict["candidates"][0]["content"]["parts"][0]["text"].strip(
                '"').replace("\n", "").replace("\"", "")

            # Extract only the text between ** symbols
            match = re.search(r"\*\*(.*?)\*\*", full_result)
            if match:
                result = match.group(1)
            else:
                result = full_result  # Fallback if no ** found

            # print(result)

        else:
            result = best_model_phrase
        # print("DONE")
        self.connectinator.geminiFlag = False
        # print(self.connectinator.geminiFlag)
        return result

    def save_as_json(self, parsed_result, output_filename="parsed_result.json"):
        with open(output_filename, 'w') as outfile:
            json.dump(parsed_result, outfile, indent=4)
            # print(f"Saved parsed result to {output_filename}")

            # Define a function to perform the API call and file write operation


class textAnimationTranslation:

    def parse_text_to_sign(self, t2s_input):
        if not t2s_input:
            return {"error": "Invalid input from user"}

        if len(t2s_input.split()) > 2:
            # print("Contacting Gemini")

            model = genai.GenerativeModel("gemini-1.5-flash")

            response = model.generate_content(
                "Convert this phrase into an Auslan English sentence (as text) Provide only the text no other explanation: " + t2s_input
            )

            response_dict = response.to_dict()

            result = (
                response_dict["candidates"][0]["content"]["parts"][0]["text"].strip().replace(
                    "\n", "").replace("\"", "")
                if response_dict["candidates"]
                else "No valid response"
            )

            # print(result)
            # print(result2)

        else:
            result = t2s_input

        return result

    def save_as_json(self, parsed_result, output_filename="parsed_input.json"):
        with open(output_filename, 'w') as outfile:
            json.dump(parsed_result, outfile, indent=4)
            # print(f"Saved parsed result to {output_filename}")

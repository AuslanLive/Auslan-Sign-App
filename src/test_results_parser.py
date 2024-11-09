import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(override=True)

genai_api_key = os.getenv("GOOGLE_API_KEY")

os.environ["GOOGLE_API_KEY"] = genai_api_key
genai.configure()
class ResultsParser:
    def __init__(self):
        pass

    def parse_model_output(self, model_output):
        """
        Parses the output from the sign language model and saves the best word 
        with the highest confidence to a JSON file.
        
        Args:
            model_output (list of tuples): Output from the model, expected as a list of (word, confidence) tuples.
        """
        if not model_output:
            # If there is no output, you could return or log an error
            return {"error": "No output from model"}

        # Find the word with the highest confidence
        best_model_phrase, best_confidence = max(model_output, key=lambda item: item[1])

        if len(best_model_phrase.split()) > 2:
            print("contacting gemini")
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Convert these words into a correct English sentence:"+ best_model_phrase)
            response_dict = response.to_dict()
            result = response_dict["candidates"][0]["content"]["parts"][0]["text"].strip('"').strip().replace("\n", "").replace("\"", "")
            print(result)
        else:
        #print(json.dumps(text))
            result = {
                "word": best_model_phrase,
                "confidence": best_confidence
            }
        return result

    def save_as_json(self, parsed_result, output_filename="parsed_result.json"):
        """
        Save the parsed result as a JSON file.
        """
        with open(output_filename, 'w') as outfile:
            json.dump(parsed_result, outfile, indent=4)
            print(f"Saved parsed result to {output_filename}")

def load_model_output(file_path):
        with open(file_path, 'r') as file:
             data = json.load(file)
             return data["model_output"]

# Manual testing
if __name__ == "__main__":
    # Create an instance of ResultsParser
    parser = ResultsParser()

    # Path to the model_output.json file (adjust path as needed)
    model_output_file = "src/model_output.json"
    
    # Load the model output from JSON file
    model_output = load_model_output(model_output_file)

    # Parse the results
    parsed_result = parser.parse_model_output(model_output)
    
    # Save the parsed result to a new JSON file
    parser.save_as_json(parsed_result)
from app.school.video_to_text.Model_Owner import Model
from app.school.video_to_text.InputParser import InputParser
import logging
from app.school.video_to_text.results_parser import ResultsParser
from app.school.text_to_animation.GrammarParser import GrammarParser
from time import time
import json
from app.school.text_to_animation.pose_video_creator import process_sentence


def create_logger():
    # Set up logging
    logger = logging.getLogger()  # Create a logger
    logger.setLevel(logging.INFO)  # Set the logging level

    # Create a file handler to log messages to a file
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)  # Set the file logging level

    # Create a console handler to log messages to the terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Set the console logging level

    # Create a formatter and set it for both handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class Connectinator:
    def __init__(self, model_path=''):
        # Setting up the results list
        self.full_phrase = AsyncResultsList(self)
        self.end_phrase_flag = False
        self.front_end_translation_variable = ''
        self.geminiFlag = False

        # Creating logger
        self.logger = create_logger()

        # Creating model class from the model_owner file
        self.model = Model(model_path)

        # Creating data processor class
        self.inputProc = InputParser()

        # Create result parser
        self.results_parser = ResultsParser(self)

        # Create grammar parser
        self.grammar_parser = GrammarParser()

        self.predictionList = []
        self.prevFlag = False

    # Process the model output
    def format_model_output(self, output):
        processed_output = self.results_parser.parse_model_output(output)

        # Update log file
        self.logger.info(
            'Model Output Processed Successfully! Message: %s', processed_output)

        # Pass this then to a varable being used for the react front end.
        if processed_output is not None:
            self.front_end_translation_variable = processed_output

        # print("DONEEE")

        with open('model_output.txt', 'a+') as f:
            f.write(
                f"\nTime: {str(time())}, Phrase: {self.front_end_translation_variable}")

    # Return auslan grammer sentence
    def format_sign_text(self, input):

        processed_t2s_phrase = self.grammar_parser.parse_text_to_auslan_grammar(input)

        # Create video from the processed sentence
        process_sentence(processed_t2s_phrase)

        # Update log file
        self.logger.info(
            'Text To Sign Processed Successfully! Message: %s', processed_t2s_phrase)

        return processed_t2s_phrase

    def get_transltion(self):
        return self.front_end_translation_variable

    def get_gem_flag(self):
        return self.geminiFlag

    # Process frame
    async def process_frame(self, keypoints):
        # print(keypoints)
        full_chunk, self.end_phrase_flag = self.inputProc.process_frame(
            keypoints)
        # print(keypoints)
        # full_chunk, self.end_phrase_flag = self.inputProc.process_frame(
        #     keypoints)
        if self.end_phrase_flag == True and self.prevFlag == False:
            # print("meow meow meow meow")
            self.prevFlag = True
            # print(self.end_phrase_flag, self.prevFlag)
            self.full_phrase.parse_results()
            self.prevFlag = False

            # print(f"End Phrase: {self.end_phrase_flag}")

        if full_chunk is not None:
            # print("AAAAAAAAa SENT TO THE MODEL")
            self.prevFlag = False

            # async predict the work and then add it to the self.full_phrase

            predicted_result = await self.predict_model(full_chunk)

            with open('ball.txt', 'a+') as f:
                f.write(f"time: {str(time())}, predict:")
                f.write(json.dumps(str(predicted_result)))
                f.write("\n\n")
                
            print(predicted_result['model_output'])
            self.full_phrase.append(predicted_result['model_output'])

    # TODO: LISTENER FOR RECEIVE FROM SAVE CHUNK, SEND TO MODEL

    # Get model prediction

    async def predict_model(self, keypoints):
        # print("SENT TO PREDICT")
        return await self.model.query_model(keypoints)

    # TODO: LISTENER FOR RECEIVE OUTPUT FROM MODEL, ADD TO LIST, SEND TO RESULTS PARSER

# Custom list class so that it can access run async and check when stuff is added


class AsyncResultsList(list):
    def __init__(self, connectinator_instance: Connectinator, *args):
        super().__init__(*args)
        self.saved_results = None
        self.connectinator = connectinator_instance

    def append(self, item):
        # print("adding worekds")
        self.connectinator.logger.info(
            f"Word added with shape {item}")
        super().append(item)

    # async call the connectinator.format_model_output on this list

    def parse_results(self):
        # Reset list result
        self.saved_results = [i for i in self]
        self.clear()

        # Reset the flag
        self.connectinator.logger.info("Parsing results asynchronously...")
   
        # change to pass saves results
        self.connectinator.format_model_output(self.saved_results)

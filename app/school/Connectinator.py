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
        # For the new BiLSTM model, output is already formatted
        # Extract the top-1 prediction for the main translation
        if output and len(output) > 0:
            # Get the top prediction (highest probability)
            top_prediction = max(output, key=lambda x: x[1])
            processed_output = top_prediction[0]  # Get the label
            
            # Update log file
            self.logger.info(
                'Model Output Processed Successfully! Message: %s', processed_output)

            # Pass this then to a variable being used for the react front end.
            if processed_output is not None:
                self.front_end_translation_variable = processed_output

            with open('model_output.txt', 'a+') as f:
                f.write(
                    f"\nTime: {str(time())}, Phrase: {self.front_end_translation_variable}")
        else:
            self.logger.info('No model output received')

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
    
    def get_top_predictions(self):
        """Get the top-5 predictions from the last model output"""
        if hasattr(self, 'last_model_output') and self.last_model_output:
            return self.last_model_output.get('top_5', [])
        return []
    
    def get_top_1_prediction(self):
        """Get the top-1 prediction from the last model output"""
        if hasattr(self, 'last_model_output') and self.last_model_output:
            return self.last_model_output.get('top_1', {})
        return {}

    # Process frame
    async def process_frame(self, keypoints):
        print(f"CONSOLE: Received keypoints input with {len(keypoints.get('keypoints', []))} components")
        
        full_chunk, self.end_phrase_flag = self.inputProc.process_frame(keypoints)
        
        if self.end_phrase_flag == True and self.prevFlag == False:
            self.prevFlag = True
            print("CONSOLE: End of phrase detected, parsing results...")
            self.full_phrase.parse_results()
            self.prevFlag = False

        if full_chunk is not None:
            print(f"CONSOLE: Model input received - chunk shape: {full_chunk.shape}")
            self.prevFlag = False

            # async predict the work and then add it to the self.full_phrase
            predicted_result = await self.predict_model(full_chunk)

            # Store the full model output for top-5 predictions
            self.last_model_output = predicted_result

            with open('ball.txt', 'a+') as f:
                f.write(f"time: {str(time())}, predict:")
                f.write(json.dumps(str(predicted_result)))
                f.write("\n\n")
                
            # Console logging for predictions
            top_1 = predicted_result['top_1']
            top_5 = predicted_result['top_5']
            
            print(f"CONSOLE: WORD DETECTED - Top-1: {top_1['label']} ({top_1['probability']:.4f})")
            print("CONSOLE: Top-5 predictions:")
            for i, (label, prob) in enumerate(top_5):
                print(f"  {i+1}. {label}: {prob:.4f}")
            
            self.full_phrase.append(predicted_result['model_output'])

    # TODO: LISTENER FOR RECEIVE FROM SAVE CHUNK, SEND TO MODEL

    # Get model prediction

    async def predict_model(self, keypoints):
        self.logger.info(f"TERMINAL: Sending keypoints to model - shape: {keypoints.shape}")
        result = await self.model.query_model(keypoints)
        self.logger.info(f"TERMINAL: Model prediction completed - top-1: {result['top_1']['label']} ({result['top_1']['probability']:.4f})")
        return result

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
        self.connectinator.logger.info("TERMINAL: Parsing results asynchronously...")
        self.connectinator.logger.info(f"TERMINAL: Processing {len(self.saved_results)} word predictions")
   
        # change to pass saves results
        self.connectinator.format_model_output(self.saved_results)

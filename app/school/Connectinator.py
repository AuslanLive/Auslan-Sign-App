from app.school.video_to_text.HonoursModelOwner import HonoursModelOwner
from app.school.video_to_text.HonoursInputParser import HonoursInputParser
import logging
from app.school.video_to_text.results_parser import ResultsParser
# GrammarParser import moved to __init__ to make it optional
from time import time
import json
# process_sentence import moved to format_sign_text to make it optional


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
    def __init__(self, model_path='', label_map_path='', stats_path=''):
        # Setting up the results list
        self.full_phrase = AsyncResultsList(self)
        self.end_phrase_flag = False
        self.front_end_translation_variable = ''
        self.geminiFlag = False

        # Creating logger
        self.logger = create_logger()

        # Creating honors model with top-5 predictions
        self.model = HonoursModelOwner(model_path, label_map_path, top_k=5)

        # Creating data processor class for hands-only 64-frame windows
        self.inputProc = HonoursInputParser(stats_path)

        # Create result parser
        self.results_parser = ResultsParser(self)

        # Create grammar parser (optional for text-to-sign)
        try:
            from app.school.text_to_animation.GrammarParser import GrammarParser
            self.grammar_parser = GrammarParser()
            self.logger.info("Grammar parser loaded successfully")
        except Exception as e:
            self.logger.warning(f"Grammar parser failed to load: {e}")
            self.logger.warning("Text-to-sign feature will be disabled")
            self.grammar_parser = None

        self.predictionList = []
        self.prevFlag = False
        
        # Store pending top-5 predictions for user selection
        self.pending_predictions = []
        self.current_sentence_words = []
        
        # Configuration: Auto-add all predictions (click-to-fix)
        self.auto_add_threshold = 0.15  # Auto-add if confidence > 15%
        self.show_selector_threshold = 0.0  # Never show inline selector (always auto-add)
        
        # Pause flag to stop processing when modal is open
        self.is_paused = False

    # Process the model output
    def format_model_output(self, output):
        processed_output = self.results_parser.parse_model_output(output)

        # Update log file
        self.logger.info(
            'Model Output Processed Successfully! Message: %s', processed_output)

        # Pass this then to a variable being used for the react front end.
        if processed_output is not None:
            self.front_end_translation_variable = processed_output

        # print("DONEEE")

        with open('model_output.txt', 'a+') as f:
            f.write(
                f"\nTime: {str(time())}, Phrase: {self.front_end_translation_variable}")

    # Return auslan grammar sentence
    def format_sign_text(self, input):
        
        if self.grammar_parser is None:
            self.logger.error("Text-to-sign feature is disabled (grammar parser not loaded)")
            return ["TEXT_TO_SIGN_DISABLED"]

        try:
            from app.school.text_to_animation.pose_video_creator import process_sentence
            
            processed_t2s_phrase = self.grammar_parser.parse_text_to_auslan_grammar(input)

            # Create video from the processed sentence
            process_sentence(processed_t2s_phrase)

            # Update log file
            self.logger.info(
                'Text To Sign Processed Successfully! Message: %s', processed_t2s_phrase)

            return processed_t2s_phrase
        except Exception as e:
            self.logger.error(f"Error in text-to-sign processing: {e}")
            return ["TEXT_TO_SIGN_ERROR"]

    def get_translation(self):
        return self.front_end_translation_variable
    
    def get_sentence_with_words(self):
        """
        Get the sentence as a list of word objects with alternatives.
        Returns both old string format and new word object format.
        """
        words_data = []
        for item in self.current_sentence_words:
            if isinstance(item, dict):
                words_data.append(item)
            else:
                # Old format - convert to word object without alternatives
                words_data.append({
                    'word': item,
                    'alternatives': [],
                    'confidence': 1.0,
                    'auto': False,
                    'id': len(words_data)
                })
        return words_data
    
    def replace_word(self, word_id, new_word):
        """
        Replace a word in the sentence (click-to-fix).
        
        Args:
            word_id: Index/ID of the word to replace
            new_word: New word text
        """
        try:
            if 0 <= word_id < len(self.current_sentence_words):
                item = self.current_sentence_words[word_id]
                if isinstance(item, dict):
                    old_word = item['word']
                    item['word'] = new_word
                    item['corrected'] = True
                    self.logger.info(f"Replaced word at {word_id}: {old_word} → {new_word}")
                else:
                    # Old format
                    self.current_sentence_words[word_id] = new_word
                    self.logger.info(f"Replaced word at {word_id}: {item} → {new_word}")
                
                self.update_translation_display()
                return True
            else:
                self.logger.error(f"Invalid word_id: {word_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error replacing word: {e}")
            return False

    def get_gem_flag(self):
        return self.geminiFlag

    # Process frame (updated for honors model)
    async def process_frame(self, keypoints):
        """
        Process incoming frame with hands-only keypoints.
        Returns top-5 predictions when 64-frame window is ready.
        
        Pauses processing when user is selecting from top-5 modal.
        """
        try:
            # Skip processing if paused (modal is open)
            if self.is_paused:
                return
            
            # Process frame through honors input parser
            window_data, word_ended_flag = self.inputProc.process_frame(keypoints)
            
            # Note: word_ended_flag indicates a single word ended (hands out of frame)
            # We DON'T finalize the entire sentence here - words accumulate!
            # Sentence is only finalized when user presses Clear button

            # Process word when ready
            if window_data is not None:
                # Get top-5 predictions from model
                predicted_result = await self.predict_model(window_data)
                
                if predicted_result is not None:
                    # Log prediction
                    with open('ball.txt', 'a+') as f:
                        f.write(f"time: {str(time())}, top5_predict:")
                        f.write(json.dumps(str(predicted_result['top5'])))
                        f.write("\n\n")
                    
                    # Handle prediction based on confidence
                    self.handle_prediction(predicted_result)
                    
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def handle_prediction(self, prediction_result):
        """
        Handle top-5 prediction with confidence-based logic:
        - High confidence (>15%): Auto-add word, allow click to fix
        - Low confidence (<15%): Ignore
        """
        top1 = prediction_result['top1']
        top5 = prediction_result['top5']
        confidence = top1['confidence']
        word = top1['label']
        
        # Verbose console logging for user feedback
        print("\n" + "="*60)
        print(f"🎯 MODEL PREDICTION COMPLETE!")
        print(f"   Top word: {word} ({confidence:.1%} confidence)")
        top5_display = ', '.join([f"{p['label']} ({p['confidence']:.0%})" for p in top5])
        print(f"   Top 5: {top5_display}")
        print("="*60 + "\n")
        
        self.logger.info(f"Prediction: {word} ({confidence:.2%})")
        top5_str = ', '.join([f"{p['label']} ({p['confidence']:.2%})" for p in top5])
        self.logger.info(f"Top-5: {top5_str}")
        
        if confidence >= self.auto_add_threshold:
            # High confidence: Auto-add with alternatives stored
            print(f"✅ AUTO-ADDING: '{word}' (confidence: {confidence:.1%})")
            print(f"   Click the word to see alternatives\n")
            self.logger.info(f"Auto-adding high-confidence word: {word} ({confidence:.2%})")
            self.add_word_to_sentence_with_alternatives(word, top5, confidence, auto=True)
            # Don't pause - continue signing!
            
        elif confidence >= self.show_selector_threshold:
            # Medium/low confidence: Show selector
            self.logger.info(f"Showing selector for medium-confidence prediction ({confidence:.2%})")
            self.pending_predictions.append({
                'top1': top1,
                'top5': top5,
                'timestamp': time(),
                'confidence': confidence
            })
            # Pause frame processing until user makes selection
            self.pause_processing()
            
        else:
            # Very low confidence: Ignore
            self.logger.info(f"Ignoring low-confidence prediction: {word} ({confidence:.2%})")
    
    def pause_processing(self):
        """Pause frame processing (modal is open)."""
        self.is_paused = True
        self.logger.info("Frame processing PAUSED - waiting for user selection")
    
    def resume_processing(self):
        """Resume frame processing (modal closed)."""
        self.is_paused = False
        self.logger.info("Frame processing RESUMED")
    
    def add_word_to_sentence(self, word, auto=False):
        """
        Add a word to the current sentence.
        
        Args:
            word: Word to add
            auto: Whether this was auto-added (high confidence)
        """
        # Simple duplicate detection
        if len(self.current_sentence_words) >= 2:
            if self.current_sentence_words[-1] == word and self.current_sentence_words[-2] == word:
                self.logger.info(f"Skipping duplicate word: {word}")
                return
        
        self.current_sentence_words.append(word)
        self.update_translation_display()
        
        self.logger.info(f"Added word ({'auto' if auto else 'manual'}): {word}")
        self.logger.info(f"Current sentence: {' '.join(self.current_sentence_words)}")
    
    def add_word_to_sentence_with_alternatives(self, word, alternatives, confidence, auto=False):
        """
        Add a word to the sentence with stored alternatives for click-to-fix.
        
        Args:
            word: Word to add
            alternatives: List of top-5 predictions
            confidence: Confidence of the selected word
            auto: Whether this was auto-added (high confidence)
        """
        # Allow duplicates - user can sign the same word multiple times
        
        # Store word with its alternatives for click-to-fix
        word_data = {
            'word': word,
            'alternatives': alternatives,
            'confidence': confidence,
            'auto': auto,
            'timestamp': time(),
            'id': len(self.current_sentence_words)  # Unique ID
        }
        
        self.current_sentence_words.append(word_data)
        self.update_translation_display()
        self.logger.info(f"Added word with alternatives: {word} ({confidence:.2%}, auto={auto})")
    
    def select_word_from_top5(self, selected_word):
        """
        User selected a word from the top-5 predictions.
        
        Args:
            selected_word: The word user chose
        """
        self.add_word_to_sentence(selected_word, auto=False)
        
        # Clear the pending prediction that was just handled
        if self.pending_predictions:
            self.pending_predictions.pop(0)
        
        # Reset frame buffer for next word
        self.inputProc.reset()
        self.logger.info("Frame buffer reset after word selection")
        
        # Resume processing
        self.resume_processing()
    
    def skip_current_prediction(self):
        """
        User skipped the current top-5 prediction.
        """
        self.logger.info("User skipped prediction")
        
        # Clear the pending prediction
        if self.pending_predictions:
            self.pending_predictions.pop(0)
        
        # Reset frame buffer for next word
        self.inputProc.reset()
        self.logger.info("Frame buffer reset after skipping prediction")
        
        # Resume processing
        self.resume_processing()
    
    def get_pending_predictions(self):
        """
        Get pending top-5 predictions for frontend.
        
        Returns:
            List of pending prediction dicts
        """
        return self.pending_predictions
    
    def clear_pending_predictions(self):
        """Clear all pending predictions."""
        self.pending_predictions = []
    
    def get_frame_buffer_status(self):
        """
        Get current frame collection status for UI feedback.
        
        Returns:
            Dict with frame collection info
        """
        return self.inputProc.get_buffer_status()
    
    async def force_predict_current_buffer(self):
        """
        Force a prediction on the current buffer (manual trigger).
        Used for spacebar capture.
        
        Returns:
            Bool: True if prediction was made, False if not enough frames
        """
        try:
            # Check if we have minimum frames
            status = self.inputProc.get_buffer_status()
            if status['frames_collected'] < 32:  # Minimum 32 frames
                self.logger.warning("Not enough frames for forced prediction")
                return False
            
            # Create window from current buffer
            window_data = self.inputProc.create_window()
            
            if window_data is not None:
                # Get prediction
                predicted_result = await self.predict_model(window_data)
                
                if predicted_result is not None:
                    # Log prediction
                    with open('ball.txt', 'a+') as f:
                        f.write(f"time: {str(time())}, manual_trigger, top5_predict:")
                        f.write(json.dumps(str(predicted_result['top5'])))
                        f.write("\n\n")
                    
                    # Handle prediction
                    self.handle_prediction(predicted_result)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in force_predict_current_buffer: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def update_translation_display(self):
        """Update the translation variable shown to frontend."""
        # Handle both string words and word objects with alternatives
        words = []
        for item in self.current_sentence_words:
            if isinstance(item, dict):
                words.append(item['word'])
            else:
                words.append(item)
        self.front_end_translation_variable = ' '.join(words)
    
    def finalize_sentence(self):
        """
        Called when phrase ends (hands down detected).
        Builds final sentence from collected words.
        """
        if self.current_sentence_words:
            # Extract words from word objects
            words = []
            for item in self.current_sentence_words:
                if isinstance(item, dict):
                    words.append(item['word'])
                else:
                    words.append(str(item))
            
            final_sentence = ' '.join(words)
            self.logger.info(f"Phrase ended. Final sentence: {final_sentence}")
            
            # Update frontend variable
            self.front_end_translation_variable = final_sentence
            
            # Write to log file
            with open('model_output.txt', 'a+') as f:
                f.write(f"\nTime: {str(time())}, Phrase: {final_sentence}")
            
            # Clear for next phrase
            self.current_sentence_words = []
            self.pending_predictions = []

    # TODO: LISTENER FOR RECEIVE FROM SAVE CHUNK, SEND TO MODEL

    # Get model prediction (updated for honors model)
    async def predict_model(self, window_data):
        """
        Query the honors model with preprocessed window data.
        
        Args:
            window_data: Preprocessed [1, 64, 84] array
            
        Returns:
            Dict with top-5 predictions
        """
        return await self.model.query_model(window_data)

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

# sensors/sensory_inputs/auditory/wake_word_detector.py
import json
import random
import threading
from difflib import SequenceMatcher

from sensors.ears.microphone import MicrophoneInput
from sensors.mouth.mouth import Mouth
from utils.logger import Logger

logger = Logger()

class WakeWordDetector:
    def __init__(self, microphone_input, config_file='config/react_keys.json', confidence_threshold=0.8):
        """
        Initialize the WakeWordDetector with configurable wake words, sleep words, and their responses.
        
        Args:
            microphone_input (MicrophoneInput): The microphone input system for capturing audio.
            config_file (str): Path to the configuration JSON file containing wake/sleep words and responses.
            confidence_threshold (float): Minimum confidence score required to trigger a wake or sleep word.
        """
        self.microphone_input = microphone_input
        self.config_file = config_file
        self.speak = Mouth()
        self.confidence_threshold = confidence_threshold
        self.listening = False
        self.lock = threading.Lock()

        self.wake_words = []
        self.sleep_words = []
        self.wake_responses = []
        self.sleep_responses = []
        self.load_config()  # Load initial config
        logger.info("WakeWordDetector initialized.")

    def load_config(self):
        """
        Load wake/sleep words and responses from the configuration JSON file.
        """
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.wake_words = config.get("wake_words", [])
                self.sleep_words = config.get("sleep_words", [])
                self.wake_responses = config.get("wake_responses", [])
                self.sleep_responses = config.get("sleep_responses", [])
                logger.info("Successfully loaded wake and sleep words and responses.")
        except FileNotFoundError:
            logger.error(f"Config file {self.config_file} not found.")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config file {self.config_file}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error loading config file {self.config_file}: {e}", exc_info=True)

    def update_config(self, new_config_data):
        """
        Update the wake/sleep words and responses dynamically.
        
        Args:
            new_config_data (dict): New configuration data to update.
        """
        self.wake_words = new_config_data.get("wake_words", self.wake_words)
        self.sleep_words = new_config_data.get("sleep_words", self.sleep_words)
        self.wake_responses = new_config_data.get("wake_responses", self.wake_responses)
        self.sleep_responses = new_config_data.get("sleep_responses", self.sleep_responses)
        logger.info("Wake and sleep words/responses updated dynamically.")

    def detect_wake_word(self, text):
        """
        Detect if a wake or sleep word is present in the given text.
        
        Args:
            text (str): The transcribed text to analyze.
        
        Returns:
            tuple: A tuple containing (is_wake_word, confidence, detected_word) or None if no match.
        """
        transcript = text.lower().strip()
        logger.info(f"Transcript received for wake word detection: {transcript}")

        # Check for wake words
        for word in self.wake_words:
            confidence = self.calculate_confidence(word, transcript)
            if confidence >= self.confidence_threshold:
                logger.info(f"Wake word detected: {word} with confidence: {confidence}")
                response = self.choose_response(self.wake_responses)
                self.speak.speak(response)
                return True, confidence, word

        # Check for sleep words
        for word in self.sleep_words:
            confidence = self.calculate_confidence(word, transcript)
            if confidence >= self.confidence_threshold:
                logger.info(f"Sleep word detected: {word} with confidence: {confidence}")
                response = self.choose_response(self.sleep_responses)
                self.speak.speak(response)
                return False, confidence, word

        return None

    def listen_for_wake_word(self, callback):
        """
        Start listening for wake and sleep words, invoking the callback when a match is detected.
        
        Args:
            callback (function): The callback function to be invoked upon detecting a wake or sleep word.
        """
        with self.lock:
            if not self.listening:
                logger.info("Starting to listen for wake or sleep words...")
                self.listening = True

                def local_callback(transcribed_text):
                    result = self.detect_wake_word(transcribed_text)
                    if result is not None:
                        detected_wake_word, confidence, matched_word = result
                        callback(detected_wake_word, confidence, matched_word)

                # Start listening using the microphone input with the provided callback
                self.microphone_input.start_listening(local_callback)

    def stop_listening(self):
        """
        Stop listening for wake and sleep words.
        """
        with self.lock:
            if self.listening:
                logger.info("Stopping wake word detection...")
                self.microphone_input.stop_listening()
                self.listening = False

    def calculate_confidence(self, word, transcript):
        """
        Calculate the confidence score for a detected word in the transcript.
        Use a more advanced text matching algorithm to compute similarity.
        
        Args:
            word (str): The wake or sleep word to check for.
            transcript (str): The transcribed text.
        
        Returns:
            float: A confidence score between 0 and 1.
        """
        similarity = SequenceMatcher(None, word, transcript).ratio()  # Higher ratio means better match
        logger.info(f"Calculated similarity for '{word}' in transcript: {similarity:.2f}")
        return similarity

    def choose_response(self, responses):
        """
        Choose a random response from a list of responses.
        
        Args:
            responses (list): A list of response strings.
        
        Returns:
            str: A randomly selected response, or None if the list is empty.
        """
        return random.choice(responses) if responses else None

    def refresh(self):
        """
        Reload configuration dynamically, useful for hot reloading.
        """
        self.load_config()
        logger.info("Configuration refreshed.")

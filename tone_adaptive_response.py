#responses/mouth/tone_adaptive_response.py
import json
from utils.logger import Logger
import random

from sensors.mouth import Mouth
# Initialize logger
logger = Logger()

class ToneAdaptiveResponse:
    def __init__(self, tts_engine=None, tone_responses_file="config/tone_responses.json"):
        """
        Initialize the ToneAdaptiveResponse class and load tone responses.
        
        :param tts_engine: Optional Mouth engine for speaking responses.
        :param tone_responses_file: Path to the tone responses configuration file.
        """
        self.tts_engine = tts_engine if tts_engine else Mouth()
        self.tone_responses_file = tone_responses_file
        self.tone_responses = {}
        self.load_tone_responses()
        logger.info("Initialized ToneAdaptiveResponse with TTS")

    def load_tone_responses(self):
        """Load predefined tone responses from a JSON file."""
        try:
            with open(self.tone_responses_file, 'r') as f:
                self.tone_responses = json.load(f)
                logger.info(f"Loaded tone responses from {self.tone_responses_file}")
        except FileNotFoundError:
            logger.error(f"Tone responses file not found: {self.tone_responses_file}")
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {self.tone_responses_file}")

    def adapt_tone(self, text, tone, emotion):
        """
        Adapt the response based on tone and emotion, and use TTS to speak the response.
        
        :param text: The default text if tone and emotion do not match.
        :param tone: The tone category (e.g., 'polite', 'angry').
        :param emotion: The specific emotion within the tone category (e.g., 'happy', 'sad').
        :return: The adapted response or the original text if no match is found.
        """
        if tone in self.tone_responses:
            if emotion in self.tone_responses[tone]:
                response = random.choice(self.tone_responses[tone][emotion])
                logger.info(f"Adapted response for tone '{tone}' and emotion '{emotion}': {response}")
            else:
                logger.warning(f"Emotion '{emotion}' not found in tone '{tone}'. Using default text.")
                response = text
        else:
            logger.warning(f"Tone '{tone}' not found. Using default text.")
            response = text
        
        # Use the Mouth engine to speak the response
        self.tts_engine.speak(response)
        return response

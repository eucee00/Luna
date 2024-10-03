# sensors/mouth/mouth.py
import queue
import threading

import pyttsx3

from utils.logger import Logger

logger = Logger()

class Mouth:
    def __init__(self, rate=160, volume=0.8, voice_index=1):
        """
        Initialize the Mouth class with the specified speech rate, volume, and voice.
        :param rate: Speech rate in words per minute.
        :param volume: Volume level (0.0 to 1.0).
        :param voice_index: Index of the voice to use.
        """
        self.engine = pyttsx3.init()
        self.set_rate(rate)
        self.set_volume(volume)
        self.set_voice(voice_index)
        self.speech_queue = queue.Queue()  # Queue to hold speech tasks
        self.processing_thread = threading.Thread(target=self._process_speech_queue, daemon=True)
        self.processing_thread.start()  # Start the background processing thread

    def set_rate(self, rate):
        """Set the speech rate."""
        self.engine.setProperty('rate', rate)

    def set_volume(self, volume):
        """Set the volume level."""
        self.engine.setProperty('volume', volume)

    def set_voice(self, voice_index):
        """Set the voice by index."""
        voices = self.engine.getProperty('voices')
        voice_id = voices[voice_index].id if 0 <= voice_index < len(voices) else voices[1].id
        self.engine.setProperty('voice', voice_id)

    def speak(self, text):
        """Add speech text to the queue for processing."""
        logger.info(f"Queuing speech: {text}")
        self.speech_queue.put(text)

    def _process_speech_queue(self):
        """Continuously process the speech queue in a separate thread."""
        while True:
            text = self.speech_queue.get()
            if text:
                try:
                    logger.info(f"Speaking: {text}")
                    self.engine.say(text)
                    self.engine.runAndWait()  # Block until speech is finished
                except Exception as e:
                    logger.error(f"Error during speech: {e}")
            self.speech_queue.task_done()

    def is_speaking(self):
        """Check if the engine is currently speaking."""
        return self.engine.isBusy()

    def stop(self):
        """Stop the speech engine safely."""
        self.engine.stop()

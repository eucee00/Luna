# sensors/ears/microphone.py
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import sounddevice as sd
import speech_recognition as sr

from utils.logger import Logger

logger = Logger()

class MicrophoneInput:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern to ensure only one instance of MicrophoneInput exists,
        managing hardware resources like the microphone.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, timeout=None, phrase_time_limit=None, noise_adjustment_interval=300):
        """
        Initializes the MicrophoneInput and sets up the speech recognizer and microphone stream.
        
        Args:
            timeout (float): Timeout for audio queue operations.
            phrase_time_limit (float): Time limit for phrases.
            noise_adjustment_interval (int): Interval for adjusting to ambient noise.
        """
        if not hasattr(self, 'initialized'):
            self._initialize(timeout, phrase_time_limit, noise_adjustment_interval)

    def _initialize(self, timeout, phrase_time_limit, noise_adjustment_interval):
        """
        Internal initialization method to set up the recognizer and microphone settings.
        """
        self.recognizer = sr.Recognizer()
        self.running = False
        self.listening = False
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        self.noise_adjustment_interval = noise_adjustment_interval
        self.last_noise_adjustment_time = time.time()
        self.audio_queue = queue.Queue(maxsize=50)
        self.stream = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.initialized = True
        logger.info("MicrophoneInput initialized.")

    def start_listening(self, local_callback):
        """
        Starts the microphone and begins listening for audio input, using a background thread for processing.
        
        Args:
            local_callback (function): A callback function to invoke when transcribed audio is available.
        """
        with self._lock:
            if not self.running:
                logger.info("Starting microphone listening.")
                self.running = True
                self.listening = True

                try:
                    # Set up the audio input stream
                    self.stream = sd.InputStream(callback=self._audio_callback, channels=1, samplerate=16000)
                    self.stream.start()
                    logger.info("Audio stream started successfully.")
                except Exception as e:
                    logger.error(f"Failed to open audio stream: {e}", exc_info=True)
                    self.running = False
                    return

                # Start a background thread to listen for audio
                self.executor.submit(self._listen_loop, local_callback)
                logger.info("Listening loop started in a background thread.")
            else:
                logger.warning("Microphone is already running.")

    def _audio_callback(self, indata, frames, time, status):
        """
        Callback function for audio input stream. Captures incoming audio and places it in the queue for processing.
        
        Args:
            indata: The incoming audio data.
            frames: The number of frames of audio data.
            time: The timestamp for the audio data.
            status: Any status flags (e.g., underflow or overflow).
        """
        if status:
            logger.warning(f"Stream status: {status}")
        try:
            self.audio_queue.put_nowait(indata.copy())
        except queue.Full:
            logger.warning("Audio queue is full. Dropping audio frame.")

    def _listen_loop(self, callback):
        """
        Background thread function that continuously processes audio from the queue for speech recognition.
        
        Args:
            callback (function): A callback function to invoke with transcribed text.
        """
        logger.info("Entering the listening loop...")
        while self.running:
            # Adjust for noise periodically
            if time.time() - self.last_noise_adjustment_time > self.noise_adjustment_interval:
                self.adjust_for_noise()

            try:
                audio_data = self.audio_queue.get(timeout=self.timeout)
            except queue.Empty:
                continue

            transcribed_text = self.process_audio_for_speech_to_text(audio_data)
            if transcribed_text:
                callback(transcribed_text)

        logger.info("Exiting the listening loop.")

    def process_audio_for_speech_to_text(self, audio_data):
        """
        Processes audio data using Google's SpeechRecognition for speech-to-text conversion.
        
        Args:
            audio_data: The audio data from the microphone input.
        
        Returns:
            str: Transcribed text, or None if no transcription is available.
        """
        try:
            # Convert audio data to the correct format for Google Speech Recognition
            audio_data = np.frombuffer(audio_data, dtype=np.float32)
            audio_data = sr.AudioData(audio_data.tobytes(), 16000, 2)
            
            # Perform speech recognition
            text = self.recognizer.recognize_google(audio_data, show_all=False)
            logger.info(f"Transcribed text: {text}")
            return text
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand the audio.")
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service: {e}")
        return None

    def stop_listening(self):
        """
        Stops the microphone and halts listening, ensuring the stream and background thread are closed properly.
        """
        with self._lock:
            if self.running:
                logger.info("Stopping microphone listening...")
                self.running = False

                if self.stream:
                    self.stream.stop()
                    self.stream.close()

                self.executor.shutdown(wait=False)
                logger.info("Microphone stopped listening.")

    def adjust_for_noise(self):
        """
        Adjusts the recognizer's energy threshold for ambient noise.
        """
        logger.info("Adjusting for ambient noise.")
        with self.recognizer as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        self.last_noise_adjustment_time = time.time()

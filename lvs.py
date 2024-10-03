# sensors/lvs.py
import threading
import time
from queue import Empty, Full, Queue

import spacy

from actions.execute import ActionExecutor
from brain.respond.intro import Introduction
from brain.respond.salutations import Salutations
from brain.sensory_inputs.auditory.wake_word_detector import WakeWordDetector
from sensors.ears.microphone import MicrophoneInput
from utils.logger import Logger

# Set up the logger
logger = Logger()

class LunaVoiceSystem:
    def __init__(self, lvs_queue=None, microphone_input=None):
        """
        Initialize the Luna Voice System components.
        This handles wake word detection, salutations, introduction, and returning to sleep after interaction.
        """
        try:
            self.lvs_queue = lvs_queue  # Queue for inter-module communication (to the GUI)
            self.nlp = spacy.load("en_core_web_sm")
            self.microphone_input = microphone_input if microphone_input else MicrophoneInput()

            self.salutations = Salutations()
            self.introduction = Introduction()
            self.wake_word_detector = WakeWordDetector(self.microphone_input)
            self.action_executor = ActionExecutor()
            self.listening_for_commands = False
            self.command_queue = Queue(maxsize=100)  # Command queue with a defined max size
            self.command_processor_thread = None
            self.lock = threading.Lock()  # Lock to manage concurrency and prevent race conditions
            self.user_interaction_thread = None  # Thread to handle post-wake interaction

            logger.info("Luna Voice System initialized successfully.")
        except Exception as e:
            logger.error(f"Initialization error: {e}", exc_info=True)
            raise
    
    def process_luna(self):
        """
        Start the main loop of the Luna Voice System.
        This method initiates wake word detection, salutations, and introduction.
        """
        logger.info("Starting Luna Voice System with Wake Word Detection...")

        def wake_word_callback(detected_wake_word, confidence, matched_word):
            if detected_wake_word:
                logger.info(f"Wake word '{matched_word}' detected with confidence {confidence}.")
                self.greet_user()  # Step 1: Greet user
                self.introduce_user()  # Step 2: Introduction

                # Step 3: Start a timer to return Luna to sleep after 15 seconds of inactivity
                if self.user_interaction_thread and self.user_interaction_thread.is_alive():
                    self.user_interaction_thread.join()  # Ensure the previous timer thread ends
                
                self.user_interaction_thread = threading.Thread(target=self.return_to_sleep_after_timeout, daemon=True)
                self.user_interaction_thread.start()

        # Start the wake word detection
        self.wake_word_detector.listen_for_wake_word(wake_word_callback)

    def return_to_sleep_after_timeout(self):
        """
        Return Luna to sleep after a 15-second timeout following user interaction.
        """
        logger.info("Starting 15-second countdown to return to sleep...")
        time.sleep(15)
        self.stop_listening_for_commands()  # Stops any ongoing listening
        self.wake_word_detector.stop_listening()  # Restart wake word detection
        logger.info("Luna is going back to sleep.")
        self._notify_gui({"type": "luna_asleep"})

    def greet_user(self):
        """
        Greet the user when Luna wakes up.
        """
        try:
            greeting = self.salutations.greetings()  # Get greeting from Salutations class
            self.update_gui_with_response(greeting)
        except Exception as e:
            logger.error(f"Error during user greeting: {e}", exc_info=True)

    def introduce_user(self):
        """
        Introduce Luna to the user after greeting.
        """
        try:
            introduction_message = self.introduction.introduce()  # Get introduction message
            self.update_gui_with_response(introduction_message)
        except Exception as e:
            logger.error(f"Error during user introduction: {e}", exc_info=True)

    def listen_for_commands(self):
        """
        Start listening for user commands and add them to the command queue.
        """
        with self.lock:
            if self.listening_for_commands:
                logger.warning("Already listening for commands.")
                return

            logger.info("Starting to listen for commands...")
            self.listening_for_commands = True

            def command_callback(transcribed_text):
                if transcribed_text:
                    try:
                        self.command_queue.put_nowait(transcribed_text)  # Add command to the queue
                        self.update_gui_with_transcription(transcribed_text)
                    except Full:
                        logger.warning("Command queue is full. Dropping command.")

            # Start the microphone for command recognition
            self.microphone_input.start_listening(command_callback)

            # Start a separate thread to process commands in the background
            self.command_processor_thread = threading.Thread(target=self.process_commands, daemon=True)
            self.command_processor_thread.start()

    def process_commands(self):
        """
        Process commands from the command queue in a background thread.
        Execute intents based on the transcribed text.
        """
        logger.info("Command processor thread started.")
        while self.listening_for_commands:
            try:
                transcribed_text = self.command_queue.get(timeout=0.5)  # Timeout to prevent blocking
                logger.info(f"Processing command: {transcribed_text}")

                intent = self.recognize_intent(transcribed_text)
                response = self.action_executor.execute_intent(intent, transcribed_text)

                # Update the GUI with the response
                self.update_gui_with_response(response)
            except Empty:
                continue  # Queue is empty, wait for the next command
            except Exception as e:
                logger.error(f"Error processing command: {e}", exc_info=True)

        logger.info("Command processor thread ending.")

    def stop_listening_for_commands(self):
        """
        Stop listening for commands, stop microphone input, and clean up resources.
        """
        with self.lock:
            if not self.listening_for_commands:
                logger.info("Not currently listening for commands.")
                return

            logger.info("Stopping listening for commands...")
            self.listening_for_commands = False

            # Stop microphone listening
            self.microphone_input.stop_listening()

            # Ensure the command processor thread has ended
            if self.command_processor_thread and self.command_processor_thread.is_alive():
                logger.info("Waiting for command processor thread to terminate...")
                self.command_processor_thread.join(timeout=5)  # Timeout to avoid blocking indefinitely

            logger.info("Stopped listening for commands.")

    def update_gui_with_transcription(self, transcribed_text):
        """
        Send transcription updates to the GUI.
        """
        self._notify_gui({"type": "transcription", "message": transcribed_text})

    def update_gui_with_response(self, response):
        """
        Send response updates to the GUI.
        """
        self._notify_gui({"type": "response", "message": response})

    def _notify_gui(self, message):
        """
        Utility method to safely notify the GUI.
        """
        if self.lvs_queue:
            try:
                self.lvs_queue.put_nowait(message)
            except Full:
                logger.warning("GUI queue is full. Dropping message.")

# luna.py
import threading
import time
from queue import Queue

from sensors.ears.microphone import MicrophoneInput
from sensors.lvs import LunaVoiceSystem
from utils.logger import Logger

logger = Logger()

class Luna:
    def __init__(self):
        """
        Initialize the Luna system and its components.
        This includes the microphone input, voice system, and GUI communication.
        """
        self._running = True
        self._stop_event = threading.Event()  # Event used to signal stopping the system

        logger.info("Initializing Luna system...")

        try:
            # Initialize the microphone input
            self.microphone_input = MicrophoneInput()

            # Queue for inter-module communication (used to communicate with the GUI)
            self.lvs_queue = Queue()

            # Initialize LunaVoiceSystem
            self.lvs = LunaVoiceSystem(lvs_queue=self.lvs_queue, microphone_input=self.microphone_input)

        except Exception as e:
            logger.error(f"Error during Luna initialization: {e}", exc_info=True)
            self._running = False

    def start(self):
        """
        Start the Luna system by initiating the wake word detection.
        This method keeps the system alive and handles monitoring.
        """
        if self._running:
            logger.info("Starting Luna system...")

            try:
                # Start the voice system (includes wake word detection)
                self.lvs.process_luna()

                # Keep the main thread alive while Luna is running
                while not self._stop_event.is_set():
                    time.sleep(1)  # Sleep for 1 second intervals, waiting for stop signal

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, stopping Luna.")
                self.stop()

            except Exception as e:
                logger.error(f"An error occurred in Luna: {e}", exc_info=True)
                self.stop()

    def stop(self):
        """
        Method to stop the Luna system gracefully.
        Ensures that all components and threads are properly terminated.
        """
        if self._running:
            self._running = False
            self._stop_event.set()  # Signal the stop event to end the main loop
            logger.info("Stopping Luna system...")

            try:
                # Shut down the LunaVoiceSystem
                self.lvs.shutdown()

                logger.info("Luna system stopped successfully.")
            except Exception as e:
                logger.error(f"An error occurred while stopping Luna: {e}", exc_info=True)

    def start_gui(self):
        """
        Start the GUI for Luna in a separate thread to prevent blocking the main system.
        """
        try:
            import sys

            from PyQt5.QtWidgets import QApplication

            from gui import MainWindow  # Import the MainWindow from gui.py

            def run_gui():
                # Set up the PyQt application and start the MainWindow
                app = QApplication(sys.argv)
                gui = MainWindow(self.microphone_input, self.lvs_queue, root=app)
                gui.show()
                sys.exit(app.exec_())

            # Start the GUI in a separate thread
            self.gui_thread = threading.Thread(target=run_gui, daemon=True)
            self.gui_thread.start()

        except Exception as e:
            logger.error(f"Error occurred while starting the GUI: {e}", exc_info=True)
            self.stop()  # Stop the system if GUI initialization fails
            
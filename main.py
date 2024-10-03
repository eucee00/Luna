# main.py
import threading
import tkinter as tk
from luna import Luna
from gui import MainWindow  # Assuming you have a Tkinter-based GUI class in gui.py
from utils.logger import Logger

# Initialize logger for the main system
logger = Logger()

def run_luna_system(luna):
    """
    Start Luna's main processing (e.g., wake word detection, command processing).
    Runs in a separate thread to allow the GUI to remain responsive.
    """
    try:
        logger.info("Starting Luna system...")
        luna.start()  # Start Luna's main loop
    except Exception as e:
        logger.error(f"An error occurred while running Luna: {e}", exc_info=True)
    finally:
        luna.stop()
        logger.info("Luna system has been shut down.")

def on_closing(root, luna, luna_thread):
    """
    Handle the closing of the Tkinter window and stop the Luna system.
    This ensures a graceful shutdown.
    """
    logger.info("Closing the application and shutting down Luna system.")
    root.quit()  # Close the Tkinter main loop
    luna.stop()  # Stop Luna system processing

    # Ensure the Luna thread has fully stopped
    if luna_thread.is_alive():
        logger.info("Waiting for Luna thread to stop...")
        luna_thread.join()  # Wait for the Luna thread to terminate
        logger.info("Luna thread has stopped.")

if __name__ == "__main__":
    try:
        logger.info("Initializing Luna system...")

        # Initialize the Luna system
        luna = Luna()

        # Initialize the Tkinter root and GUI components
        root = tk.Tk()
        gui = MainWindow(root, luna.lvs_queue, luna.microphone_input)  # Pass necessary objects to the GUI

        # Start the Luna system in a separate thread to keep the GUI responsive
        luna_thread = threading.Thread(target=run_luna_system, args=(luna,))
        luna_thread.daemon = True  # Set as daemon to exit when the main program exits
        luna_thread.start()

        # Configure the close behavior of the Tkinter window
        root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, luna, luna_thread))

        # Start the GUI main loop in the main thread
        root.mainloop()

    except Exception as e:
        logger.error(f"An error occurred in the main application: {e}", exc_info=True)
    finally:
        luna.stop()
        logger.info("Luna system has been shut down.")

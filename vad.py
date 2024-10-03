# sensors/ears/vad.py
import librosa
import numpy as np

from sensors.ears.microphone import MicrophoneInput
from utils.logger import Logger

logger = Logger()

class VoiceActivityDetection:
    def __init__(self, threshold=0.02, sample_rate=16000, frame_duration=0.02):
        """
        Initializes the Voice Activity Detection (VAD) system.

        Args:
            threshold (float): Energy threshold to detect voice activity.
            sample_rate (int): The sample rate of audio data.
            frame_duration (float): Duration of each audio frame in seconds (for short-term energy calculation).
        """
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration  # Frame duration in seconds (default 20ms)
        self.frame_length = int(self.sample_rate * self.frame_duration)  # Frame length in samples
        self.microphone_input = MicrophoneInput()
        logger.info("Voice Activity Detection (VAD) initialized.")

    def calculate_short_term_energy(self, audio_frame):
        """
        Calculate the short-term energy of an audio frame.

        Args:
            audio_frame (numpy.ndarray): The audio frame data.

        Returns:
            float: Short-term energy of the frame.
        """
        return np.sum(audio_frame ** 2) / len(audio_frame)

    def detect_voice_activity(self, audio_data):
        """
        Detect whether there is voice activity in the given audio data.

        Args:
            audio_data (numpy.ndarray): The audio data to analyze.

        Returns:
            bool: True if voice activity is detected, False otherwise.
        """
        energy_values = []
        # Split audio data into frames and calculate short-term energy
        for i in range(0, len(audio_data), self.frame_length):
            frame = audio_data[i:i + self.frame_length]
            if len(frame) == 0:
                continue
            energy = self.calculate_short_term_energy(frame)
            energy_values.append(energy)

        average_energy = np.mean(energy_values)
        logger.info(f"Calculated average short-term energy: {average_energy:.6f}")

        return average_energy > self.threshold

    def start_vad(self):
        """
        Continuously monitor for voice activity and log detection results.
        """
        logger.info("Starting advanced VAD...")

        try:
            while True:
                # Capture audio in real-time from the microphone
                audio_data = self.microphone_input.capture_audio()

                if len(audio_data) == 0:
                    logger.warning("No audio data captured.")
                    continue

                # Detect voice activity
                if self.detect_voice_activity(librosa.util.buf_to_float(audio_data)):
                    logger.info("Voice activity detected.")
                else:
                    logger.info("No voice activity detected.")
        except KeyboardInterrupt:
            logger.info("VAD stopped by user.")
        except Exception as e:
            logger.error(f"Error in VAD: {e}")
        finally:
            # Release microphone resources
            self.microphone_input.release()


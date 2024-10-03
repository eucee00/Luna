# brain/sensory_inputs/auditory/sound_analysis.py
import numpy as np
from sensors.ears.microphone import MicrophoneInput
from brain.sensory_inputs.auditory.noise_filter import NoiseFilter
from brain.sensory_inputs.auditory.vad import VoiceActivityDetection
from utils.logger import Logger

logger = Logger()

class SoundAnalysis:
    def __init__(self, noisy_threshold=50):
        """
        Initializes SoundAnalysis for environmental sound observation and analysis.
        
        Args:
            noisy_threshold (int): Threshold above which the environment is considered noisy.
        """
        self.microphone_input = MicrophoneInput()
        self.noise_filter = NoiseFilter()
        self.vad = VoiceActivityDetection()
        self.noisy_threshold = noisy_threshold
        self.sound_level = 0
        self.is_noisy = False
        self.audio_data_store = []  # Store audio data for deeper analysis over time
        logger.info("Advanced Sound Analysis initialized.")

    def calculate_sound_level(self, audio_data):
        """
        Calculate the sound level of the given audio data in decibels.
        
        Args:
            audio_data (numpy.ndarray): The raw audio data.
            
        Returns:
            float: The sound level in dB.
        """
        amplitude = np.mean(np.abs(audio_data))
        sound_level = 20 * np.log10(amplitude) if amplitude > 0 else 0
        logger.info(f"Calculated sound level: {sound_level} dB")
        return sound_level

    def analyze_sound(self):
        """
        Analyzes the sound level in the environment and checks if the environment is noisy.
        """
        logger.info("Starting sound analysis...")
        audio_data = self.microphone_input.start_listening(lambda x: x)

        # Apply noise reduction
        cleaned_audio = self.noise_filter.reduce_noise(audio_data)

        # Calculate sound level
        self.sound_level = self.calculate_sound_level(cleaned_audio)

        # Analyze if the environment is noisy
        if self.sound_level > self.noisy_threshold:
            self.is_noisy = True
            logger.info(f"Environment is noisy. Sound level: {self.sound_level} dB.")
        else:
            self.is_noisy = False
            logger.info(f"Environment is calm. Sound level: {self.sound_level} dB.")

    def long_term_environment_analysis(self):
        """
        Stores sound data over time and analyzes long-term noise patterns.
        """
        logger.info("Starting long-term sound analysis...")
        while True:
            audio_data = self.microphone_input.start_listening(lambda x: x)
            self.audio_data_store.append(audio_data)

            # Perform deeper analysis over time here if necessary
            # Example: detecting patterns in noisy environments over time

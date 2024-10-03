# sensors/ears/noise_filter.py
import noisereduce as nr
import numpy as np
from sensors.ears.microphone import MicrophoneInput
from utils.logger import Logger

logger = Logger()

class NoiseFilter:
    def __init__(self, noise_reduction_factor=0.9, stationary=False, freq_mask_smooth_hz=500, time_mask_smooth_ms=100):
        """
        Initializes an advanced Noise Filter to reduce background noise in captured audio.

        Args:
            noise_reduction_factor (float): The proportion of noise to reduce.
            stationary (bool): Whether the noise is stationary.
            freq_mask_smooth_hz (int): Smoothing parameter for frequency masking.
            time_mask_smooth_ms (int): Smoothing parameter for time masking.
        """
        self.noise_reduction_factor = noise_reduction_factor
        self.stationary = stationary
        self.freq_mask_smooth_hz = freq_mask_smooth_hz
        self.time_mask_smooth_ms = time_mask_smooth_ms
        self.microphone_input = MicrophoneInput()  # Using MicrophoneInput for audio capture
        logger.info("Advanced Noise Filter initialized.")

    def reduce_noise(self, audio_data):
        """
        Reduces noise from the provided audio data using advanced noise reduction techniques.

        Args:
            audio_data (numpy.ndarray): The raw audio data captured from the microphone.

        Returns:
            numpy.ndarray: The noise-reduced audio data.
        """
        try:
            reduced_noise = nr.reduce_noise(y=audio_data, sr=16000, 
                                            prop_decrease=self.noise_reduction_factor, 
                                            stationary=self.stationary,
                                            freq_mask_smooth_hz=self.freq_mask_smooth_hz,
                                            time_mask_smooth_ms=self.time_mask_smooth_ms)
            logger.info("Noise reduction successful.")
            return reduced_noise
        except Exception as e:
            logger.error(f"Error reducing noise: {e}")
            return audio_data

    def capture_and_reduce_noise(self):
        """
        Captures audio using the microphone and applies noise reduction.

        Returns:
            numpy.ndarray: Noise-reduced audio data.
        """
        try:
            audio_data = self.microphone_input.start_listening(lambda x: x)
            reduced_audio = self.reduce_noise(audio_data)
            return reduced_audio
        except Exception as e:
            logger.error(f"Error capturing and reducing noise: {e}")
            return None
        
    def calculate_amplitude_reduction(self, audio_data):
        """
        Calculates the amplitude reduction factor after noise reduction.

        Args:
            audio_data (speech_recognition.AudioData or numpy.ndarray): The audio data to process.

        Returns:
            float: The amplitude reduction factor.
        """
        if isinstance(audio_data, sr.AudioData):
            original_amplitude = np.mean(np.abs(np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)))
        elif isinstance(audio_data, np.ndarray):
            original_amplitude = np.mean(np.abs(audio_data))
        else:
            raise TypeError("audio_data must be either speech_recognition.AudioData or numpy.ndarray")

        filtered_audio = self.reduce_noise(audio_data)

        if isinstance(filtered_audio, sr.AudioData):
            filtered_amplitude = np.mean(np.abs(np.frombuffer(filtered_audio.get_raw_data(), dtype=np.int16)))
        elif isinstance(filtered_audio, np.ndarray):
            filtered_amplitude = np.mean(np.abs(filtered_audio))
        else:
            raise TypeError("filtered_audio must be either speech_recognition.AudioData or numpy.ndarray")
        
        if original_amplitude == 0:
            return 0

        reduction_factor = filtered_amplitude / original_amplitude
        return reduction_factor
    
    def get_amplitude(self, audio_data):
        """
        Calculates the amplitude of the provided audio data.

        Args:
            audio_data (speech_recognition.AudioData or numpy.ndarray): The audio data to process.
            
        Returns:
            float: The amplitude of the audio data.
        """
        if isinstance(audio_data, sr.AudioData):
            return np.mean(np.abs(np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)))
        elif isinstance(audio_data, np.ndarray):
            return np.mean(np.abs(audio_data))
        else:
            raise TypeError("audio_data must be either speech_recognition.AudioData or numpy.ndarray")

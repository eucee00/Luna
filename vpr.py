# sensors/ears/vpr.py
import os

import joblib
import librosa
import numpy as np
import soundfile as sf
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from sensors.ears.microphone import MicrophoneInput
from utils.logger import Logger

logger = Logger()

class VoiceProfileRecognition:
    def __init__(self, profile_dir='config/voice_profiles', model_path='config/voice_model.pkl', timeout=10):
        """
        Initialize the VoiceProfileRecognition system.
        :param profile_dir: Directory to store voice profiles.
        :param model_path: Path to store/load the trained model.
        :param timeout: Microphone timeout duration for capturing audio.
        """
        self.microphone_input = MicrophoneInput(timeout=timeout)
        self.profile_dir = profile_dir
        self.model_path = model_path
        self.model = make_pipeline(StandardScaler(), SVC(kernel='linear', probability=True))
        self.labels = []

        logger.info("Voice profile recognition system initialized.")

        # Load existing model if available, otherwise prepare for new training
        if not self.load_model():
            logger.info("No pre-trained model found. Will train a new one when profiles are added.")

    def load_voice_profiles(self):
        """
        Load pre-trained voice profiles from the profile directory and assign labels.
        :return: voice_profiles (np.ndarray), labels (np.ndarray)
        """
        voice_profiles = []
        labels = []
        logger.info(f"Loading voice profiles from {self.profile_dir}")

        if not os.path.exists(self.profile_dir):
            logger.error(f"Voice profile directory {self.profile_dir} does not exist.")
            return np.array([]), np.array([])

        for voice_profile_file in os.listdir(self.profile_dir):
            file_path = os.path.join(self.profile_dir, voice_profile_file)
            try:
                # Load the audio file and extract the MFCC features
                voice_profile, _ = librosa.load(file_path, sr=16000)
                mfccs = self.extract_features(voice_profile)
                voice_profiles.append(mfccs)
                labels.append(len(labels))  # Assign a numerical label
                self.labels.append(os.path.splitext(voice_profile_file)[0])  # Store filename without extension as label
                logger.info(f"Loaded and processed {voice_profile_file}")
            except Exception as e:
                logger.error(f"Error loading {voice_profile_file}: {str(e)}")

        return np.array(voice_profiles), np.array(labels)

    def extract_features(self, audio_data):
        """
        Extract MFCC features from audio data.
        :param audio_data: Raw audio data.
        :return: MFCC feature vector (numpy.ndarray)
        """
        try:
            mfccs = librosa.feature.mfcc(y=audio_data, sr=16000, n_mfcc=13)
            return np.mean(mfccs.T, axis=0)  # Average MFCC coefficients across frames
        except Exception as e:
            logger.error(f"Error extracting MFCC features: {str(e)}")
            return np.zeros(13)  # Return a dummy vector in case of error

    def train_model(self):
        """
        Train the model using pre-loaded voice profiles and save it.
        """
        try:
            voice_profiles, labels = self.load_voice_profiles()
            if len(voice_profiles) > 0:
                # Train the SVM model using voice profiles and their labels
                self.model.fit(voice_profiles, labels)
                logger.info("Voice profile model trained successfully.")
                # Save the trained model
                self.save_model()
            else:
                logger.warning("No voice profiles found. Model training skipped.")
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")

    def save_model(self):
        """
        Save the trained model to disk.
        """
        try:
            joblib.dump((self.model, self.labels), self.model_path)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")

    def load_model(self):
        """
        Load the trained model from disk, if available.
        :return: True if model loaded successfully, False otherwise
        """
        if os.path.exists(self.model_path):
            try:
                self.model, self.labels = joblib.load(self.model_path)
                logger.info(f"Loaded pre-trained model from {self.model_path}")
                return True
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
        else:
            logger.warning(f"Model not found at {self.model_path}. A new one will be trained.")
        return False

    async def authenticate_user(self):
        """
        Capture audio using MicrophoneInput and authenticate the user based on their voice profile.
        :return: Predicted user label and confidence score (or None, 0.0 if no match)
        """
        try:
            raw_audio = await self.microphone_input.listen_for_audio()
            if raw_audio is None:
                logger.error("Failed to capture audio for authentication.")
                return None, 0.0

            # Extract features from the captured audio
            features = self.extract_features(librosa.util.buf_to_float(raw_audio))

            # Predict the speaker based on extracted features
            prediction = self.model.predict_proba([features])[0]
            predicted_label = np.argmax(prediction)
            confidence = prediction[predicted_label]

            # Get the predicted user's profile name (file name)
            predicted_user = self.labels[predicted_label]
            logger.info(f"Authentication result: {predicted_user} with confidence {confidence:.2f}")

            return predicted_user, confidence
        except Exception as e:
            logger.error(f"Error during user authentication: {str(e)}")
            return None, 0.0

    def store_user_data(self, voice_features, user_name):
        """
        Store a new user's voice profile data and re-train the model with the new data.
        :param voice_features: The raw audio data of the user's voice.
        :param user_name: The user's name (label for the voice profile).
        """
        try:
            # Ensure profile directory exists
            os.makedirs(self.profile_dir, exist_ok=True)

            # Create a file for the new user's voice profile
            profile_path = os.path.join(self.profile_dir, f"{user_name}.wav")

            # Use soundfile to save the audio data (voice_features is expected to be raw audio)
            sf.write(profile_path, voice_features, samplerate=16000)
            logger.info(f"Stored new voice profile for {user_name} at {profile_path}")

            # Re-train the model with the new voice profile
            self.train_model()
        except Exception as e:
            logger.error(f"Error storing user data: {str(e)}")

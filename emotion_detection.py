import numpy as np
import cv2
from sensors.eyes.camera_input import CameraInput
from brain.sensory_inputs.visual.facial_recognition import FaceRecognition
from utils.logger import Logger
from utils.async_task_manager import AsyncTaskManager

logger = Logger()

class EmotionDetection:
    def __init__(self, model_path):
        """
        Initialize the EmotionDetection system, load the emotion detection model, and set up camera input.
        Args:
            model_path (str): Path to the trained emotion detection model.
        """
        self.camera_input = CameraInput()
        self.face_recognition = FaceRecognition()  # Reusing face recognition module to detect faces
        self.logger = Logger(name="EmotionDetection")
        self.model = self.load_model(model_path)
        self.task_manager = AsyncTaskManager(max_workers=2)
        self.task_manager.start()

        # Emotion map corresponding to model predictions
        self.emotion_map = {
            0: "Angry",
            1: "Disgust",
            2: "Fear",
            3: "Happy",
            4: "Sad",
            5: "Surprise",
            6: "Neutral"
        }
        self.logger.info("EmotionDetection initialized.")

    def load_model(self, model_path):
        """
        Load the pre-trained emotion detection model (CNN or other deep learning models).
        Args:
            model_path (str): Path to the trained model.

        Returns:
            model: Loaded deep learning model.
        """
        try:
            # Assuming the model is a deep learning model (e.g., Keras, PyTorch, TensorFlow)
            model = cv2.dnn.readNetFromONNX(model_path)  # Example with ONNX model loading
            self.logger.info("Emotion detection model loaded successfully.")
            return model
        except Exception as e:
            self.logger.error(f"Error loading model from {model_path}: {e}")
            return None

    def detect_emotions_async(self):
        """
        Start asynchronous emotion detection using the AsyncTaskManager.
        """
        self.logger.info("Starting asynchronous emotion detection.")
        self.task_manager.add_task(self.detect_emotions, priority=1)

    def detect_emotions(self):
        """
        Detect emotions in real-time using the camera feed.
        Captures the frame, detects faces, and applies the emotion detection model.
        """
        try:
            while True:
                # Capture frame from camera
                frame = self.camera_input.capture_frame()
                if frame is None:
                    self.logger.error("Failed to capture frame from camera.")
                    continue

                # Detect faces in the frame using face recognition
                faces = self.face_recognition.detect_face(frame)

                # Process each detected face for emotion recognition
                for (x, y, w, h) in faces:
                    face_roi = frame[y:y+h, x:x+w]
                    emotion = self.process_face_for_emotion(face_roi)

                    if emotion:
                        # Draw bounding box and emotion label on the frame
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, emotion, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Display the frame with emotion annotations
                cv2.imshow("Emotion Detection", frame)

                # Break the loop if 'q' key is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            self.logger.error(f"Error during emotion detection: {e}")
        finally:
            # Release resources
            self.camera_input.release()
            cv2.destroyAllWindows()

    def process_face_for_emotion(self, face_roi):
        """
        Preprocess the face and use the model to predict the emotion.
        
        Args:
            face_roi (numpy.ndarray): The region of interest (face) from the detected face.

        Returns:
            str: The predicted emotion or None if no emotion is detected.
        """
        try:
            # Preprocess the face ROI (resize, grayscale, normalize)
            face_roi = cv2.resize(face_roi, (48, 48))
            face_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            face_roi = face_roi.astype("float32") / 255.0  # Normalize pixel values

            # Reshape for model input
            face_input = np.expand_dims(face_roi, axis=0)  # Add batch dimension
            face_input = np.expand_dims(face_input, axis=-1)  # Add channel dimension

            # Perform emotion prediction
            self.model.setInput(face_input)
            prediction = self.model.forward()

            # Extract the emotion label with the highest confidence
            emotion_index = np.argmax(prediction)
            emotion = self.emotion_map[emotion_index]

            self.logger.info(f"Detected emotion: {emotion}")
            return emotion

        except Exception as e:
            self.logger.error(f"Error processing face for emotion: {e}")
            return None

    def stop_emotion_detection(self):
        """
        Stop any ongoing emotion detection tasks.
        """
        try:
            self.logger.info("Stopping emotion detection tasks...")
            self.task_manager.stop()
        except Exception as e:
            self.logger.error(f"Error stopping emotion detection: {e}")


import os
import cv2
import numpy as np
from sensors.eyes.camera_input import CameraInput
from utils.logger import Logger
from utils.async_task_manager import AsyncTaskManager

logger = Logger()

class FaceRecognition:
    def __init__(self, known_faces_dir="brain/sensory_inputs/visual/known_faces"):
        """
        Initialize the face recognition system, load the Haar Cascade for face detection,
        and load the known faces for recognition.
        """
        self.camera_input = CameraInput()
        self.face_cascade = cv2.CascadeClassifier(os.path.join(os.path.dirname(__file__), "haarcascade_frontalface_default.xml"))
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.logger = Logger(name="FaceRecognition")
        self.task_manager = AsyncTaskManager(max_workers=3)
        self.task_manager.start()

        # Load known faces from the directory
        self.known_faces_dir = known_faces_dir
        self.known_face_names = []
        self.load_known_faces(self.known_faces_dir)
        self.logger.info("FaceRecognition initialized and known faces loaded.")
        
    def load_known_faces(self, known_faces_dir):
        """
        Load known faces and labels from the specified directory.
        Train the face recognizer model with the loaded faces.
        """
        faces = []
        labels = []
        self.known_face_names = []

        for label, filename in enumerate(os.listdir(known_faces_dir)):
            if filename.endswith(".jpg") or filename.endswith(".png"):
                image_path = os.path.join(known_faces_dir, filename)
                image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                faces.append(image)
                labels.append(label)
                self.known_face_names.append(os.path.splitext(filename)[0])
                self.logger.info(f"Loaded face data for {os.path.splitext(filename)[0]}")

        if faces and labels:
            self.recognizer.train(faces, np.array(labels))
            self.logger.info("Face recognition model trained with known faces.")
        else:
            self.logger.warning("No known faces found, model not trained.")

    def detect_face(self):
        """
        Detect a face in the frame using the Haar Cascade face detector.
        Returns the region of interest (ROI) of the detected face.
        """
        face_found = False
        face_roi = None

        try:
            while not face_found:
                ret, frame = self.camera_input.get_frame()
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                for (x, y, w, h) in faces:
                    face_found = True
                    face_roi = gray_frame[y:y+h, x:x+w]
                    self.logger.info("Face detected.")
                    break

        except Exception as e:
            self.logger.error(f"Error detecting face: {e}")

        return face_roi

    def collect_face_data(self, face_roi):
        """
        Collect the facial data from the detected face region of interest (ROI).
        
        Parameters:
        - face_roi: The region of interest of the detected face.
        
        Returns:
        - numpy.ndarray: The processed face data suitable for recognition.
        """
        try:
            face_data = np.array(face_roi).reshape(-1, 1).astype(np.float32)
            self.logger.info("Face data collected.")
            return face_data
        except Exception as e:
            self.logger.error(f"Error collecting face data: {e}")
            return None

    def store_face_data(self, face_roi, label):
        """
        Store the face data by updating the face recognizer model with new data.
        
        Parameters:
        - face_roi: The region of interest of the detected face.
        - label: The label/name of the person.
        """
        try:
            face_data = self.collect_face_data(face_roi)
            if face_data is not None:
                self.recognizer.update([face_data], [label])
                self.logger.info(f"Stored new face data for {label}.")
            else:
                self.logger.error("Failed to collect face data for storing.")
        except Exception as e:
            self.logger.error(f"Error storing face data: {e}")

    def recognize_face(self, face_roi):
        """
        Recognize the face by comparing it with known faces.
        
        Parameters:
        - face_roi: The region of interest of the detected face.
        
        Returns:
        - str: The name of the recognized person or None if unrecognized.
        """
        try:
            face_data = self.collect_face_data(face_roi)
            if face_data is None:
                return None

            label, confidence = self.recognizer.predict(face_data)
            if confidence < 100:
                name = self.known_face_names[label]
                self.logger.info(f"Recognized face as {name} with confidence {confidence}.")
                return name
            else:
                self.logger.info(f"Face not recognized with confidence {confidence}.")
                return None
        except Exception as e:
            self.logger.error(f"Error recognizing face: {e}")
            return None

    def recognize_face_async(self):
        """
        Asynchronously recognize faces using the AsyncTaskManager.
        """
        self.logger.info("Starting asynchronous face recognition...")
        self.task_manager.add_task(self._recognize_face_task, priority=1)

    def _recognize_face_task(self):
        """
        The internal task for asynchronously recognizing a face.
        """
        try:
            while True:
                face_roi = self.detect_face()
                if face_roi is not None:
                    recognized_face = self.recognize_face(face_roi)
                    if recognized_face:
                        self.logger.info(f"Recognized face: {recognized_face}")
                    else:
                        self.logger.info("Face not recognized.")
        except Exception as e:
            self.logger.error(f"Error in asynchronous face recognition task: {e}")

    def stop_face_recognition(self):
        """
        Stop any ongoing face recognition tasks.
        """
        try:
            self.logger.info("Stopping face recognition tasks...")
            self.task_manager.stop()
        except Exception as e:
            self.logger.error(f"Error stopping face recognition tasks: {e}")

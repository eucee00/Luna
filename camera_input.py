# sensors/eyes/camera_input.py
import os

import cv2

from utils.logger import Logger

logger = Logger()

class CameraInput:
    def __init__(self, camera_index=0):
        """
        Initialize the CameraInput class.
        :param camera_index: Index of the camera to use.
        """
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Load pre-trained face and eye detection models
        haarcascade_path = os.path.join(os.path.dirname(__file__), "haarcascade_frontalface_default.xml")
        eye_cascade_path = os.path.join(os.path.dirname(__file__), "haarcascade_eye.xml")
        
        if not os.path.exists(haarcascade_path) or not os.path.exists(eye_cascade_path):
            logger.error("Luna's vision resources (haarcascades) are missing.")
            raise FileNotFoundError("Luna is Temporarily Blind - Haarcascade files are missing.")
        
        self.face_cascade = cv2.CascadeClassifier(haarcascade_path)
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

        if not self.cap.isOpened():
            logger.error(f"Luna Unable to access the camera at index {self.camera_index}.")
            raise RuntimeError("Luna is Temporarily Blind - Camera not accessible.")
        logger.info(f"Luna's visual system initialized using camera index {self.camera_index}.")

    def capture_frame(self):
        """
        Capture a single frame from the camera.
        :return: Captured frame or None if unsuccessful.
        """
        ret, frame = self.cap.read()
        if not ret:
            logger.error("Luna Unable to capture frames right now.")
            return None
        return frame

    def display_frame(self, frame):
        """
        Display the captured frame in a window.
        :param frame: The frame to display.
        """
        if frame is None:
            logger.error("Luna is unable to display an empty frame.")
            return
        
        cv2.imshow('Luna Seeing', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            logger.info("Luna is quitting the vision window.")
            self.release_camera()

    def find_faces(self, frame):
        """
        Detect faces in the provided frame.
        :param frame: The frame in which to detect faces.
        :return: List of detected faces as rectangles.
        """
        if frame is None:
            logger.error("Luna cannot detect faces in an empty frame.")
            return []
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if not faces.any():
            logger.info("No faces detected in the current frame.")
        else:
            logger.info(f"Detected {len(faces)} face(s) in the current frame.")
        return faces

    def detect_facial_features(self, frame, faces):
        """
        Detect facial features (like eyes) in the detected faces.
        :param frame: The frame containing the faces.
        :param faces: List of face bounding boxes.
        :return: Frame with facial features highlighted.
        """
        if frame is None or len(faces) == 0:
            logger.error("Luna cannot detect facial features without faces.")
            return frame
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        for (x, y, w, h) in faces:
            face_roi = frame[y:y+h, x:x+w]
            eyes = self.eye_cascade.detectMultiScale(cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY), scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(face_roi, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        logger.info("Luna detected facial features in the frame.")
        return frame

    def take_picture(self, frame, file_name="luna_image.jpg"):
        """
        Save the captured frame as an image.
        :param frame: Frame to save as an image.
        :param file_name: File name for the saved image.
        :return: Path to the saved image.
        """
        if frame is None:
            logger.error("Luna cannot take a picture of an empty frame.")
            return None
        
        cv2.imwrite(file_name, frame)
        logger.info(f"Luna has saved a picture to {file_name}.")
        return file_name

    def release_camera(self):
        """
        Release the camera and destroy any OpenCV windows.
        """
        if self.cap.isOpened():
            self.cap.release()
            logger.info("Luna has released the camera resource.")
        cv2.destroyAllWindows()
        logger.info("All vision-related windows have been closed.")

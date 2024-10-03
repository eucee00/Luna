import cv2
import mediapipe as mp
import numpy as np
from utils.logger import Logger
from sensors.eyes.camera_input import CameraInput
from utils.async_task_manager import AsyncTaskManager

# Initialize logger for body language analysis
logger = Logger(name="BodyLanguageAnalysis")

class BodyLanguageAnalysis:
    def __init__(self):
        """
        Initialize MediaPipe Pose module, camera input, and async task manager.
        """
        self.mp_pose = mp.solutions.pose
        self.pose_drawing_spec = mp.solutions.drawing_utils.DrawingSpec(thickness=2, circle_radius=2)
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.cap = CameraInput()  # Custom CameraInput class for video stream capture
        self.logger = logger

        # Initialize AsyncTaskManager for real-time body language detection
        self.task_manager = AsyncTaskManager(max_workers=2)
        self.task_manager.start()

    def train_body_patterns(self):
        """
        Train Luna to understand body patterns using camera input data.
        This function can be used to collect and label body poses for training.
        """
        # TODO: Implement a training mechanism to collect and label body pose data
        self.logger.info("Training body patterns is not yet implemented.")

    def detect_body_language_async(self):
        """
        Detect body language asynchronously using the AsyncTaskManager.
        """
        self.logger.info("Starting asynchronous body language detection.")
        self.task_manager.add_task(self.detect_body_language, priority=1)

    def detect_body_language(self):
        """
        Detect body language patterns in real-time using camera input.
        Uses MediaPipe Pose to extract pose landmarks and determine specific gestures or postures.
        """
        try:
            while True:
                # Capture frame from the camera
                frame = self.cap.capture_frame()
                if frame is None:
                    self.logger.error("No frame captured from the camera.")
                    continue

                # Convert the image to RGB as required by MediaPipe
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Process the image and detect pose landmarks
                results = self.pose.process(image_rgb)

                # Check if pose landmarks are detected
                if results.pose_landmarks:
                    # Analyze landmarks for specific body language patterns
                    self.analyze_pose_landmarks(results.pose_landmarks)

                    # Draw pose landmarks on the image for visualization
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame, 
                        results.pose_landmarks, 
                        self.mp_pose.POSE_CONNECTIONS, 
                        self.pose_drawing_spec
                    )

                # Display the frame (can be omitted in a headless setup)
                cv2.imshow('Body Language Analysis', frame)

                # Break the loop if 'q' key is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            self.logger.error(f"An error occurred during body language detection: {e}")
        finally:
            # Release resources
            self.cap.release()
            cv2.destroyAllWindows()

    def analyze_pose_landmarks(self, landmarks):
        """
        Analyze pose landmarks to detect specific body language patterns.
        
        Parameters:
        - landmarks: Pose landmarks detected by MediaPipe.
        """
        try:
            if self.are_arms_raised(landmarks):
                self.logger.info("Arms raised detected.")
            elif self.are_arms_crossed(landmarks):
                self.logger.info("Arms crossed detected.")
            elif self.are_shoulders_tilted(landmarks):
                self.logger.info("Shoulders tilted detected.")
            else:
                self.logger.info("No specific body language pattern detected.")
        except Exception as e:
            self.logger.error(f"Error analyzing pose landmarks: {e}")

    def are_arms_raised(self, landmarks):
        """
        Determine if the arms are raised above the head based on pose landmarks.
        
        Parameters:
        - landmarks: Pose landmarks detected by MediaPipe.
        
        Returns:
        - bool: True if arms are raised, False otherwise.
        """
        try:
            left_shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            left_wrist = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST]
            right_shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            right_wrist = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST]

            # Check if wrists are above shoulders (y-coordinate in image, smaller is higher)
            return left_wrist.y < left_shoulder.y and right_wrist.y < right_shoulder.y
        except Exception as e:
            self.logger.error(f"Error detecting arms raised: {e}")
            return False

    def are_arms_crossed(self, landmarks):
        """
        Determine if arms are crossed in front of the body based on pose landmarks.
        
        Parameters:
        - landmarks: Pose landmarks detected by MediaPipe.
        
        Returns:
        - bool: True if arms are crossed, False otherwise.
        """
        try:
            left_wrist = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST]
            right_wrist = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST]
            left_elbow = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_ELBOW]
            right_elbow = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_ELBOW]

            # Check if wrists are positioned in front of the chest (crossing over)
            return left_wrist.x > right_elbow.x and right_wrist.x < left_elbow.x
        except Exception as e:
            self.logger.error(f"Error detecting arms crossed: {e}")
            return False

    def are_shoulders_tilted(self, landmarks):
        """
        Determine if shoulders are tilted based on pose landmarks.
        
        Parameters:
        - landmarks: Pose landmarks detected by MediaPipe.
        
        Returns:
        - bool: True if shoulders are tilted, False otherwise.
        """
        try:
            left_shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]

            # Check if the difference between shoulders' y-coordinates is significant
            return abs(left_shoulder.y - right_shoulder.y) > 0.1
        except Exception as e:
            self.logger.error(f"Error detecting shoulders tilted: {e}")
            return False

    def stop_body_language_detection(self):
        """
        Stop any ongoing body language detection tasks.
        """
        try:
            self.logger.info("Stopping body language detection tasks...")
            self.task_manager.stop()
        except Exception as e:
            self.logger.error(f"Error stopping body language detection tasks: {e}")


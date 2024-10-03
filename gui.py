# gui.py
import math
import queue
import random
import sys
import time
from threading import Event, Thread

import librosa
import numpy as np
from PyQt5.QtCore import QRectF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen, QRadialGradient
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from sensors.ears.microphone import \
    MicrophoneInput  # Importing the MicrophoneInput


class NebulaParticle:
    def __init__(self, canvas, x, y, vx, vy, size=5, color='lime'):
        """Initialize particle with position, velocity, size, and color."""
        self.canvas = canvas
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.is_active = False

    def set_active(self, active):
        """Activate or deactivate particle behavior based on state."""
        self.is_active = active
        self.color = 'yellow' if active else 'cyan'

    def move(self, amplitude):
        """Move particles based on amplitude from audio input."""
        self.scale_size(amplitude)

        if self.is_active:
            self.vx += random.uniform(-0.3, 0.3)
            self.vy += random.uniform(-0.3, 0.3)
            self.x += self.vx
            self.y += self.vy

            # Boundary checks for the particle movement
            if self.x < 0:
                self.x = 0
                self.vx *= -1
            elif self.x > 800:
                self.x = 800
                self.vx *= -1

            if self.y < 0:
                self.y = 0
                self.vy *= -1
            elif self.y > 400:
                self.y = 400
                self.vy *= -1

    def scale_size(self, amplitude):
        """Scale particle size based on the audio amplitude."""
        self.size = max(2, min(30, amplitude // 300))  # Adjusted size scaling for a glowing nebula effect


class NebulaNetwork(QWidget):
    def __init__(self):
        """Initialize nebula particle network for visualization."""
        super().__init__()
        self.particles = [
            NebulaParticle(self, random.randint(0, 800), random.randint(0, 400),
                           random.uniform(-2, 2), random.uniform(-2, 2))
            for _ in range(70)  # Increased particle count for nebula effect
        ]
        self.amplitude = 0
        self.lines = []

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(50)  # Update every 50ms for smooth particle animation

    def paintEvent(self, event):
        """Handle painting of particles and lines to simulate a nebula."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw particles with radial gradients to simulate glowing nebula particles
        for particle in self.particles:
            gradient = QRadialGradient(particle.x + particle.size / 2, particle.y + particle.size / 2, particle.size)
            gradient.setColorAt(0, QColor(255, 255, 255, 150))  # Inner glow
            gradient.setColorAt(1, QColor(0, 255, 255, 50))  # Outer cyan glow
            brush = QBrush(gradient)
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(particle.x, particle.y, particle.size, particle.size))

        # Draw connecting lines between particles for the nebula's gaseous effect
        for line in self.lines:
            pen = QPen(QColor('purple'), 0.8)
            painter.setPen(pen)
            painter.drawLine(line[0], line[1])

    def update_particles(self):
        """Update particle positions and redraw connections."""
        for particle in self.particles:
            particle.move(self.amplitude)

        self.update_lines()
        self.update()  # Trigger repaint to redraw particles

    def update_lines(self):
        """Draw lines between particles that are within a certain distance of each other."""
        self.lines.clear()

        for i, p1 in enumerate(self.particles):
            for p2 in self.particles[i + 1:]:
                distance = math.hypot(p1.x - p2.x, p1.y - p2.y)
                if distance < 150:  # Adjusted distance for more connections
                    self.lines.append(((p1.x + p1.size / 2, p1.y + p1.size / 2),
                                       (p2.x + p2.size / 2, p2.y + p2.size / 2)))

    def update_particle_behavior(self, mid_energy, treble_energy):
        """Update particle behavior based on audio energy levels."""
        for particle in self.particles:
            if mid_energy > 1000:  # Example threshold for mid frequencies
                particle.set_active(True)
            else:
                particle.set_active(False)

            if treble_energy > 500:  # Example threshold for treble frequencies
                particle.color = 'magenta'
            else:
                particle.color = 'cyan'


class AudioThread(Thread):
    def __init__(self, microphone_input, nebula_network, stop_event):
        """Initialize the thread to handle real-time audio input."""
        super().__init__(daemon=True)
        self.microphone_input = microphone_input
        self.nebula_network = nebula_network
        self.stop_event = stop_event

    def run(self):
        """Continuously capture audio and update particle animation based on frequency bands."""
        while not self.stop_event.is_set():
            try:
                # Get the audio signal from the microphone input
                audio_data = self.microphone_input.get_current_audio_data()

                # Use librosa to analyze the audio signal
                if len(audio_data) > 0:
                    # Compute the short-time Fourier transform (STFT)
                    stft = np.abs(librosa.stft(audio_data))

                    # Summarize the amplitude of specific frequency bands (e.g., bass, mid, treble)
                    bass_energy = np.sum(stft[:50])
                    mid_energy = np.sum(stft[50:200])
                    treble_energy = np.sum(stft[200:])

                    # Use different energy levels to affect the animation
                    self.nebula_network.amplitude = bass_energy
                    self.nebula_network.update_particle_behavior(mid_energy, treble_energy)

                time.sleep(0.05)
            except Exception as e:
                print(f"Error in AudioThread: {e}")


class MainWindow(QWidget):
    def __init__(self, microphone_input, lvs_queue, root):
        """Initialize the main window for the GUI."""
        super().__init__()

        self.setWindowTitle('Luna Voice System - Orion Nebula')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: black;")

        layout = QVBoxLayout()

        # Title
        self.title_label = QLabel("L . V . S - Orion Nebula", self)
        self.title_label.setFont(QFont("Futura", 36, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # Nebula Animation Network
        self.nebula_network = NebulaNetwork()
        layout.addWidget(self.nebula_network)

        # Status Labels
        self.wake_word_label = QLabel("Wake Word: Not Detected", self)
        self.wake_word_label.setFont(QFont("Arial", 12))
        self.wake_word_label.setStyleSheet("color: white;")
        layout.addWidget(self.wake_word_label)

        self.status_label = QLabel("Listening...", self)
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("color: lightgreen;")
        layout.addWidget(self.status_label)

        # Set layout
        self.setLayout(layout)

        # Audio input and animation update
        self.microphone_input = microphone_input
        self.lvs_queue = lvs_queue
        self.stop_event = Event()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_animation)
        self.update_timer.start(50)  # Update every 50ms
        self.root = root
        self.audio_thread = AudioThread(self.microphone_input, self.nebula_network, self.stop_event)
        self.audio_thread.start()
        self.lvs_queue.put("start")
        self.show()

    def update_animation(self):
        """Update the nebula animation and GUI elements."""
        try:
            if not self.lvs_queue.empty():
                try:
                    data = self.lvs_queue.get_nowait()
                    if 'wake_word' in data:
                        self.wake_word_label.setText(f"Wake Word: {data['wake_word']}")
                        self.status_label.setText("Listening...")
                except queue.Empty:
                    pass
            else:
                self.wake_word_label.setText("Wake Word: Not Detected")
                self.status_label.setText("Listening...")

            self.nebula_network.update()  # Update particle animation
        except Exception as e:
            print(f"Error in update_animation: {e}")

    def keyPressEvent(self, event):
        """Handle key press event to stop the animation."""
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        """Handle closing the window and cleaning up resources."""
        self.stop_event.set()  # Stop the audio thread
        self.audio_thread.join()  # Ensure thread terminates
        self.microphone_input.close()  # Ensure the microphone stream is properly closed
        self.root.quit()  # Ensure the application quits
        event.accept()

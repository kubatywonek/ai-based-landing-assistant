import matplotlib.pyplot as plt
import os
from datetime import datetime

"""
Simple telemetry class to log and save flight data for analysis.
Currently logs step, altitude, aileron, elevator, pitch, and roll.
"""
class Telemetry:
    
    def __init__(self):
        self.step = []
        self.alt = []
        self.aileron = []
        self.elevator = []
        self.pitch = []
        self.roll = []
    
    def log(self, entry):
        self.step.append(entry.get('step', 0))
        self.alt.append(entry.get('alt', 0))
        self.aileron.append(entry.get('aileron', 0))
        self.elevator.append(entry.get('elevator', 0))
        self.pitch.append(entry.get('pitch', 0))
        self.roll.append(entry.get('roll', 0))
    
    def save(self):
        local_path = os.path.dirname(__file__)
        directory = os.path.join(local_path, "telemetry_logs")
        os.makedirs(directory, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        full_path = os.path.join(directory, f"telemetry_log-{timestamp}.csv")
        with open(full_path, 'w') as f:
            f.write("step,altitude,aileron,elevator,pitch,roll\n")
            for i in range(len(self.step)):
                f.write(f"{self.step[i]},{self.alt[i]},{self.aileron[i]},{self.elevator[i]},{self.pitch[i]},{self.roll[i]}\n")
    
    def plot(self):
        fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        fig.canvas.manager.set_window_title("Agent's flight telemetry report")

        # Altitude plot
        axs[0].plot(self.step, self.alt, color='blue', linewidth=2)
        axs[0].set_ylabel("Altitude [ft]")
        axs[0].set_xlabel("Flight time [steps]")
        axs[0].set_title("Glide path")
        axs[0].grid(True)

        # Control surfaces plot
        axs[1].plot(self.step, self.aileron, color='green', label='Aileron', alpha=0.8)
        axs[1].plot(self.step, self.elevator, color='red', label='Elevator', alpha=0.8)
        axs[1].set_ylabel("Deflection [-1.0, 1.0]")
        axs[1].set_xlabel("Flight time [steps]")
        axs[1].set_title("Control surface activity")
        axs[1].legend()
        axs[1].grid(True)

        # Orientation plot
        axs[2].plot(self.step, self.pitch, color='purple', label='Pitch', linewidth=1.5)
        axs[2].plot(self.step, self.roll, color='orange', label='Roll', linewidth=1.5)
        axs[2].set_ylabel("Angle [degrees]")
        axs[2].set_xlabel("Flight time [steps]")
        axs[2].set_title("Aircraft orientation")
        axs[2].legend()
        axs[2].grid(True)

        plt.tight_layout()
        plt.show()
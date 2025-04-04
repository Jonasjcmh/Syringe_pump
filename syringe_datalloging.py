import serial
import time
import math
import keyboard  # Library to detect key press
import csv

# Configure serial connection to Octopus board
SERIAL_PORT = "COM7"  # Change to your actual port (e.g., "/dev/ttyUSB0" on Linux)
BAUD_RATE = 115200

# Define motion parameters
X_MIN, X_MAX = 0, 50  # Movement range for X-axis
Y_MIN, Y_MAX = 0, 50  # Movement range for Y-axis
FREQ = 0.5  # Frequency of movement (Hz), adjust between 0.5 and 1.5 Hz

# Establish serial communication
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)

# Home X and Y axes
ser.write(b"G28 X Y\n")  # Home both axes
ser.flush()

# Enable motors and set speed
ser.write(b"M17\n")  # Enable motors
ser.write(f"G1 F{SPEED}\n".encode())  # Set movement speed

# Calibrate steps per mm using G-code and reverse Y-axis direction
ser.write(b"M92 X178 Y-178\n")  # Adjust steps per mm for accurate displacement
ser.flush()
time.sleep(1)

# Function to retrieve and print steps per mm
ser.write(b"M503\n")  # Read current settings
response = ser.readlines()
for line in response:
    print(line.decode().strip())

# Open CSV file for data logging
with open(".venv/Include/motion_log.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "X Position", "Y Position"])

    try:
        while True:
            if keyboard.is_pressed('x'):
                print("'X' key pressed. Stopping motion and returning to home position.")
                break

            period = 1 / FREQ  # Calculate motion period
            step_time = 0.01  # Log every 10 ms
            steps = int((period / 2) / step_time)  # Number of steps per half-cycle

            # Move to max position
            ser.write(f"G1 X{X_MAX} Y{Y_MAX}\n".encode())
            for _ in range(steps):
                if keyboard.is_pressed('x'):
                    break
                writer.writerow([time.time(), X_MAX, Y_MAX])
                time.sleep(step_time)

            # Move to min position
            ser.write(f"G1 X{X_MIN} Y{Y_MIN}\n".encode())
            for _ in range(steps):
                if keyboard.is_pressed('x'):
                    break
                writer.writerow([time.time(), X_MIN, Y_MIN])
                time.sleep(step_time)

    except KeyboardInterrupt:
        print("Motion stopped by user.")

# Return to home position before stopping
ser.flush()
time.sleep(5)  # Wait for homing to complete

# Disable motors
ser.write(b"M18\n")
ser.close()

print("Motion log saved to motion_log.csv")
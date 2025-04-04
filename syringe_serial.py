import serial
import time
import math
import keyboard  # Library to detect key press

# Configure serial connection to Octopus board
SERIAL_PORT = "COM7"  # Change to your actual port (e.g., "/dev/ttyUSB0" on Linux)
BAUD_RATE = 115200

# Define motion parameters
X_MIN, X_MAX = 0, 50  # Movement range for X-axis
Y_MIN, Y_MAX = 00, 50  # Movement range for Y-axis
FREQ = 2.0  # Frequency of movement (Hz), adjust between 0.5 and 1.5 Hz
SPEED = 3000  # Movement speed in mm/min

# Establish serial communication
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
time.sleep(2)  # Wait for connection to establish

# Home X and Y axes
ser.write(b"G28 X Y\n")  # Home both axes
ser.flush()
time.sleep(5)  # Wait for homing to complete

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

try:
    while True:
        if keyboard.is_pressed('x'):
            print("'X' key pressed. Stopping motion and returning to home position.")
            break

        period = 1 / FREQ  # Calculate motion period

        # Move to max position
        gcode = f"G1 X{X_MAX} Y{Y_MAX}\n"
        ser.write(gcode.encode())
        time.sleep(period / 2)

        # Move to min position
        gcode = f"G1 X{X_MIN} Y{Y_MIN}\n"
        ser.write(gcode.encode())
        time.sleep(period / 2)

except KeyboardInterrupt:
    print("Motion stopped by user.")

# Return to home position before stopping
ser.write(b"G28 X Y\n")  # Return to home position
time.sleep(5)  # Wait for homing to complete
ser.write(b"M18\n")  # Disable motors
ser.close()

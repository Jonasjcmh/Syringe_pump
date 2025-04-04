import serial
import time
import keyboard
import csv
import matplotlib.pyplot as plt
import pandas as pd

# -------- Serial config --------
PRINTER_PORT = "COM7"    # Octopus board
ARDUINO_PORT = "COM3"    # Arduino Mega with pressure sensors
BAUD_PRINTER = 115200
BAUD_ARDUINO = 9600

# -------- Motion parameters --------
X_MIN, X_MAX = 0, 90
Y_MIN, Y_MAX = 0, 90
FREQ = 0.5  # Hz
SPEED = 5000  # mm/min

SPEED_MIN = 1000  # Minimum speed in mm/min
SPEED_MAX = 5000  # Maximum speed in mm/min
DIST_X = X_MAX - X_MIN  # Distance to move in X axis (mm)
DIST_Y = Y_MAX - Y_MIN  # Distance to move in Y axis (mm)


# -------- Linear relation for time based on speed --------
def calculate_half_period(speed):
    return (-3 / 2000) * speed + 9  # Linear relation

# -------- Timing --------
HALF_PERIOD = 1 / (2 * FREQ)   # Duration of half cycle
SENSOR_INTERVAL = 0.02         # 20 ms for sensor readings

# -------- Connect to devices --------
ser = serial.Serial(PRINTER_PORT, BAUD_PRINTER, timeout=2)
time.sleep(1)
ser.reset_input_buffer()
ser.reset_output_buffer()

arduino = serial.Serial(ARDUINO_PORT, BAUD_ARDUINO, timeout=1)
time.sleep(1)

# -------- Printer setup --------
ser.write(b"\n")
time.sleep(0.5)
ser.write(b"M502\n")     # Restore factory defaults
time.sleep(0.5)
ser.write(b"M500\n")     # Save to EEPROM
time.sleep(0.5)
ser.write(b"G28 X Y\n")  # Home
ser.flush()
time.sleep(1)
ser.write(b"M17\n")      # Enable motors
ser.write(f"G1 F{SPEED}\n".encode())  # Set speed
ser.write(b"M92 X178 Y-178\n")        # Steps per mm
ser.flush()
time.sleep(1)

# -------- Open CSV log file --------
with open("motion_log.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Time (s)", "Pressure 1 (kPa)", "Pressure 2 (kPa)", "Switch State"])

    print("Starting motion loop. Press 'x' to stop.")
    try:
        t0 = time.time()
        phase = "forward"

        # -------- Motion loop --------
        last_gcode_time = 0  # To track the last G-code time

        while True:
            if keyboard.is_pressed('x'):
                print("Stopping motion.")
                break

            # Set speed (can be varied between 1000 and 5000)
            speed = SPEED_MAX  # Change this dynamically as needed

            # Calculate the half period based on the current speed
            half_period = calculate_half_period(speed)

            # Calculate the current time and check if half_period has passed since last G-code
            current_time = time.time() - t0
            if current_time - last_gcode_time >= half_period:

                # Decide whether to move forward or backward
                if phase == "forward":
                    target_x, target_y = X_MAX, Y_MAX
                else:
                    target_x, target_y = X_MIN, Y_MIN

                # Send the G-code to the printer
                ser.write(f"G1 X{target_x} Y{target_y}\n".encode())
                ser.flush()

                # Update the time when the G-code was last written
                last_gcode_time = current_time

            t_start = time.time() - t0

            # Sensor data reading and logging
            next_sensor_time = time.time()
            while (time.time() - t0 - t_start) < half_period:  # Use the calculated half_period here
                now = time.time()
                t_now = now - t0

                if now >= next_sensor_time:
                    pressure1 = pressure2 = None
                    switch_state = None

                    if arduino.in_waiting:
                        try:
                            line = arduino.readline().decode().strip()
                            millis, p1, p2, switch = line.split(',')
                            pressure1 = float(p1)
                            pressure2 = float(p2)
                            switch_state = int(switch)  # 0 for pressed, 1 for open
                        except:
                            pressure1 = pressure2 = switch_state = None

                    writer.writerow([round(t_now, 3), pressure1, pressure2, switch_state])
                    print(f"Time: {round(t_now, 3)} s, Switch: {switch_state}")
                    next_sensor_time += SENSOR_INTERVAL

            phase = "backward" if phase == "forward" else "forward"

    except KeyboardInterrupt:
        print("Interrupted by user.")

# -------- Return to home and cleanup --------
ser.write(b"G1 X0 Y0\n")
time.sleep(2)
ser.write(b"M18\n")
ser.close()
arduino.close()

print("Motion complete. Data saved to motion_log.csv.")

# -------- Plotting --------
df = pd.read_csv("motion_log.csv")

# Clean up and convert data
df["Pressure 1 (kPa)"] = pd.to_numeric(df["Pressure 1 (kPa)"], errors="coerce").fillna(0)
df["Pressure 2 (kPa)"] = pd.to_numeric(df["Pressure 2 (kPa)"], errors="coerce").fillna(0)
df["Switch State"] = pd.to_numeric(df["Switch State"], errors="coerce").fillna(1)  # Default to open (1)

# Plot
plt.figure(figsize=(10, 5))
plt.subplot(2, 1, 1)
plt.plot(df["Time (s)"], df["Pressure 1 (kPa)"], label="Pressure 1 (kPa)")
plt.plot(df["Time (s)"], df["Pressure 2 (kPa)"], label="Pressure 2 (kPa)")
plt.xlabel("Time (s)")
plt.ylabel("Pressure (kPa)")
plt.title("Pressure Sensor Readings Over Time")
plt.grid(True)
plt.legend()

# Plot the switch state
plt.subplot(2, 1, 2)
plt.plot(df["Time (s)"], df["Switch State"], label="Switch State", color="red")
plt.xlabel("Time (s)")
plt.ylabel("Switch State (Open/Closed)")
plt.title("Switch State Over Time")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

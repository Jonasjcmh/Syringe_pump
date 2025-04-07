import serial
import time
import keyboard
import csv

# Serial connection config
SERIAL_PORT = "COM7"
BAUD_RATE = 115200

# Motion parameters
X_MIN, X_MAX = 0, 50
Y_MIN, Y_MAX = 0, 50
FREQ = 1.0  # Hz (full cycle = 0.5s, half-cycle = 0.25s)
SPEED = 1000  # mm/min

# Timing
HALF_PERIOD = 1 / (2 * FREQ)     # 0.25 seconds for 2 Hz
STEP_INTERVAL = 0.01             # 10 ms log interval

# Connect to printer
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
time.sleep(2)
ser.reset_input_buffer()
ser.reset_output_buffer()

# Reset to safe defaults and home
ser.write(b"\n")
time.sleep(0.5)
ser.write(b"M502\n")     # Restore firmware defaults
time.sleep(0.5)
ser.write(b"M500\n")     # Save to EEPROM
time.sleep(0.5)
ser.write(b"G28 X Y\n")  # Home X and Y
time.sleep(3)

# Enable motors, set feedrate and steps/mm
ser.write(b"M17\n")                             # Enable motors
ser.write(f"G1 F{SPEED}\n".encode())            # Set movement speed
ser.write(b"M92 X178 Y-178\n")                  # Calibrate/invert Y
time.sleep(1)

# Open CSV file
with open("motion_log.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Time (s)", "Phase", "X Target", "Y Target"])

    print("Starting motion loop. Press 'x' to stop.")

    try:
        t0 = time.time()
        phase = "forward"

        while True:
            if keyboard.is_pressed('x'):
                print("Stopping motion.")
                break

            # Set target
            if phase == "forward":
                target_x, target_y = X_MAX, Y_MAX
            else:
                target_x, target_y = X_MIN, Y_MIN

            # Log and send motion command
            t_start = time.time() - t0
            writer.writerow([round(t_start, 3), f"start_{phase}", target_x, target_y])
            ser.write(f"G1 X{target_x} Y{target_y}\n".encode())

            # Log time during half-cycle
            while (time.time() - t0 - t_start) < HALF_PERIOD:
                t_now = time.time() - t0
                writer.writerow([round(t_now, 3), f"moving_{phase}", target_x, target_y])
                time.sleep(STEP_INTERVAL)

            # Log end
            t_end = time.time() - t0
            writer.writerow([round(t_end, 3), f"end_{phase}", target_x, target_y])

            # Toggle phase
            phase = "backward" if phase == "forward" else "forward"

    except KeyboardInterrupt:
        print("Interrupted by user.")

# Return to home and disable motors
ser.write(b"G1 X0 Y0\n")
time.sleep(2)
ser.write(b"M18\n")
ser.close()

print("Motion complete. Log saved to motion_log.csv.")

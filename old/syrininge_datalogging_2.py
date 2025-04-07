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
FREQ = 2.0  # Hz
SPEED = 2000  # mm/min

# Timing
HALF_PERIOD = 1 / (2 * FREQ)
STEP_INTERVAL = 0.01  # 10 ms

# Connect to printer
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
time.sleep(2)

# Wake and home
ser.reset_input_buffer()
ser.reset_output_buffer()
ser.write(b"M502\n")     # Restore factory settings
time.sleep(0.5)
ser.write(b"M500\n")     # Save to EEPROM
time.sleep(0.5)
ser.write(b"G28 X Y\n")  # Re-home
time.sleep(1)
ser.write(b"M17\n")      # Enable motors
ser.write(f"G1 F{SPEED}\n".encode())  # Set speed


ser.write(b"\n")
time.sleep(1)
ser.write(b"G28 X Y\n")
time.sleep(3)
ser.write(b"M17\n")
ser.write(f"G1 F{SPEED}\n".encode())
ser.write(b"M92 X178 Y-178\n")
time.sleep(1)

# Open CSV for logging
with open("../motion_log.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Time (s)", "Phase", "X Target", "Y Target"])

    print("Starting motion loop. Press 'x' to stop.")

    try:
        t0 = time.time()

        while True:
            if keyboard.is_pressed('x'):
                print("Stopping motion.")
                break

            # --- FORWARD ---
            t_start = time.time() - t0
            writer.writerow([round(t_start, 3), "start_forward", X_MAX, Y_MAX])
            ser.write(f"G1 X{X_MAX} Y{Y_MAX}\n".encode())

            while (time.time() - t0 - t_start) < HALF_PERIOD:
                t_now = time.time() - t0
                writer.writerow([round(t_now, 3), "moving_forward", X_MAX, Y_MAX])
                time.sleep(STEP_INTERVAL)

            t_end = time.time() - t0
            writer.writerow([round(t_end, 3), "end_forward", X_MAX, Y_MAX])

            if keyboard.is_pressed('x'):
                break

            # --- BACKWARD ---
            t_start = time.time() - t0
            writer.writerow([round(t_start, 3), "start_backward", X_MIN, Y_MIN])
            ser.write(f"G1 X{X_MIN} Y{Y_MIN}\n".encode())

            while (time.time() - t0 - t_start) < HALF_PERIOD:
                t_now = time.time() - t0
                writer.writerow([round(t_now, 3), "moving_backward", X_MIN, Y_MIN])
                time.sleep(STEP_INTERVAL)

            t_end = time.time() - t0
            writer.writerow([round(t_end, 3), "end_backward", X_MIN, Y_MIN])

    except KeyboardInterrupt:
        print("Interrupted by user.")

# Return to home and disable
ser.write(b"G1 X0 Y0\n")
time.sleep(2)
ser.write(b"M18\n")
ser.close()

print("Motion complete. Log saved to motion_log.csv.")

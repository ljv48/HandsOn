import serial
import time
import re
import matplotlib.pyplot as plt
from supabase import create_client, Client
from datetime import datetime, timezone

# Supabase setup
SUPABASE_URL = "https://tslcyteqrbeiwjifpdeb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzbGN5dGVxcmJlaXdqaWZwZGViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2NTcwMzIsImV4cCI6MjA3NzIzMzAzMn0.VWqv2VkqJ7csDKn6G947T-J7Pf9jlHhGWo33B0eof2s"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Serial setup ---
port = '/dev/cu.usbmodem14201'  # Change to your Arduino port
baud = 9600
max_points = 50  # max data points to show per sensor
x_window = 10  # seconds shown on x-axis window

print("Connecting to Arduino...")
ser = serial.Serial(port, baud, timeout=1)
time.sleep(2)
print(f"Connected to {port}")

# --- Matplotlib setup ---
plt.ion()
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4))

# Initialize empty data lists
force_data, flex_data, move_data = [], [], []
# Separate time tracking for each sensor
force_time, flex_time, move_time = [], [], []

# Empty plot lines
force_line, = ax1.plot([], [], label="Force Sensor", color='blue')
flex_line,  = ax2.plot([], [], label="Flex Sensor", color='green')
move_line,  = ax3.plot([], [], label="Movement Sensor", color='orange')

# Labeling graphs and axis
for ax, title in zip(
    [ax1, ax2, ax3],
    ["Force Sensor Data", "Flex Sensor Data", "Movement Sensor Data"]
):
    ax.set_xlim(0, x_window)  # initial x-axis window
    ax.set_ylim(0, 1023)  # temporary default until scaling updates
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Analog Reading")
    ax.set_title(title)
    ax.legend()

ax1.set_ylabel("Force (PSI)")
ax1.set_ylim(0, 50)

plt.ion()  # turn on interactive plotting
plt.show()


# PSI calibration
def fsr_to_psi(analog_value, r_fixed=10000, k=800000, area_in2=0.125):
    if analog_value == 0:
        return 0
    r_fsr = r_fixed * (1023 - analog_value) / analog_value
    force_g = k / r_fsr
    psi = (force_g * 0.00220462) / area_in2
    return psi

def store_to_supabase(force, flex, move):
    supabase.table("trainer_data").insert({
        "force": force,
        "flex": flex,
        "move": move,
        "timestamp": datetime.now(timezone.utc)  # proper timestamptz
    }).execute()


# Main loop
start_time = time.time()

while True:
    if ser.in_waiting > 0:
        raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
        print(raw_line)

        match = re.search(r'(\d+)', raw_line)
        if match:
            value = int(match.group(1))

            value = float(match.group(1))  # Cast as float for sensor data
            current_time = time.time() - start_time  # Seconds since start

            # Force Sensor
            if "Force" in raw_line:
                psi_value = fsr_to_psi(value)
                current_time = time.time() - start_time
                force_time.append(current_time)
                force_data.append(psi_value)

                # Saving to Supabase
                from datetime import datetime, timezone

                data = {
                    "user_id": "trainer",
                    "force": float(psi_value),
                    "flex": float(flex_data[-1]) if flex_data else 0.0,
                    "move": float(move_data[-1]) if move_data else 0.0,
                    "timestamp": datetime.now(timezone.utc).isoformat()  # ISO string
                }
                response = supabase.table("trainer_data").insert(data).execute()
                print(response)

                # Trim data lists to max_points
                if len(force_data) > max_points:
                    force_data = force_data[-max_points:]
                    force_time = force_time[-max_points:]

                # Plot
                force_line.set_xdata(force_time)
                force_line.set_ydata(force_data)
                current_max = max(force_data) if len(force_data) > 0 else 50
                ax1.set_ylim(0, max(50, current_max + 5))
                ax1.relim()
                ax1.autoscale_view(True, True, True)

            # Flex Sensor
            elif "Flex" in raw_line:
                current_time = time.time() - start_time
                flex_time.append(current_time)
                flex_data.append(value)

                if len(flex_data) > max_points:
                    flex_data = flex_data[-max_points:]
                    flex_time = flex_time[-max_points:]

                flex_line.set_xdata(flex_time)
                flex_line.set_ydata(flex_data)
                ax2.relim()
                ax2.autoscale_view(True, True, True)

                # Movement sensor
            elif "Movement" in raw_line:
                current_time = time.time() - start_time
                move_time.append(current_time)
                move_data.append(value)

                if len(move_data) > max_points:
                    move_data = move_data[-max_points:]
                    move_time = move_time[-max_points:]

                move_line.set_xdata(move_time)
                move_line.set_ydata(move_data)
                ax3.relim()
                ax3.autoscale_view(True, True, True)

            # Shifting x-axis view in real-time
            for ax, t_data in zip([ax1, ax2, ax3], [force_time, flex_time, move_time]):
                if len(t_data) > 0:
                    ax.set_xlim(max(0, t_data[-1] - x_window), t_data[-1])

            plt.pause(0.05)  # Small delay to update plots

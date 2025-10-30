import serial  # library for connecting to port
import time  # manipulate time
import re  # input strings conform to a certain format
import matplotlib.pyplot as plt  # allows use of plt instead of matplotlib.pyplot


port = '/dev/cu.usbmodem14201'  # Second port on right side
baud = 9600
max_points = 50

# connecting to arduino
print("Connecting to Arduino...")
ser = serial.Serial(port, baud, timeout=1)
time.sleep(2)
print(f"Connected to {port}")

# 3 subplots (1 row, 3 columns)
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4))


# data containers
force_data, flex_data, move_data = [], [], []


def fsr_to_psi(analog_value, r_fixed=10000, k=800000, area_in2=0.125):
    # Converts FSR analog reading (0–1023) to approximate PSI.

    if analog_value == 0:
        return 0
    r_fsr = r_fixed * (1023 - analog_value) / analog_value
    force_g = k / r_fsr
    psi = (force_g * 0.00220462) / area_in2  # grams → pounds → psi
    return psi


# empty plot lines
force_line, = ax1.plot([], [], label="Force Sensor", color='blue')
flex_line,  = ax2.plot([], [], label="Flex Sensor", color='green')
move_line,  = ax3.plot([], [], label="Movement Sensor", color='orange')

# labeling
for ax, title in zip(
    [ax1, ax2, ax3],
    ["Force Sensor Data", "Flex Sensor Data", "Movement Sensor Data"]
):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1023)
    ax.set_xlabel("Samples")
    ax.set_ylabel("Analog Reading")
    ax.set_title(title)
    ax.legend()

# update y-axis label for force
ax1.set_ylabel("Force (PSI)")
ax1.set_ylim(0, 50)  # adjust based on expected range
plt.ion()
plt.show()


# allows serial reading continuously
while True:
    if ser.in_waiting > 0:
        raw_line = ser.readline().decode('utf-8', errors='ignore').strip()  # reads connection, decodes into string, removes whitespace
        print(raw_line)  # shows raw incoming line

        # Check which sensor sent the data and the amount
        match = re.search(r'(\d+)', raw_line)
        if match:
            value = int(match.group(1))  # converts to integer

            if "Force" in raw_line:
                psi_value = fsr_to_psi(value)  # Convert analog reading to PSI
                force_data.append(psi_value)

                # limit number of displayed points
                if len(force_data) > max_points:
                    force_data = force_data[-max_points:]

                force_line.set_ydata(force_data)
                force_line.set_xdata(range(len(force_data)))
                ax1.relim()
                ax1.autoscale_view(True, True, True)

            elif "Flex" in raw_line:
                flex_data.append(value)
                if len(flex_data) > max_points:
                    flex_data = flex_data[-max_points:]
                flex_line.set_ydata(flex_data)
                flex_line.set_xdata(range(len(flex_data)))
                ax2.relim()
                ax2.autoscale_view(True, True, True)

            elif "Movement" in raw_line:
                move_data.append(value)
                if len(move_data) > max_points:
                    move_data = move_data[-max_points:]
                move_line.set_ydata(move_data)
                move_line.set_xdata(range(len(move_data)))
                ax3.relim()
                ax3.autoscale_view(True, True, True)

            plt.pause(0.05)   # small delay for updates

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

# empty plot lines
force_line, = ax1.plot([], [], label="Force Sensor", color='blue')
flex_line,  = ax2.plot([], [], label="Flex Sensor", color='green')
move_line,  = ax3.plot([], [], label="Movement Sensor", color='orange')

# labeling
for ax, title in zip(  # takes objects and turns into tuples to assign elements to the ax and title
    [ax1, ax2, ax3],
    ["Force Sensor Data", "Flex Sensor Data", "Movement Sensor Data"]
):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1023)
    ax.set_xlabel("Samples")
    ax.set_ylabel("Analog Reading")
    ax.set_title(title)
    ax.legend()

plt.ion()  # interactive mode for live updates
plt.show()  # shows figures

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
                force_data.append(value)  # adds new data point
                force_line.set_ydata(force_data)  # updates y-axis data
                force_line.set_xdata(range(len(force_data)))  # updates x-axis to match new length
                ax1.relim()  # calculates the new minimum and maximum data values
                ax1.autoscale_view(True, True, True)  # applies these new limits to the plot

            elif "Flex" in raw_line:
                flex_data.append(value)
                flex_line.set_ydata(flex_data)
                flex_line.set_xdata(range(len(flex_data)))
                ax2.relim()
                ax2.autoscale_view(True, True, True)

            elif "Movement" in raw_line:
                move_data.append(value)
                move_line.set_ydata(move_data)
                move_line.set_xdata(range(len(move_data)))
                ax3.relim()
                ax3.autoscale_view(True, True, True)

            plt.pause(0.05)  # pauses execution @ 0.05 seconds

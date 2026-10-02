import time
import serial.tools.list_ports

SERIAL_PORT = None  # Auto-detect if None
BAUD_RATE = 115200

# 🚀 Auto-Detect USB Serial Port
def find_usb_serial():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "USB" in port.description or "Serial" in port.description:
            print(f"🔍 Auto-detected USB Serial Device: {port.device}")
            return port.device
    return None

# 🚀 Send Command & Handle Responses
def send_command(ser, command):
    """Sends a command and reads the response, handling errors & acknowledgments."""
    ser.write((command + "\r").encode())  # Send command with carriage return
    time.sleep(0.1)  # Delay for response
    response = ser.read_all().decode().strip()  # Read full response
    response = response.replace(command, "").strip()  # Remove echoed command
    
    # Error Handling
    if response == "-":
        print(f"❌ Error: Invalid command '{command}'")
        return None
    elif response.startswith("-1"):
        print(f"❌ Error: Out-of-range parameter in '{command}'")
        return None
    elif response.startswith("-2"):
        print(f"❌ Error: Command not available in current mode '{command}'")
        return None
    
    # Command Acknowledgment
    if response == "+":
        print(f"✅ Command '{command}' acknowledged.")
        return None

    return response  # Return valid response

# 🚀 Parse Fault Flags
def parse_fault_flags(ff_value):
    faults = {
        1: "Overheat", 2: "Overvoltage", 4: "Undervoltage", 8: "Short circuit",
        16: "Emergency stop", 32: "Motor/Sensor fault", 64: "MOSFET failure",
        128: "Default config loaded"
    }
    return [desc for bit, desc in faults.items() if int(ff_value) & bit] or ["No Faults"]

# 🚀 Parse Status Flags
def parse_status_flags(fs_value):
    statuses = {
        1: "Serial Mode", 2: "Pulse Mode", 4: "Analog Mode", 8: "Power Stage Off",
        16: "Stall Detected", 32: "At Limit", 128: "MicroBasic Script Running",
        256: "Motor/Sensor Tuning Mode"
    }
    return [desc for bit, desc in statuses.items() if int(fs_value) & bit] or ["No Status Flags"]

# 🚀 Get Motor & System Data
def get_motor_data(ser):
    print("\n📊 **Motor & System Data**")

    # Motor Current (Apply Scaling)
    response_current = send_command(ser, "?A")
    if response_current:
        values = response_current.split("=")[-1].split(":")
        if len(values) >= 2:
            try:
                motor_1_current = float(values[0]) / 10  # 🔄 Apply scaling (divided by 10)
                motor_2_current = -float(values[1]) / 10  # 🔄 Reverse sign & apply scaling
                print(f"🔹 Motor 1 Current: {motor_1_current:.2f} A | Motor 2 Current: {motor_2_current:.2f} A")
            except ValueError:
                print(f"⚠️  Unexpected current values: {values}")

    # Battery Voltage (Scaling applied)
    response_voltage = send_command(ser, "?V")
    if response_voltage:
        values = response_voltage.split("=")[-1].split(":")
        if len(values) >= 3:
            try:
                battery_voltage_1 = float(values[0]) / 10  
                battery_voltage_2 = float(values[1]) / 10  
                controller_voltage = float(values[2]) / 100  
                print(f"🔹 Battery 1 Voltage: {battery_voltage_1:.1f} V | Battery 2 Voltage: {battery_voltage_2:.1f} V | Controller Voltage: {controller_voltage:.2f} V")
            except ValueError:
                print(f"⚠️  Unexpected voltage values: {values}")

    # Motor Power Output (Apply Scaling)
    response_power = send_command(ser, "?P")
    if response_power:
        values = response_power.split("=")[-1].split(":")
        if len(values) >= 2:
            try:
                motor_1_power = float(values[0])   # Apply scaling
                motor_2_power = float(values[1])  # Apply scaling
                print(f"🔹 Motor 1 Power: {motor_1_power:.2f} W | Motor 2 Power: {motor_2_power:.2f} W")
            except ValueError:
                print(f"⚠️  Unexpected power values: {values}")

    # Temperature
    response_temp = send_command(ser, "?T")
    if response_temp:
        values = response_temp.split("=")[-1].split(":")
        if len(values) >= 3:
            print(f"🔹 Controller Temp: {values[0]}°C | Motor 1 Temp: {values[1]}°C | Motor 2 Temp: {values[2]}°C")

# 🚀 Get Error & Fault Data
def get_error_data(ser):
    print("\n🚨 **Error & Fault Status**")

    # Fault Flags
    response_ff = send_command(ser, "?FF")
    if response_ff:
        fault_flags = response_ff.split("=")[-1]
        faults = parse_fault_flags(fault_flags)
        print(f"⚠️  Faults: {', '.join(faults)}")

    # Status Flags
    response_fs = send_command(ser, "?FS")
    if response_fs:
        status_flags = response_fs.split("=")[-1]
        statuses = parse_status_flags(status_flags)
        print(f"🔹 Status: {', '.join(statuses)}")

    # Motor Runtime Errors
    response_fm = send_command(ser, "?FM 1")  # Motor 1
    if response_fm:
        print(f"⚙️  Motor 1 Runtime Status: {response_fm}")

    # Closed Loop Error
    response_e = send_command(ser, "?E 1")  # Motor 1
    if response_e:
        print(f"🎯 Closed Loop Error: {response_e}")

# 🚀 Main Execution
def main():
    port = find_usb_serial() if SERIAL_PORT is None else SERIAL_PORT
    if port is None:
        print("❌ No USB Serial device found.")
        return

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        time.sleep(2)  # Allow time for serial connection
        print(f"✅ Connected to {port} at {BAUD_RATE} baud.")

        get_motor_data(ser)  # Read motor parameters
        get_error_data(ser)  # Read error status

        ser.close()
        print("🔌 Connection closed.")

    except serial.SerialException as e:
        print(f"❌ Serial Communication Error: {e}")

if __name__ == "__main__":
    main()

import serial
import time
import threading
import signal
import sys

# Serial port configuration - adjust as needed
SERIAL_PORT = '/dev/ttyUSB0'  # Arduino connected via USB
# Use '/dev/ttyACM0' if using Arduino Uno or similar
BAUD_RATE = 9600

# Tap detection configuration
TAP_THRESHOLD = 500          # Analog value threshold (0-1023)
DOUBLE_TAP_THRESHOLD = 0.5   # Maximum time between taps for double tap (seconds)
HOLD_THRESHOLD = 1.0         # Minimum time for hold detection (seconds)
DEBOUNCE_TIME = 0.02         # Minimum time between state changes (seconds)

# Global variables for state tracking
last_tap_time = 0
tap_count = 0
press_start_time = 0
is_pressed = False
last_fsr_value = 0
last_state_change_time = 0

# Flags for actions
double_tap_detected = False
hold_detected = False
single_tap_detected = False
hold_duration = 0

# Set up serial connection
ser = None

def setup_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to Arduino on {SERIAL_PORT}")
        time.sleep(2)  # Give the Arduino time to reset
        return True
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return False

def cleanup():
    """Clean up resources before exiting"""
    if ser and ser.is_open:
        ser.close()
        print("Serial connection closed")
    print("Program terminated")
    sys.exit(0)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nReceived interrupt signal")
    cleanup()

# Register the signal handler for graceful exit
signal.signal(signal.SIGINT, signal_handler)

def process_fsr_value(fsr_value):
    """Process FSR readings and detect taps/holds"""
    global last_tap_time, tap_count, press_start_time, is_pressed
    global last_state_change_time, double_tap_detected, hold_detected, single_tap_detected, hold_duration
    
    current_time = time.time()
    
    # Debounce - ignore rapid changes
    if current_time - last_state_change_time < DEBOUNCE_TIME:
        return
    
    # Detect press start
    if fsr_value > TAP_THRESHOLD and not is_pressed:
        is_pressed = True
        press_start_time = current_time
        last_state_change_time = current_time
        print(f"Press detected! Value: {fsr_value}")
    
    # Detect release
    elif fsr_value <= TAP_THRESHOLD and is_pressed:
        is_pressed = False
        press_duration = current_time - press_start_time
        last_state_change_time = current_time
        
        # Check if it was a hold
        if press_duration >= HOLD_THRESHOLD:
            print(f"Hold detected! Duration: {press_duration:.2f}s")
            hold_detected = True
            hold_duration = press_duration
            tap_count = 0  # Reset tap counter after hold
        
        # Check if it was a tap
        elif press_duration < HOLD_THRESHOLD:
            # Check for double tap
            if tap_count == 1 and (current_time - last_tap_time <= DOUBLE_TAP_THRESHOLD):
                print("Double tap detected!")
                double_tap_detected = True
                tap_count = 0  # Reset tap counter
            else:
                print("Single tap detected")
                single_tap_detected = True
                tap_count = 1
                last_tap_time = current_time
    
    # Handle ongoing hold
    elif fsr_value > TAP_THRESHOLD and is_pressed:
        if current_time - press_start_time >= HOLD_THRESHOLD:
            # To avoid spamming, only print hold status occasionally
            if int((current_time - press_start_time) * 10) % 10 == 0:
                print(f"Holding... {current_time - press_start_time:.1f}s")
                hold_duration = current_time - press_start_time

def read_fsr_data():
    """Main loop to read FSR data from Arduino"""
    if not setup_serial():
        print("Failed to connect to Arduino. Exiting...")
        return
    
    try:
        while True:
            if ser.in_waiting > 0:
                # Read a line from serial and strip whitespace
                line = ser.readline().decode('utf-8').strip()
                
                try:
                    # Convert to integer
                    fsr_value = int(line)
                    process_fsr_value(fsr_value)
                except ValueError:
                    # Skip invalid data
                    pass
    except Exception as e:
        print(f"Error reading from serial: {e}")
    finally:
        cleanup()

def main():
    """Main function to run the program"""
    print("FSR Tap Detection System")
    print("Press Ctrl+C to exit")
    
    # Example of how you might use the detected actions
    def check_actions():
        global double_tap_detected, hold_detected, single_tap_detected, hold_duration
        
        while True:
            # Check for actions and handle them
            if double_tap_detected:
                print("Action: Running double tap function!")
                # Add your double tap action here
                double_tap_detected = False
            
            if hold_detected:
                print(f"Action: Running hold function! Hold duration: {hold_duration:.1f}s")
                # Add your hold action here
                hold_detected = False
            
            if single_tap_detected:
                print("Action: Running single tap function!")
                # Add your single tap action here
                single_tap_detected = False
            
            time.sleep(0.1)  # Small delay to avoid hogging CPU
    
    # Start threads for reading data and checking actions
    read_thread = threading.Thread(target=read_fsr_data)
    action_thread = threading.Thread(target=check_actions)
    
    read_thread.daemon = True
    action_thread.daemon = True
    
    read_thread.start()
    action_thread.start()
    
    # Keep main thread alive until user interrupts
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
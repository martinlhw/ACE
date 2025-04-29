#!/usr/bin/env python3
import serial
import time
import threading
import queue

class PokerSignalReceiver:
    def __init__(self, port='/dev/ttyACM0', baud_rate=9600):
        """Initialize the signal receiver."""
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.connected = False
        
        # Data storage for multiple sensors
        self.weights = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        self.last_events = {1: None, 2: None, 3: None, 4: None}
        
        # Queue for events that can be processed by the game
        self.event_queue = queue.Queue()
        
        # Create and start event processing thread
        self.running = True
        self.processing_thread = threading.Thread(target=self._read_serial_thread)
        self.processing_thread.daemon = True
        
        # Connect on initialization
        self.connect()
        self.processing_thread.start()
    
    def connect(self):
        """Connect to the Arduino."""
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            # Allow time for Arduino to reset after connection
            time.sleep(2)
            self.connected = True
            print(f"Connected to Arduino on port {self.port}")
            return True
        except Exception as e:
            print(f"Error connecting to Arduino: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the Arduino."""
        self.running = False
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            self.connected = False
            print("Disconnected from Arduino")
    
    def send_command(self, command):
        """Send a command to the Arduino."""
        if not self.connected:
            print("Not connected to Arduino")
            return False
        
        try:
            self.ser.write((command + "\n").encode())
            print(f"Sent command: {command}")
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
    
    def tare_scale(self, sensor_num=None):
        """Send tare command to the Arduino."""
        if sensor_num is not None:
            if 1 <= sensor_num <= 4:
                return self.send_command(f"TARE:{sensor_num}")
            else:
                print(f"Invalid sensor number: {sensor_num}")
                return False
        else:
            return self.send_command("TARE_ALL")
    
    def _process_message(self, message):
        """Process a message from the Arduino."""
        message = message.strip()
        # print(message)
        # Skip empty messages
        if not message:
            return
        
        
        if self.port == '/dev/ttyACM2':
            # Skip messages from the second Arduino
            if message.startswith("ack"):
                return
        # Process different message types
        if message.startswith("WEIGHT:"):
            try:
                parts = message.split(":", 2)
                if len(parts) == 3:
                    sensor_num = int(parts[1])
                    weight_value = float(parts[2])
                    old_weight = self.weights[sensor_num]
                    self.weights[sensor_num] = weight_value
                    
                    # Add to event queue if weight has meaningfully changed
                    if abs(weight_value - old_weight) > 1.0:  # 1g threshold to avoid noise
                        self.event_queue.put({
                            'type': 'WEIGHT',
                            'sensor': sensor_num,
                            'value': weight_value
                        })
            except (ValueError, IndexError):
                print(f"Invalid weight value format: {message}")
        
        elif message.startswith("EVENT:"):
            try:
                print(message)
                parts = message.split(":", 2)
                if len(parts) == 3:
                    event_type = parts[1]
                    sensor_num = int(parts[2])
                    
                    self.last_events[sensor_num] = event_type
                    
                    # Add to event queue
                    if event_type in ['SINGLE_TAP', 'DOUBLE_TAP', 'HOLD']:
                        self.event_queue.put({
                            'type': event_type,
                            'sensor': sensor_num
                        })
            except (ValueError, IndexError):
                print(f"Invalid event format: {message}")
        
        elif message.startswith("STATUS:"):
            status = message.split(":", 1)[1]
            print(f"Status update: {status}")
    
    def _read_serial_thread(self):
        """Background thread to continuously read from Arduino."""
        while self.running:
            if not self.connected:
                # Try to reconnect if disconnected
                if self.connect():
                    print("Reconnected to Arduino")
                else:
                    # Wait before trying again
                    time.sleep(3)
                    continue
            
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').rstrip()
                    self._process_message(line)
            except Exception as e:
                print(f"Error reading from serial: {e}")
                self.connected = False
            
            # Small sleep to avoid hammering the CPU
            time.sleep(0.01)
    
    def get_next_event(self):
        """Get the next event from the queue if available."""
        if not self.event_queue.empty():
            return self.event_queue.get(block=False)
        return None
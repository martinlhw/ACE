const int FSR_PIN = A0;           // Analog pin for FSR input
const int LED_PIN = 13;           // Optional LED for visual feedback
const int SAMPLE_RATE = 50;       // How many samples per second (Hz)
const int DELAY_MS = 1000 / SAMPLE_RATE;

void setup() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
    
    // Initialize serial communication at 9600 bits per second
    Serial.begin(9600);
    
    // Wait for serial port to connect (needed for native USB port only)
    while (!Serial) {
        ; // wait for serial port to connect
    }
}

void loop() {
    // Read the FSR value (0-1023)
    int fsrValue = analogRead(FSR_PIN);
    
    // Send the value to the Raspberry Pi
    Serial.println(fsrValue);
    
    // Optional: Visual feedback on the Arduino
    if (fsrValue > 500) {
        digitalWrite(LED_PIN, HIGH);
    } else {
        digitalWrite(LED_PIN, LOW);
    }
    
    // Wait for a bit to maintain consistent sampling rate
    delay(DELAY_MS);
}
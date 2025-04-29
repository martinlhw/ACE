/*
   Combined HX711 weight sensing with FSR tap detection
   Supporting 4 sets of sensors with USB communication to Raspberry Pi
*/

#include <HX711_ADC.h>
#if defined(ESP8266)|| defined(ESP32) || defined(AVR)
#include <EEPROM.h>
#endif

// HX711 pins
const int HX711_dout1 = 2; // mcu > HX711 dout pin
const int HX711_sck1 = 3;  // mcu > HX711 sck pin
const int HX711_dout2 = 4; // mcu > HX711 dout pin
const int HX711_sck2 = 5;  // mcu > HX711 sck pin
const int HX711_dout3 = 7; // mcu > HX711 dout pin
const int HX711_sck3 = 6;  // mcu > HX711 sck pin
const int HX711_dout4 = 8; // mcu > HX711 dout pin
const int HX711_sck4 = 9;  // mcu > HX711 sck pin

// FSR pins
const int FSR_PIN1 = A1;   // Analog pin for FSR input
const int FSR_PIN2 = A2;
const int FSR_PIN3 = A3;
const int FSR_PIN4 = A4;
const int LED_PIN = 13;    // LED for visual feedback

// HX711 constructors:
HX711_ADC LoadCell1(HX711_dout1, HX711_sck1);
HX711_ADC LoadCell2(HX711_dout2, HX711_sck2);
HX711_ADC LoadCell3(HX711_dout3, HX711_sck3);
HX711_ADC LoadCell4(HX711_dout4, HX711_sck4);

// Weight sensing variables
const int calVal_eepromAdress = 0;
unsigned long t = 0;
const int serialPrintInterval = 100; // Interval between weight prints (ms)

// Calibration values for each load cell
float calibrationValue1 = 758.05;
float calibrationValue2 = 758.05; // Adjust these based on your calibration
float calibrationValue3 = 758.05;
float calibrationValue4 = 758.05;

// Tap detection configuration
const int TAP_THRESHOLD = 100;       // Analog value threshold for tap detection
const unsigned long DOUBLE_TAP_TIME = 500;  // Time window for double tap (ms)
const unsigned long HOLD_TIME = 500;        // Hold detection time (ms)
const unsigned long DEBOUNCE_TIME = 50;     // Increased debounce time (ms)

// Tap state variables for each FSR
struct TapState {
  unsigned long lastTapTime = 0;
  int tapCount = 0;
  unsigned long pressStartTime = 0;
  bool isPressed = false;
  unsigned long lastStateChangeTime = 0;
};

TapState fsrState[4]; // Array for all 4 FSR sensors

// For smoother FSR readings
const int NUM_READINGS = 5;
int fsrReadings[4][NUM_READINGS]; // 2D array for all 4 FSR sensors
int readIndex[4] = {0, 0, 0, 0};
int fsrTotal[4] = {0, 0, 0, 0};
int fsrAverage[4] = {0, 0, 0, 0};

void setup() {
  // Setup for serial communication with Pi
  Serial.begin(9600); delay(10);
  Serial.println("STATUS:STARTING");
  Serial.println("STATUS:Multiple weight sensors and FSR tap detection initializing");

  // Setup for LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Initialize FSR readings arrays
  for (int sensor = 0; sensor < 4; sensor++) {
    for (int i = 0; i < NUM_READINGS; i++) {
      fsrReadings[sensor][i] = 0;
    }
  }

  // Initialize all HX711 load cells
  unsigned long stabilizingtime = 2000;
  boolean _tare = true;
  
  // Initialize LoadCell1
  LoadCell1.begin();
  LoadCell1.start(stabilizingtime, _tare);
  if (LoadCell1.getTareTimeoutFlag()) {
    Serial.println("STATUS:ERROR:HX711_1 connection timeout");
  } else {
    LoadCell1.setCalFactor(calibrationValue1);
    Serial.println("STATUS:HX711_1 initialized");
  }
  
  // Initialize LoadCell2
  LoadCell2.begin();
  LoadCell2.start(stabilizingtime, _tare);
  if (LoadCell2.getTareTimeoutFlag()) {
    Serial.println("STATUS:ERROR:HX711_2 connection timeout");
  } else {
    LoadCell2.setCalFactor(calibrationValue2);
    Serial.println("STATUS:HX711_2 initialized");
  }
  
  // Initialize LoadCell3
  LoadCell3.begin();
  LoadCell3.start(stabilizingtime, _tare);
  if (LoadCell3.getTareTimeoutFlag()) {
    Serial.println("STATUS:ERROR:HX711_3 connection timeout");
  } else {
    LoadCell3.setCalFactor(calibrationValue3);
    Serial.println("STATUS:HX711_3 initialized");
  }
  
  // Initialize LoadCell4
  LoadCell4.begin();
  LoadCell4.start(stabilizingtime, _tare);
  if (LoadCell4.getTareTimeoutFlag()) {
    Serial.println("STATUS:ERROR:HX711_4 connection timeout");
  } else {
    LoadCell4.setCalFactor(calibrationValue4);
    Serial.println("STATUS:HX711_4 initialized");
  }
  
  Serial.println("STATUS:READY");
}

// Function to get smoothed FSR reading for a specific sensor
int getSmoothedFSRReading(int sensorIndex, int pin) {
  // Subtract the last reading
  fsrTotal[sensorIndex] = fsrTotal[sensorIndex] - fsrReadings[sensorIndex][readIndex[sensorIndex]];
  // Read from the sensor
  fsrReadings[sensorIndex][readIndex[sensorIndex]] = analogRead(pin);
  // Add the reading to the total
  fsrTotal[sensorIndex] = fsrTotal[sensorIndex] + fsrReadings[sensorIndex][readIndex[sensorIndex]];
  // Advance to the next position in the array
  readIndex[sensorIndex] = (readIndex[sensorIndex] + 1) % NUM_READINGS;
  
  // Calculate the average
  fsrAverage[sensorIndex] = fsrTotal[sensorIndex] / NUM_READINGS;
  return fsrAverage[sensorIndex];
}

// Process tap detection for a specific FSR sensor
void processTapDetection(int sensorIndex, int fsrValue) {
  unsigned long currentTime = millis();
  
  // Implement debounce for state changes
  if (currentTime - fsrState[sensorIndex].lastStateChangeTime < DEBOUNCE_TIME) {
    // Skip this iteration if we're within debounce period
    return;
  }
  
  // Detect press start
  if (fsrValue > TAP_THRESHOLD && !fsrState[sensorIndex].isPressed) {
    fsrState[sensorIndex].isPressed = true;
    fsrState[sensorIndex].pressStartTime = currentTime;
    fsrState[sensorIndex].lastStateChangeTime = currentTime;
    digitalWrite(LED_PIN, HIGH); // Visual feedback
    Serial.print("EVENT:TAP_START:");
    Serial.println(sensorIndex + 1);  // Send sensor number (1-4)
  }
  
  // Detect release
  else if (fsrValue <= TAP_THRESHOLD && fsrState[sensorIndex].isPressed) {
    fsrState[sensorIndex].isPressed = false;
    unsigned long pressDuration = currentTime - fsrState[sensorIndex].pressStartTime;
    fsrState[sensorIndex].lastStateChangeTime = currentTime;
    digitalWrite(LED_PIN, LOW);  // Turn off LED
    
    // Check if it was a hold
    if (pressDuration >= HOLD_TIME) {
      Serial.print("EVENT:HOLD:");
      Serial.println(sensorIndex + 1);
      fsrState[sensorIndex].tapCount = 0;  // Reset tap counter after hold
    }
    // Check if it was a tap
    else {
      // Check for double tap
      if (fsrState[sensorIndex].tapCount > 0 && 
          (currentTime - fsrState[sensorIndex].lastTapTime <= DOUBLE_TAP_TIME)) {
        Serial.print("EVENT:DOUBLE_TAP:");
        Serial.println(sensorIndex + 1);
        fsrState[sensorIndex].tapCount = 0;  // Reset tap counter
      }
      else {
        // First tap
        fsrState[sensorIndex].tapCount = 1;
        fsrState[sensorIndex].lastTapTime = currentTime;
        
        // Wait for potential second tap
        delay(5);  // Short delay to not block other functions
      }
    }
  }
  
  // Handle ongoing hold
  else if (fsrValue > TAP_THRESHOLD && fsrState[sensorIndex].isPressed) {
    if (currentTime - fsrState[sensorIndex].pressStartTime >= HOLD_TIME) {
      // Print hold notification once per second
      if ((currentTime - fsrState[sensorIndex].pressStartTime) % 1000 < 20) {
        Serial.print("EVENT:HOLDING:");
        Serial.println(sensorIndex + 1);
      }
    }
  }
  
  // After a certain amount of time without a second tap, declare it a single tap
  if (fsrState[sensorIndex].tapCount == 1 && 
      currentTime - fsrState[sensorIndex].lastTapTime > DOUBLE_TAP_TIME) {
    Serial.print("EVENT:SINGLE_TAP:");
    Serial.println(sensorIndex + 1);
    fsrState[sensorIndex].tapCount = 0;
  }
}

void loop() {
  // === WEIGHT SENSING FOR ALL LOAD CELLS ===
  static boolean newDataReady1 = 0;
  static boolean newDataReady2 = 0;
  static boolean newDataReady3 = 0;
  static boolean newDataReady4 = 0;

  // Check for new weight data on all load cells
  if (LoadCell1.update()) newDataReady1 = true;
  if (LoadCell2.update()) newDataReady2 = true;
  if (LoadCell3.update()) newDataReady3 = true;
  if (LoadCell4.update()) newDataReady4 = true;

  // Get weight values at the set interval
  if (millis() > t + serialPrintInterval) {
    if (newDataReady1) {
      float weight1 = LoadCell1.getData();
      Serial.print("WEIGHT:1:");
      Serial.println(weight1);
      newDataReady1 = 0;
    }
    
    if (newDataReady2) {
      float weight2 = LoadCell2.getData();
      Serial.print("WEIGHT:2:");
      Serial.println(weight2);
      newDataReady2 = 0;
    }
    
    if (newDataReady3) {
      float weight3 = LoadCell3.getData();
      Serial.print("WEIGHT:3:");
      Serial.println(weight3);
      newDataReady3 = 0;
    }
    
    if (newDataReady4) {
      float weight4 = LoadCell4.getData();
      Serial.print("WEIGHT:4:");
      Serial.println(weight4);
      newDataReady4 = 0;
    }
    
    t = millis();
  }

  // === TAP DETECTION FOR ALL FSRs ===
  int fsrPins[4] = {FSR_PIN1, FSR_PIN2, FSR_PIN3, FSR_PIN4};
  
  for (int i = 0; i < 4; i++) {
    int fsrValue = getSmoothedFSRReading(i, fsrPins[i]);
    processTapDetection(i, fsrValue);
  }
  
  // Process commands from Raspberry Pi
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.startsWith("TARE:")) {
      int sensorNum = command.substring(5).toInt();
      if (sensorNum >= 1 && sensorNum <= 4) {
        switch (sensorNum) {
          case 1:
            LoadCell1.tareNoDelay();
            break;
          case 2:
            LoadCell2.tareNoDelay();
            break;
          case 3:
            LoadCell3.tareNoDelay();
            break;
          case 4:
            LoadCell4.tareNoDelay();
            break;
        }
        Serial.print("STATUS:TARE_STARTED:");
        Serial.println(sensorNum);
      }
    }
    else if (command == "TARE_ALL") {
      LoadCell1.tareNoDelay();
      LoadCell2.tareNoDelay();
      LoadCell3.tareNoDelay();
      LoadCell4.tareNoDelay();
      Serial.println("STATUS:TARE_ALL_STARTED");
    }
    else if (command == "STATUS") {
      Serial.println("STATUS:OK");
    }
  }

  // Check if tares are complete
  if (LoadCell1.getTareStatus() == true) {
    Serial.println("STATUS:TARE_COMPLETE:1");
  }
  if (LoadCell2.getTareStatus() == true) {
    Serial.println("STATUS:TARE_COMPLETE:2");
  }
  if (LoadCell3.getTareStatus() == true) {
    Serial.println("STATUS:TARE_COMPLETE:3");
  }
  if (LoadCell4.getTareStatus() == true) {
    Serial.println("STATUS:TARE_COMPLETE:4");
  }
  
  // Small delay for stability
  delay(5);
}
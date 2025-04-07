#include <AFMotor.h>
#include <Servo.h>

// Servo for machine spin
Servo servo_body;

// Servo for dispenser
Servo servo_disp;

// DC motor for dispenser
AF_DCMotor motor(1);

int motorSpeed = 255; // 0 = stop, 255 = max

void setup() {
  // Turn on servos
  servo_body.attach(10); // pin 10 = machine body control
  servo_disp.attach(9); // pin 9 = dispenser control

  // Motor 1
  motor.setSpeed(motorSpeed);
  motor.run(RELEASE); // Off initialliy

  // Serial.begin(9600); // #TODO: make sure to use the same baud rate in RPI
}

// For ending test

void loop () {
  servo_body.write(0);
  servo_disp.write(0);
}

// For Demo body - machine

// void loop () {
//   servo_body.write(0);
//   delay(2000);
//   servo_body.write(45);
//   delay(2000);
//   servo_body.write(90);
//   delay(2000);
//   servo_body.write(135);
//   delay(2000);
//   servo_body.write(180);
//   delay(2000);
// }

// For Demo Dispenser

// void loop () {
// servo_body.write(0);
//   // 1. Turn dispenser servo to 180 degrees
//   servo_disp.write(180);
//   delay(500);  // small delay to let it get there (optional)

//   // 2. Turn motor on (FORWARD) for 0.5 seconds
//   motor.run(FORWARD);
//   delay(3000);  // 500ms spin time

//   // 3. Stop motor
//   motor.run(RELEASE);

//   // 4. Return dispenser servo to 0 degrees
//   servo_disp.write(0);
//   delay(2000);  // Wait before starting next cycle
// }


// void loop() {
//   servo_body.write(0);
//   Check if there is incoming data from the RPI
//   if (Serial.available() > 0) {
//     dispense = Serial.read() - '0'; // Read the incoming byte and convert it from ASCII to int

//     SECTION 1: Dispenser control
//     if (dispense) {
//       servo_body.write(180); // push
//       delay(1000); // #TODO: replace with DC motor control after figuring out battery problem
//       servo_body.write(0); // return
//       delay(1000); // placeholder delay for testing.
//     }

//     SECTION 2: Machine body control
//     if (move) {
//       servo_body.write(angle);
//     }
//   }
// }

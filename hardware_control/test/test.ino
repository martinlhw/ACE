#include <AFMotor.h>
#include <Servo.h>

// Servo for machine spin
Servo servo_body;

// Servo for dispenser
Servo servo_disp;

// DC motor for dispenser
AF_DCMotor motor(1);

void setup() {
  servo_body.attach(10); // pin 10 = machine body control
  servo_disp.attach(9); // pin 9 = dispenser control

  // Default position
  servo_body.write(90);
  servo_disp.write(180);

  // Defaut speed
  motor.setSpeed(255);
  motor.run(RELEASE); // RELEASE: stop, FORWARD: rotate forward

  for (int i = 0; i < 52; i++) {
    servo_disp.write(0);
    delay(1000);
    motor.run(FORWARD);
    delay(1000);
    motor.run(RELEASE);
    servo_disp.write(180);
    delay(3000);
  }

}

void loop() {
  
}

// Test function
void motorMove(int time) {
  for (int i = 0; i < time ; i++) {
    motor.run(FORWARD);
    delay(90);
    motor.run(RELEASE);
    delay(10);
  }
}

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
  motor.setSpeed(200);
  motor.run(RELEASE);

  for (int i = 0; i < 52; i++) {
    // Move Serovs to default position.
    servo_body.write(i*3);
    delay(500);
    servo_disp.write(40);
    delay(3000);
    servo_disp.write(180);
    delay(3000);
  }
}


void loop() {
  
}

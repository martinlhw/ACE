#include <AFMotor.h>
#include <Servo.h>



// 0: Only do community card test, 1: do player throws 
int big_test = 0;



// Servo for machine spin
Servo servo_body;

// Servo for dispenser
Servo servo_disp;

// DC motor for dispenser
AF_DCMotor motor(1);

int motorSpeed = 0; // 0 = stop, 255 = max
int close_speed = 120;
int far_speed = 120;

// Angles
int player_1_angle_1 = 150;
int player_1_angle_2 = 140;

int player_2_angle_1 = 120;
int player_2_angle_2 = 110;

int player_3_angle_1 = 70;
int player_3_angle_2 = 60;

int player_4_angle_1 = 40;
int player_4_angle_2 = 30;

void setup() {
  servo_body.attach(10); // pin 10 = machine body control
  servo_disp.attach(9); // pin 9 = dispenser control

  // Default position
  servo_body.write(90);
  servo_disp.write(180);
  motor.setSpeed(0);
  motor.run(RELEASE);

  // Community Card
  for (int i = 0; i < 5; i++) {
    // Turn body angle
    servo_body.write(70 + i * 10);

    // Push card
    servo_disp.write(30);
    delay(1000);

    // Shoot card
    motor.setSpeed(80);
    motor.run(FORWARD);
    delay(1000);
    motor.run(RELEASE);

    // Return servo for next card
    servo_disp.write(180);
    
    // Delay between dispenses
    delay(1000);
  }

  // Play card
  if (big_test) {
    for (int i = 0; i < 4; i++) {
      if (i == 0) {
        // Card 1
        servo_body.write(player_1_angle_1);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(far_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(500);
        
        // Card 2
        servo_body.write(player_1_angle_2);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(far_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(1000);
      }
      else if (i == 1) {
        // Card 1
        servo_body.write(player_2_angle_1);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(close_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(500);
        
        // Card 2
        servo_body.write(player_2_angle_2);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(close_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(1000);
      }
      else if (i == 2) {
        // Card 1
        servo_body.write(player_3_angle_1);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(close_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(500);
        
        // Card 2
        servo_body.write(player_3_angle_2);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(close_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(1000);
      }
      else {
        Card 1
        servo_body.write(player_4_angle_1);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(far_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(500);
        
        // Card 2
        servo_body.write(player_4_angle_2);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(far_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(1000);
      }
    }
  }
}

void loop() {
  
}

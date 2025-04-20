#include <AFMotor.h>
#include <Servo.h>

// Servo for machine spin
Servo servo_body;

// Servo for dispenser
Servo servo_disp;

// DC motor for dispenser
AF_DCMotor motor(1);

// default: 100
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

int big_test = 0;

void setup() {
  
  Serial.begin(9600); // #TODO: make sure to use the same baud rate in RPI
  while (!Serial) {
    ; // Wait until serial port is available
  }

  servo_body.attach(10); // pin 10 = machine body control
  servo_disp.attach(9); // pin 9 = dispenser control

  // Default position
  servo_body.write(90);
  servo_disp.write(180);
  motor.setSpeed(200);
  motor.run(RELEASE);


  // Community Card
  for (int i = 0; i < 1; i++) {
    servo_body.write(70 + i* 10);
    servo_disp.write(30);
    delay(1000);

    motor.setSpeed(80);
    motor.run(FORWARD);
    delay(1000);
    motor.run(RELEASE);

    servo_disp.write(180);
    delay(1000);  // Wait before starting next cycle
  }

  // People
  if (big_test) {
    for (int i = 0; i < 4; i++) {
      if (i == 0) {
        servo_body.write(player_1_angle_1);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(far_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(500);
        
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
        servo_body.write(player_2_angle_1);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(close_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(500);
        
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
        servo_body.write(player_3_angle_1);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(close_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(500);
        
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
        servo_body.write(player_4_angle_1);
        servo_disp.write(30);
        delay(1000);

        motor.setSpeed(far_speed);
        motor.run(FORWARD);
        delay(1000);
        motor.run(RELEASE);

        servo_disp.write(180);
        delay(500);
        
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

String inputString = "";
bool commandReady = false;

void loop() {
  // // Step 1: Read serial input character by character
  // while (Serial.available()) {
  //   char c = Serial.read();
    
  //   if (c == '\n') {
  //     commandReady = true;
  //     break;
  //   } else {
  //     inputString += c;
  //   }
  // }

  // // Step 2: Process complete command
  // if (commandReady) {
  //   if (inputString.startsWith("B")) {
  //     int angle = inputString.substring(1).toInt();
  //     if (angle >= 0 && angle <= 180) {
  //       servo_body.write(angle); // Move body servo to requested angle
  //     }
  //   }

  //   // Reset after processing
  //   inputString = "";
  //   commandReady = false;
  // }
}

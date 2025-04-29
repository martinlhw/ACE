#include <AFMotor.h>
#include <Servo.h>

// Servo for machine spin
Servo servo_body;

// Servo for dispenser
Servo servo_disp;

// DC motor for dispenser
AF_DCMotor motor(1);

int motor_speed = 0; // 0 = stop, 255 = max
int community_speed = 80;
int close_speed = 100;
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

// Saved value for re-dispense sequence
int last_dispense_speed = 0;

// RPI input
String input_string = "";
bool command_ready = false;

void setup() {
  // Connecting with RPI
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait until serial port is available
  }

  servo_body.attach(10); // pin 10 = machine body control
  servo_disp.attach(9); // pin 9 = dispenser control

  // Default position
  servo_body.write(90);
  servo_disp.write(180);
  motor.setSpeed(0);
  motor.run(RELEASE);
}

// Main loop
void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    
    if (c == '\n') {
      command_ready = true;
      break;
    } else {
      input_string += c;
    }
  }

  if (command_ready) {
    // Input check for proper format of "A" + "0" + "\n"
    if (input_string.length() >= 2) {
      char commandType = input_string.charAt(0);
      int commandValue = input_string.substring(1).toInt();

      // Game Phase - (0: preflop, 1: flop, 2: turn, 3: river)
      if (commandType == 'P') {
        if (commandValue == 0) {
          preflop();
        } else if (commandValue == 1) {
          flop();
        } else if (commandValue == 2) {
          turn();
        } else if (commandValue == 3) {
          river();
        }
      }

      // Body control
      else if (commandType == 'B') {
        if (commandValue == 1) {
          servo_body.write(player_1_angle_2);
          delay(30);
        } else if (commandValue == 2) {
          servo_body.write(player_2_angle_2);
          delay(30);
        } else if (commandValue == 3) {
          servo_body.write(player_3_angle_1);
          delay(30);
        } else if (commandValue == 4) {
          servo_body.write(player_4_angle_1);
          delay(30);
        }
      }

      // Dispenser control
      else if (commandType == 'D') {
        if (commandValue == 1) {
          give_card(player_1_angle_2, far_speed);
          delay(30);
        } else if (commandValue == 2) {
          give_card(player_2_angle_2, close_speed);
          delay(30);
        } else if (commandValue == 3) {
          give_card(player_3_angle_1, close_speed);
          delay(30);
        } else if (commandValue == 4) {
          give_card(player_4_angle_1, far_speed);
          delay(30);
        }
      }

      // Redo (Re-dispense)
      else if (commandType == 'R') {
        dispense(last_dispense_speed);
      }
    }

    // Reset after processing
    input_string = "";
    command_ready = false;
  }
}

// General dispense command
void dispense(int dispense_speed) {
  // Save dispense value
  last_dispense_speed = dispense_speed;

  // Push card
  servo_disp.write(30);
  delay(1000);

  // Shoot card
  motor.setSpeed(dispense_speed);
  motor.run(FORWARD);
  delay(1000);
  motor.run(RELEASE);

  // Return servo for next card
  servo_disp.write(180);
}

// Give card to specific player
void give_card(int playerangle, int dispense_speed) {
  servo_body.write(playerangle);
  dispense(dispense_speed);
}

void burn() {
  servo_body.write(180);
  dispense(80);
  servo_body.write(90);
}

void preflop() {
  for (int i = 0; i < 4; i++) {
    if (i == 0) {
      give_card(player_1_angle_1, far_speed);
      delay(500);
      give_card(player_1_angle_2, far_speed);
    }
    else if (i == 1) {
      give_card(player_2_angle_1, close_speed);
      delay(500);
      give_card(player_2_angle_2, close_speed);
    }
    else if (i == 2) {
      give_card(player_3_angle_1, close_speed);
      delay(500);
      give_card(player_3_angle_2, close_speed);
    }
    else {
      give_card(player_4_angle_1, far_speed);
      delay(500);
      give_card(player_4_angle_2, far_speed);
      serial.print("ack");
    }
  }
}

void flop() {
  burn();
  delay(500);
  // Community Card
  for (int i = 0; i < 3; i++) {
    // Turn body angle
    servo_body.write(70 + i * 10);
    dispense(community_speed);
    // Delay between dispenses
    delay(1000);
  }
  serial.print("ack");

}

void turn() {
  burn();
  delay(500);
  servo_body.write(100);
  dispense(community_speed);
  serial.print("ack");
}

void river() {
  burn();
  delay(500);
  servo_body.write(110);
  dispense(community_speed);
  serial.print("ack");
}

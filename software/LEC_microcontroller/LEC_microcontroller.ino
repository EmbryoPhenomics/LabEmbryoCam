/*
Script for Arduino UNO in the LabEmbryoCam tasked with receiving and passing on user interaction
with joystick and z-buttons, AND controlling the LED ring light used for illuminating the sample.
*/

/* MANUAL CONTROLS

Joystick
Pin 2 of X and Y connected to A0 and A1 respectively. 
Pin 1 connected to 5V
Pin 3 connected to ground.

Z Buttons
Pin 2 of buttons connected to A0 (up) and A1 (down) respectively, 
Pin 1 connected to ground.

*/ 

int Y = A0; // Joystick pin
int X = A1; // Joystick pin

int ret = 0; // For detecting port type

float x_val = 0; // Joystick return
float y_val = 0; // Joystick return

int old_x = 0; // Joystick previous return
int old_y = 0; // Joystick previous return

float zero_x_val = 0; // Zero
float zero_y_val = 0; // Zero

float x_float = 0;
float y_float = 0;

char out = ' ';

//  Set pin numbers for the two push buttons
const int buttonPinUp = 2;     // the number of the pushbutton pin for Z up
const int buttonPinDn = 3;    // push button pin for Z down

// Variables will change depending on the state of the buttons.
int buttonStateUp = 0; // Z-up button return
int buttonStateDn = 0; // Z-down button return


/*
LED ring
The LuMini rings need two data pins connected - A2 (16) & A3 (17) 
In addition to 5V and Ground.
*/

#include <FastLED.h>

#define NUM_LEDS 40
#define DATA_PIN 16
#define CLOCK_PIN 17

// Define the array of leds
CRGB ring[NUM_LEDS];

int brightness = 10; //Initial brightness

// Time delay for joystick signals
int dt = 15;

void setup() {
  // Joystick/z-button setup
  Serial.begin(115200); // setup serial
  Serial.println("joystick");
  delay(100);
  pinMode(buttonPinUp, INPUT_PULLUP);
  pinMode(buttonPinDn, INPUT_PULLUP);

  // Get zero position of joystick - note that the joystick needs to be centred
  zero_x_val = analogRead(X); // read X
  zero_y_val = analogRead(Y); // read Y

  
  
// Lighting setup
  Serial.begin(115200);
  Serial.println("light");
  LEDS.addLeds<APA102, DATA_PIN ,CLOCK_PIN, BGR>(ring, NUM_LEDS);
  //LEDS.addLeds<WS2811, DATA_PIN , BGR>(ring, NUM_LEDS);
  LEDS.setBrightness(brightness);
   // Rotate around the circle
  for (int i = 0; i < NUM_LEDS; i++) {
    ring[i] = CRGB::White;
    }
  FastLED.show();

  delay(1000);
}


void loop() {
/* 
If connection from Raspberry Pi is established via serial then parse input as a change
in the LED brightness
*/
  if (Serial.available() > 0){
    brightness = Serial.parseInt();
    brightness = brightness - 100; // To counteract zero reads from arduino being used as brightness

    if (brightness >= 0) {
      LEDS.setBrightness(brightness);
      FastLED.show();
      Serial.println(brightness);
    }
  }
/* 
Read state of the joystickr or z-buttons and send on the appropriate commands to the 
Raspberry Pi for downstream action as appropriate (e.g. send gcode to Duet XYZ board 
update the known position).
*/

  x_val = analogRead(X);
  y_val = analogRead(Y);

  x_float = x_val / zero_x_val; // read X
  y_float = y_val / zero_y_val; // read Y
  if (x_float < 1.35 && x_float > 1.2 && y_float <= 1.2 && y_float >= 0.8) {
    Serial.println("G0X0.02F10");
    delay(dt);
  }

  if (y_float < 1.35 && y_float > 1.2 && x_float <= 1.2 && x_float >= 0.8) {
    Serial.println("G0Y0.02F10");
    delay(dt);
  }

  if (x_float >= 1.35 && x_float < 1.7 && y_float <= 1.2 && y_float >= 0.8) {
    Serial.println("G0X0.2F100");
    delay(dt);
  }

  if (y_float >= 1.35 && y_float < 1.7 && x_float <= 1.2 && x_float >= 0.8) {
    Serial.println("G0Y0.2F100");
    delay(dt);
  }

  if (x_float >= 1.71 && y_float <= 1.2 && y_float >= 0.8) {
    Serial.println("G0X0.5F600");
    delay(dt);
  }

  if (y_float >= 1.71 && x_float <= 1.2 && x_float >= 0.8) {
    Serial.println("G0Y0.5F600");
    delay(dt);
  }

  if (x_float > 0.75 && x_float < 0.8 && y_float <= 1.2 && y_float >= 0.8) {
    Serial.println("G0X-0.02F10");
    delay(dt);
  }

  if (y_float > 0.75  && y_float < 0.8 && x_float <= 1.2 && x_float >= 0.8) {
    Serial.println("G0Y-0.02F10");
    delay(dt);
  }

  if (x_float > 0.3 && x_float <= 0.75 && y_float <= 1.2 && y_float >= 0.8) {
    Serial.println("G0X-0.2F100");
    delay(dt);
  }

  if (y_float >= 0.3 && y_float <= 0.75 && x_float <= 1.2 && x_float >= 0.8) {
    Serial.println("G0Y-0.2F100");
    delay(dt);
  }

  if (x_float <= 0.3 && y_float <= 1.2 && y_float >= 0.8) {
    Serial.println("G0X-0.5F600");
    delay(dt);
  }

  if (y_float <= 0.3 && x_float <= 1.2 && x_float >= 0.8) {
    Serial.println("G0Y-0.5F600");
    delay(dt);
  }

  // Diagonal movement
  if (x_float > 1.2 && y_float > 1.2) {
    Serial.println("G0X-0.05Y-0.05F600");
    delay(dt);
  }


  if (x_float < 0.8 && y_float < 0.8) {
    Serial.println("G0X-0.05Y-0.05F600");
    delay(dt);
  }

  if (x_float < 0.8 && y_float > 1.2) {
    Serial.println("G0X-0.05Y0.05F600");
    delay(dt);
  }

  if (x_float > 1.2 && y_float < 0.8) {
    Serial.println("G0X0.05Y-0.05F600");
    delay(dt);
  }

  // Z buttons
  buttonStateUp = digitalRead(buttonPinUp);
  buttonStateDn = digitalRead(buttonPinDn);

  if (buttonStateUp == HIGH && buttonStateDn == HIGH)
  {
    //Serial.println("Oops!");
  }

  //  If Up button pressed, send "Up" G-code.
  else if (buttonStateUp == HIGH)

  {
    Serial.println("G0Z-0.05F500");
    delay(dt);
  }

  //  If Down button pressed, send "Down" G-code.
  else if (buttonStateDn == HIGH)
  {
    Serial.println("G0Z0.05F500");
    delay(dt);
  }
}

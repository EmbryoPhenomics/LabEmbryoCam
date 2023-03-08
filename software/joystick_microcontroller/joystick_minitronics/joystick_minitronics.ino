// Joystick
// Pin 2 of X and Y connected to A0 and A1 respectively. Pin 1 connected to 5V, and Pin 3 connected to ground.
int Y = A0;
int X = A1;

int ret = 0; // For detecting port type

float x_val = 0;
float y_val = 0;


int old_x = 0;
int old_y = 0;

float zero_x_val = 0;
float zero_y_val = 0;

float x_float = 0;
float y_float = 0;

char out = ' ';

// Time delay for joystick signals
int dt = 15;


// Z buttons
// Pin 2 of Z up and Z down connected to A0 and A1 respectively, Pin 1 connected to ground.
//  Set pin numbers for the two push buttons
const int buttonPinUp = 2;     // the number of the pushbutton pin for Z up
const int buttonPinDn = 3;    // push button pin for Z down

// Variables will change depending on the state of the buttons.
int buttonStateUp = 0;         // variable for reading the pushbutton status
int buttonStateDn = 0;         // variable for reading the pushbutton status

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200); // setup serial
  Serial.println("joystick");
  delay(100);
  pinMode(buttonPinUp, INPUT_PULLUP);
  pinMode(buttonPinDn, INPUT_PULLUP);

  // Get zero position of joystick - note that the joystick needs to be centred
  zero_x_val = analogRead(X); // read X
  zero_y_val = analogRead(Y); // read Y

  delay(1000);

}





void loop() {

  // put your main code here, to run repeatedly:
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

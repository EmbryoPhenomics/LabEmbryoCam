#include <FastLED.h>

// How many leds in your strip? Uncomment the corresponding line
#define NUM_LEDS 40

// The LuMini rings need two data pins connected - A2 & A3
#define DATA_PIN 16
#define CLOCK_PIN 17

// Define the array of leds
CRGB ring[NUM_LEDS];

int brightness = 10;

void setup() {
  Serial.begin(115200);
  Serial.println("light");
  LEDS.addLeds<APA102, DATA_PIN ,CLOCK_PIN, BGR>(ring, NUM_LEDS);
  //LEDS.addLeds<WS2811, DATA_PIN , BGR>(ring, NUM_LEDS);
  LEDS.setBrightness(brightness);
   // //Rotate around the circle
  for (int i = 0; i < NUM_LEDS; i++) {
    // Set the i'th led to the current hue
    ring[i] = CRGB::White;
    }
  FastLED.show();
}

void loop() {
  if (Serial.available() > 0){
    brightness = Serial.parseInt();
    brightness = brightness - 100; // To counteract zero reads from arduino being used as brightness

    if (brightness >= 0) {
      LEDS.setBrightness(brightness);
      FastLED.show();
      Serial.println(brightness);
    }
  }
}
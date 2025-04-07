#define SWITCH_PIN 22  // The pin where the switch is connected

void setup() {
  Serial.begin(9600);
  pinMode(SWITCH_PIN, INPUT_PULLUP);  // Enable internal pull-up resistor
}

void loop() {
  int raw1 = analogRead(A0);
  int raw2 = analogRead(A1);

  float pressure1 = (raw1 * 5.0 / 1023.0 - 0.5) * 25.0;
  float pressure2 = (raw2 * 5.0 / 1023.0 - 0.5) * 25.0;

  // Read switch state (LOW when pressed, HIGH when open)
  int switchState = digitalRead(SWITCH_PIN);

  // Send as CSV: timestamp, pressure1, pressure2, switchState
  Serial.print(millis());
  Serial.print(",");
  Serial.print(pressure1);
  Serial.print(",");
  Serial.print(pressure2);
  Serial.print(",");
  Serial.println(switchState);  // 0 when pressed, 1 when open

  delay(10);  // 100 Hz
}


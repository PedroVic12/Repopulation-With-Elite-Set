const int LED_PINS[] = {2, 3, 4};
const int BUTTON_PINS[] = {5, 6, 7};
const int VOLTAGE_PIN = A0;

void setup() {
  Serial.begin(9600);
  
  for (int i = 0; i < 3; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
  }
}

void loop() {
  for (int i = 0; i < 3; i++) {
    if (digitalRead(BUTTON_PINS[i]) == LOW) {
      digitalWrite(LED_PINS[i], HIGH);
    } else {
      digitalWrite(LED_PINS[i], LOW);
    }
  }

  int voltageValue = analogRead(VOLTAGE_PIN);
  float voltage = voltageValue * (5.0 / 1023.0);

  Serial.print("LED_STATUS:");
  for (int i = 0; i < 3; i++) {
    Serial.print(digitalRead(LED_PINS[i]));
    if (i < 2) Serial.print(",");
  }
  Serial.print(";VOLTAGE:");
  Serial.println(voltage, 2);

  delay(100);
}
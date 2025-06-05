
// sudo chmod 666 /dev/ttyUSB0

// === Classes organizadas ===
class SensorRC {
  int pin;
public:
  SensorRC(int analogPin) {
    pin = analogPin;
  }

  float readVoltage() {
    int value = analogRead(pin);
    return (value * 5.0) / 1023.0;
  }
};

class LedControl {
  int pin;
  bool estado;
public:
  LedControl(int outputPin) {
    pin = outputPin;
    pinMode(pin, OUTPUT);
    estado = false;
  }

  void on() {
    digitalWrite(pin, HIGH);
    estado = true;
  }

  void off() {
    digitalWrite(pin, LOW);
    estado = false;
  }

  void blink(int times, int delayMs, String motivo) {
    Serial.print("LED vermelho piscando (");
    Serial.print(motivo);
    Serial.println(")");
    for (int i = 0; i < times; i++) {
      on();
      delay(delayMs);
      off();
      delay(delayMs);
    }
  }

  bool isOn() {
    return estado;
  }
};

// === Pinos ===
const int botaoVerdePin = 2;
const int botaoAmareloPin = 3;

// === Instâncias ===
SensorRC capacitor(A1);
LedControl ledVerde(8);
LedControl ledVermelho(9);

void setup() {
  Serial.begin(9600);
  pinMode(botaoVerdePin, INPUT_PULLUP);   // Botão com resistor pullup interno
  pinMode(botaoAmareloPin, INPUT_PULLUP);

}

void loop() {
  float carga = capacitor.readVoltage();
  Serial.print("Tensão no capacitor: ");
  Serial.print(carga);
  Serial.println(" V");

  bool botaoVerde = digitalRead(botaoVerdePin) == LOW;
  bool botaoAmarelo = digitalRead(botaoAmareloPin) == LOW;

  if (botaoVerde) {
    Serial.println("Botão VERDE pressionado - Iniciando CARGA");
    if (!ledVerde.isOn()) {
      ledVerde.on();
      Serial.println("LED Verde: LIGADO");
    }
    ledVerde.on();
    ledVermelho.blink(1, 200, "CARGA");
  }

  if (botaoAmarelo) {
    Serial.println("Botão AMARELO pressionado - Iniciando DESCARGA");
    if (ledVerde.isOn()) {
      ledVerde.off();
      Serial.println("LED Verde: DESLIGADO");
    }
    ledVermelho.blink(4, 200, "DESCARGA");
  }

  delay(1000);
}

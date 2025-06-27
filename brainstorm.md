
#include <Arduino.h>

// Defina os pinos para o sensor TCS3200
#define S0 4
#define S1 5
#define S2 6
#define S3 7
#define sensorOut 8

// Defina os pinos para os relés
#define rele1 9
#define rele2 10

unsigned int red = 0;
unsigned int green = 0;
unsigned int blue = 0;

void setup() {
  Serial.begin(9600);
  
  // Configuração dos pinos do sensor TCS3200
  pinMode(S0, OUTPUT);
  pinMode(S1, OUTPUT);
  pinMode(S2, OUTPUT);
  pinMode(S3, OUTPUT);
  pinMode(sensorOut, INPUT);
  
  digitalWrite(S0, HIGH);
  digitalWrite(S1, LOW);

  // Configuração dos pinos dos relés
  pinMode(rele1, OUTPUT);
  pinMode(rele2, OUTPUT);
  
  // Inicialmente, ambos os relés estão desligados
  digitalWrite(rele1, LOW);
  digitalWrite(rele2, LOW);
}

void loop() {
  // Lê os valores RGB
  readRGB();
  
  // Decide a ação com base nos valores RGB
  decideAction();
  
  delay(50); // Pode ajustar este delay conforme necessário
}

void readRGB() {
  // Lê o valor vermelho
  digitalWrite(S2, LOW);
  digitalWrite(S3, LOW);
  red = pulseIn(sensorOut, LOW);
  delay(10);

  // Lê o valor verde
  digitalWrite(S2, HIGH);
  digitalWrite(S3, HIGH);
  green = pulseIn(sensorOut, LOW);
  delay(10);

  // Lê o valor azul
  digitalWrite(S2, LOW);
  digitalWrite(S3, HIGH);
  blue = pulseIn(sensorOut, LOW);
  delay(10);

  // Imprime os valores RGB no monitor serial
  Serial.print("R: ");
  Serial.print(red);
  Serial.print("\tG: ");
  Serial.print(green);
  Serial.print("\tB: ");
  Serial.println(blue);
}

void decideAction() {
  if (red < 60 && green > 90 && blue > 60) {
    // Vermelho: Vai para a direita
    digitalWrite(rele1, LOW);  // Motor direito ligado
    digitalWrite(rele2, HIGH); // Motor esquerdo desligado
    delay(700);  // Vira por 500ms. Ajuste conforme necessário.
    digitalWrite(rele1, LOW);  // Motor direito ligado
    digitalWrite(rele2, LOW);  // Motor esquerdo ligado
    delay(10);
  } 
  else if (red > 50 && green < 50 && blue < 60) {
    // Verde: Vai para frente
    digitalWrite(rele1, LOW);  // Motor direito ligado
    digitalWrite(rele2, LOW);  // Motor esquerdo ligado
  } 
  else if (red > 80 && green > 50 && blue < 60) {
    // Azul: Vai para a esquerda
    digitalWrite(rele1, HIGH); // Motor direito desligado
    digitalWrite(rele2, LOW);  // Motor esquerdo ligado
    delay(700);  // Vira por 500ms. Ajuste conforme necessário.
    digitalWrite(rele1, LOW);  // Motor direito ligado
    digitalWrite(rele2, LOW);  // Motor esquerdo ligado
    delay(10);
  } 
  else if (red > 150 && green > 145 && blue > 100) {
    // Preto: Parar
    digitalWrite(rele1, HIGH); // Motor direito desligado
    digitalWrite(rele2, HIGH); // Motor esquerdo desligado
  }
}


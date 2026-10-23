#include <IRremote.hpp>  // biblioteca IRremote para ler o controle remoto

// biblioteca dos sensores laterais
#include <Wire.h>
#include <VL53L0X.h>

// https://simplifycpp.org/

#define IR_RECEIVE_PIN 11     // Receptor infravermelho
#define SENSOR_LINHA   A0     // Sensor de refletância (borda branca)
#define TRIG           A2     // Ultrassônico
#define ECHO           A3

// Sensores laser VL53L0X (I2C: SDA = A4, SCL = A5)
#define XSHUT_SENSOR1  7
#define XSHUT_SENSOR2  8
#define SENSOR1_ENDERECO 42
#define SENSOR2_ENDERECO 43

// Teclas do Controle Remoto
#define READY_CODE 0x80       // Tecla 1
#define START_CODE 0x81       // Tecla 2
#define STOP_CODE  0x82       // Tecla 3

// Motor esquerdo
const int IN1_ESQ = 10;
const int IN2_ESQ = 9;

// Motor direito
const int IN3_DIR = 6;
const int IN4_DIR = 5;

// Valores de PWM
const int PWM_MAX   = 255;    // Potência máxima 
const int PWM_RE    = 255;    // Potência da ré
const int PWM_GIRO  = 180;    // Potência do giro de 180° na borda
const int PWM_BUSCA = 127;    // 50% de duty cycle 


// Variáveis de controle
const unsigned long TEMPO_RE   = 1000;  // ~10 a 20 cm para trás (1 segundo) 
const unsigned long TEMPO_GIRO = 650;  // ~180° (calibrar)
const int LIMIAR = 700;       // Calibrar ao detectador borda
const bool BRANCO_E_MAIOR = false;
const int DISTANCIA_ATAQUE = 40;  

// Sensores laser
const unsigned long INTERVALO_LASER = 1000;  // envio serial a cada 1 s
VL53L0X Sensor1;
VL53L0X Sensor2;
unsigned long ultimoEnvioLaser = 0;

unsigned long lerControle() {
  unsigned long codigo = 0;
  if (IrReceiver.decode()) {
    codigo = IrReceiver.decodedIRData.decodedRawData;
    IrReceiver.resume();
  }
  // Retorna o código do botão recebido (0 se nada foi recebido)
  return codigo;
}

// ---------------- Motores ----------------
void motorEsquerdo(int pwm) {  
    analogWrite(IN1_ESQ, pwm);  
    analogWrite(IN2_ESQ, 0); 
    analogWrite(IN1_ESQ, 0);    
    analogWrite(IN2_ESQ, pwm); 
  
}

void motorDireito(int pwm) {
    analogWrite(IN3_DIR, pwm);  
    analogWrite(IN4_DIR, 0); 
    analogWrite(IN3_DIR, 0);    
    analogWrite(IN4_DIR, pwm); 
}

void parar() {
  motorEsquerdo(0);
  motorDireito(0);
}

void andarFrente(int pwm) {
    analogWrite(IN1_ESQ, pwm);  
    analogWrite(IN2_ESQ, 0); 
    analogWrite(IN3_DIR, 0);    
    analogWrite(IN4_DIR, pwm);
}

void andarTras(int pwm) {
    analogWrite(IN1_ESQ, 0);  
    analogWrite(IN2_ESQ, pwm); 
    analogWrite(IN3_DIR, pwm);    
    analogWrite(IN4_DIR, 0);
}


void girarHorario(int pwm) {
    analogWrite(IN1_ESQ, pwm);  
    analogWrite(IN2_ESQ, 0); 
    analogWrite(IN3_DIR, pwm);    
    analogWrite(IN4_DIR, 0);
}

// ---------------- Sensores ----------------
bool bordaBrancaDetectada() {
  int valor = analogRead(SENSOR_LINHA);
  return BRANCO_E_MAIOR ? (valor > LIMIAR) : (valor < LIMIAR);
}

long medirDistanciaCm() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  // medindo o tempo de retorno
  duracao = pulseIn(ECHO, HIGH); 

  // calcula a distancia em cm/s
  float vel_som = 0.0343;
  distancia = duracao * vel_som / 2;

  Serial.print("\nDistancia: ");
  Serial.print(distancia);
  Serial.print(" cm");

  return distancia;
}

void finalizar() {
  parar();
  Serial.println(F("PARAR - FIM"));
  // gambiarra do professor para parar dentro do loop
  while (1);
}

void lerSensores()
{
  //Lê a distância em centímetros.
  int measure1 = Sensor1.readRangeContinuousMillimeters()*0.1;
  int measure2 = Sensor2.readRangeContinuousMillimeters()*0.1;
  bool detectado = false;
  const int distanciaMin = 0;
  const int distanciaMax = 25;

  //Mostra o resultado no monitor serial.
  Serial.print(measure1);
  Serial.println("cm");
  Serial.print('\n');
  Serial.print(measure2);
  Serial.println("cm");
  Serial.println();

  delay(1000);

  //Verifica se a leitura está dentro dos parâmetros de detecção.
  if((measure1 > distanciaMin) && (measure1 <= distanciaMax) || (measure2 > distanciaMin) && (measure2 <= distanciaMax)) {
    Serial.println("Detectou!");
    detectado = true;
  }
  else {
    Serial.println ("Nenhum objeto detectado."); 
  }
}

// =====================================================================

void configPinos(){

  // motores
  pinMode(IN1_ESQ, OUTPUT);
  pinMode(IN2_ESQ, OUTPUT);
  pinMode(IN3_DIR, OUTPUT);
  pinMode(IN4_DIR, OUTPUT);

  // sensores digitais
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  // Sensor analogico
  pinMode(SENSOR_LINHA, INPUT);
}



void configSensoresLaser() {
  // Desliga os dois sensores (XSHUT em LOW)
  pinMode(XSHUT_SENSOR1, OUTPUT);
  pinMode(XSHUT_SENSOR2, OUTPUT);

  Wire.begin();

  // Liga um por vez e troca o endereço I2C
  pinMode(XSHUT_SENSOR2, INPUT);
  delay(10);
  Sensor2.setAddress(SENSOR2_ENDERECO);

  pinMode(XSHUT_SENSOR1, INPUT);
  delay(10);
  Sensor1.setAddress(SENSOR1_ENDERECO);

  if (!Sensor1.init()) Serial.println(F("Falha ao iniciar Sensor1"));
  if (!Sensor2.init()) Serial.println(F("Falha ao iniciar Sensor2"));

  Sensor1.setTimeout(500);
  Sensor2.setTimeout(500);

  Sensor1.startContinuous();
  Sensor2.startContinuous();
}

void on_event_button2(){
  // O botão 2 foi pressionado? NÃO -> continua esperando | SIM -> segue para o LOOP
  Serial.println(F("Aguardando botao 2 para INICIAR..."));
  unsigned long ultimoPrint = 0;
  while (lerControle() != START_CODE) {

    if (millis() - ultimoPrint > 300) {
      ultimoPrint = millis();
      // Serial.print(F("Sensor A0 = "));
      // Serial.print(analogRead(SENSOR_LINHA));
      // Serial.print(F(" -> "));
      //Serial.println(bordaBrancaDetectada() ? F("BRANCO") : F("PRETO"));
    }

    lerSensores();
  }
  Serial.println(F("INICIAR"));
}

void on_event_button3(){
  // O botão 3 foi pressionado? - Desligar
  if (lerControle() == STOP_CODE) {
    finalizar();
  }
}

void on_event_button1(){
    if (IrReceiver.decodedIRData.decodedRawData == READY_CODE) {  
      parar();
    }
}

// ------------------------------------------------------------

void setup() {
  // Configuração inicial
  Serial.begin(9600);
  IrReceiver.begin(IR_RECEIVE_PIN);
  configPinos();
  configSensoresLaser();

  // Aguardando o btn 2 ser pressionado
  on_event_button2();
  Serial.println("fim dos logs agora");
}


void loop() {
  lerSensores();

  if (bordaBrancaDetectada()) {
    // SIM: andar para trás (10 a 20 cm) e girar ~180°
    andarTras(PWM_RE);
    delay(TEMPO_RE);
    girarHorario(PWM_GIRO);
    delay(TEMPO_GIRO);

  } else {
    long D = medirDistanciaCm();

    if (D < DISTANCIA_ATAQUE) {
      andarFrente(PWM_MAX);
    } 
    else {
      girarHorario(PWM_BUSCA);    // (uma roda para frente e a outra para trás) PWM de 50%
    }
  }

  // O botão 3 foi pressionado? - Desligar
  if (lerControle() == STOP_CODE) {
    finalizar();
  }

}
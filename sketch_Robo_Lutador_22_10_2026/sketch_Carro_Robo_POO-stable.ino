#include <Arduino.h>
#include <IRremote.hpp>
#include <Wire.h>
#include <VL53L0X.h>

constexpr uint8_t IR_RECEIVE_PIN = 11;
constexpr uint8_t SENSOR_LINHA = A0;
constexpr uint8_t TRIG = A2;
constexpr uint8_t ECHO = A3;

constexpr uint8_t XSHUT_SENSOR1 = 7;
constexpr uint8_t XSHUT_SENSOR2 = 8;
constexpr uint8_t SENSOR1_ENDERECO = 42;
constexpr uint8_t SENSOR2_ENDERECO = 43;

constexpr unsigned long READY_CODE = 0x80; // Botao 1: pausa
constexpr unsigned long START_CODE = 0x81; // Botao 2: iniciar/retomar
constexpr unsigned long STOP_CODE = 0x82;  // Botao 3: parada definitiva
constexpr unsigned long STRATEGY_7_CODE = 0x86;
constexpr unsigned long STRATEGY_8_CODE = 0x87;
constexpr unsigned long STRATEGY_9_CODE = 0x88;

constexpr uint8_t IN1_ESQ = 10;
constexpr uint8_t IN2_ESQ = 9;
constexpr uint8_t IN3_DIR = 6;
constexpr uint8_t IN4_DIR = 5;

constexpr int PWM_MAX = 255;
constexpr int PWM_RE = 220;
constexpr int PWM_GIRO = 180;
constexpr int PWM_BUSCA = 140;
constexpr int PWM_AVANCO_AGRESSIVO = 200;

constexpr unsigned long TEMPO_RE = 400;
constexpr unsigned long TEMPO_GIRO = 500;
constexpr unsigned long INTERVALO_BUSCA_8 = 500;
constexpr unsigned long INTERVALO_BUSCA_9 = 300;
constexpr int LIMIAR_LINHA = 700;
constexpr bool BRANCO_E_MAIOR = false;
constexpr long DISTANCIA_ATAQUE_CM = 40;
constexpr int DISTANCIA_LASER_CM = 25;

VL53L0X Sensor1;
VL53L0X Sensor2;

enum class Estrategia : uint8_t
{
    Nenhuma,
    AvancoAgressivo,
    VarreduraHorario,
    VarreduraAntiHorario
};

enum class FaseBorda : uint8_t
{
    Normal,
    Recuando,
    Girando
};

Estrategia estrategia = Estrategia::Nenhuma;
FaseBorda faseBorda = FaseBorda::Normal;
unsigned long inicioFaseBorda = 0;
unsigned long ultimaMudancaBusca = 0;
bool pausado = false;
int sentidoBusca = 1;

unsigned long lerControle()
{
    if (!IrReceiver.decode())
    {
        return 0;
    }

    const unsigned long codigo = IrReceiver.decodedIRData.decodedRawData;
    IrReceiver.resume();
    return codigo;
}

void configurarMotor(uint8_t pinoFrente, uint8_t pinoRe, int potencia)
{
    potencia = constrain(potencia, -PWM_MAX, PWM_MAX);

    if (potencia > 0)
    {
        analogWrite(pinoRe, 0);
        analogWrite(pinoFrente, potencia);
    }
    else if (potencia < 0)
    {
        analogWrite(pinoFrente, 0);
        analogWrite(pinoRe, -potencia);
    }
    else
    {
        analogWrite(pinoFrente, 0);
        analogWrite(pinoRe, 0);
    }
}

void definirMotores(int potenciaEsquerda, int potenciaDireita)
{
    configurarMotor(IN1_ESQ, IN2_ESQ, potenciaEsquerda);
    configurarMotor(IN4_DIR, IN3_DIR, potenciaDireita);
}

void parar()
{
    definirMotores(0, 0);
}

void andarFrente(int potencia)
{
    definirMotores(potencia, potencia);
}

void andarTras(int potencia)
{
    definirMotores(-potencia, -potencia);
}

void girarHorario(int potencia)
{
    definirMotores(potencia, -potencia);
}

void girarAntiHorario(int potencia)
{
    definirMotores(-potencia, potencia);
}

bool bordaBrancaDetectada()
{
    const int valor = analogRead(SENSOR_LINHA);
    return BRANCO_E_MAIOR ? valor > LIMIAR_LINHA : valor < LIMIAR_LINHA;
}

long medirDistanciaCm()
{
    digitalWrite(TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG, LOW);

    const unsigned long duracao = pulseIn(ECHO, HIGH, 25000UL);
    if (duracao == 0)
    {
        return 999;
    }

    return static_cast<long>(duracao * 0.0343f / 2.0f);
}

int lerDistanciaLaserCm(VL53L0X &sensor)
{
    const uint16_t milimetros = sensor.readRangeContinuousMillimeters();
    if (sensor.timeoutOccurred() || milimetros == 0 || milimetros >= 8190)
    {
        return 0;
    }

    return milimetros / 10;
}

bool configurarSensoresLaser()
{
    pinMode(XSHUT_SENSOR1, OUTPUT);
    pinMode(XSHUT_SENSOR2, OUTPUT);
    digitalWrite(XSHUT_SENSOR1, LOW);
    digitalWrite(XSHUT_SENSOR2, LOW);
    Wire.begin();

    pinMode(XSHUT_SENSOR2, INPUT);
    delay(10);
    if (!Sensor2.init())
    {
        Serial.println(F("Falha ao iniciar Sensor2."));
        return false;
    }
    Sensor2.setAddress(SENSOR2_ENDERECO);

    pinMode(XSHUT_SENSOR1, INPUT);
    delay(10);
    if (!Sensor1.init())
    {
        Serial.println(F("Falha ao iniciar Sensor1."));
        return false;
    }
    Sensor1.setAddress(SENSOR1_ENDERECO);

    Sensor1.setTimeout(50);
    Sensor2.setTimeout(50);
    Sensor1.startContinuous();
    Sensor2.startContinuous();
    return true;
}

bool configurarPinos()
{
    pinMode(IN1_ESQ, OUTPUT);
    pinMode(IN2_ESQ, OUTPUT);
    pinMode(IN3_DIR, OUTPUT);
    pinMode(IN4_DIR, OUTPUT);
    pinMode(TRIG, OUTPUT);
    pinMode(ECHO, INPUT);
    pinMode(SENSOR_LINHA, INPUT);
    pinMode(LED_BUILTIN, OUTPUT);

    digitalWrite(TRIG, LOW);
    parar();
    return configurarSensoresLaser();
}

void piscarLedInicializacao()
{
    for (uint8_t piscada = 0; piscada < 3; ++piscada)
    {
        digitalWrite(LED_BUILTIN, HIGH);
        delay(150);
        digitalWrite(LED_BUILTIN, LOW);
        delay(150);
    }
}

void pararDefinitivamente()
{
    parar();
    Serial.println(F("Parada definitiva. Reinicie o Arduino para voltar a operar."));
    while (true)
    {
        parar();
    }
}

void selecionarEstrategia(unsigned long codigo)
{
    switch (codigo)
    {
    case STRATEGY_7_CODE:
        estrategia = Estrategia::AvancoAgressivo;
        sentidoBusca = 1;
        Serial.println(F("Estrategia 7 selecionada: avanco agressivo."));
        break;
    case STRATEGY_8_CODE:
        estrategia = Estrategia::VarreduraHorario;
        sentidoBusca = 1;
        Serial.println(F("Estrategia 8 selecionada: varredura alternada, horario primeiro."));
        break;
    case STRATEGY_9_CODE:
        estrategia = Estrategia::VarreduraAntiHorario;
        sentidoBusca = -1;
        Serial.println(F("Estrategia 9 selecionada: varredura alternada, anti-horario primeiro."));
        break;
    default:
        return;
    }

    ultimaMudancaBusca = millis();
}

void aguardarInicio()
{
    Serial.println(F("Selecione a estrategia 7, 8 ou 9; depois pressione 2 para iniciar."));

    while (true)
    {
        const unsigned long codigo = lerControle();
        if (codigo == STOP_CODE)
        {
            pararDefinitivamente();
        }

        if (codigo == STRATEGY_7_CODE || codigo == STRATEGY_8_CODE || codigo == STRATEGY_9_CODE)
        {
            selecionarEstrategia(codigo);
        }
        else if (codigo == START_CODE)
        {
            if (estrategia == Estrategia::Nenhuma)
            {
                Serial.println(F("Escolha primeiro a estrategia 7, 8 ou 9."));
            }
            else
            {
                Serial.println(F("Combate iniciado."));
                return;
            }
        }
    }
}

bool processarControles()
{
    const unsigned long codigo = lerControle();
    if (codigo == STOP_CODE)
    {
        pararDefinitivamente();
    }

    if (codigo == READY_CODE)
    {
        pausado = true;
        faseBorda = FaseBorda::Normal;
        parar();
        Serial.println(F("Pausado. Pressione 2 para retomar."));
    }
    else if (codigo == START_CODE && pausado)
    {
        pausado = false;
        ultimaMudancaBusca = millis();
        Serial.println(F("Retomando."));
    }

    if (pausado)
    {
        parar();
    }
    return pausado;
}

bool processarRecuperacaoBorda()
{
    const unsigned long agora = millis();

    if (faseBorda == FaseBorda::Recuando)
    {
        if (agora - inicioFaseBorda >= TEMPO_RE)
        {
            girarHorario(PWM_GIRO);
            faseBorda = FaseBorda::Girando;
            inicioFaseBorda = agora;
        }
        return true;
    }

    if (faseBorda == FaseBorda::Girando)
    {
        if (agora - inicioFaseBorda >= TEMPO_GIRO)
        {
            faseBorda = FaseBorda::Normal;
            parar();
        }
        return true;
    }

    if (bordaBrancaDetectada())
    {
        Serial.println(F("Borda detectada: recuando e girando."));
        andarTras(PWM_RE);
        faseBorda = FaseBorda::Recuando;
        inicioFaseBorda = agora;
        return true;
    }

    return false;
}

void executarBusca()
{
    if (estrategia == Estrategia::AvancoAgressivo)
    {
        andarFrente(PWM_AVANCO_AGRESSIVO);
        return;
    }

    const unsigned long intervalo = estrategia == Estrategia::VarreduraHorario
                                        ? INTERVALO_BUSCA_8
                                        : INTERVALO_BUSCA_9;
    if (millis() - ultimaMudancaBusca >= intervalo)
    {
        sentidoBusca = -sentidoBusca;
        ultimaMudancaBusca = millis();
    }

    if (sentidoBusca > 0)
    {
        girarHorario(PWM_BUSCA);
    }
    else
    {
        girarAntiHorario(PWM_BUSCA);
    }
}

void setup()
{
    Serial.begin(9600);
    IrReceiver.begin(IR_RECEIVE_PIN);

    if (!configurarPinos())
    {
        parar();
        Serial.println(F("Inicializacao interrompida. Verifique os sensores e a fiacao."));
        while (true)
        {
            parar();
        }
    }

    piscarLedInicializacao();
    aguardarInicio();
}

void loop()
{
    if (processarControles())
    {
        return;
    }

    if (processarRecuperacaoBorda())
    {
        return;
    }

    const long distanciaFrontal = medirDistanciaCm();
    const int distanciaSensor1 = lerDistanciaLaserCm(Sensor1);
    const int distanciaSensor2 = lerDistanciaLaserCm(Sensor2);
    const bool alvoSensor1 = distanciaSensor1 > 0 && distanciaSensor1 < DISTANCIA_LASER_CM;
    const bool alvoSensor2 = distanciaSensor2 > 0 && distanciaSensor2 < DISTANCIA_LASER_CM;

    if ((distanciaFrontal > 0 && distanciaFrontal < DISTANCIA_ATAQUE_CM) ||
        (alvoSensor1 && alvoSensor2))
    {
        andarFrente(PWM_MAX);
    }
    else if (alvoSensor1)
    {
        girarAntiHorario(PWM_GIRO);
    }
    else if (alvoSensor2)
    {
        girarHorario(PWM_GIRO);
    }
    else
    {
        executarBusca();
    }
}


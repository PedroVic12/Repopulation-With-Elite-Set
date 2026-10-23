/*
 * ===================================================================================
 * ARQUIVO DE CABEÇALHO: CONFIGURAÇÕES E PINAGEM DO ROBÔ LUTADOR (SUMÔ)
 * UFF - LABORATÓRIO DE ENG. ELÉTRICA (PROF. FELIPE SASS - GRUPO 1 2026)
 * ===================================================================================
 */

#ifndef ROBOT_CONFIG_H
#define ROBOT_CONFIG_H

#include <Arduino.h>

// --- RECEPTOR INFRAVERMELHO & CONTROLE SONY ---
#define IR_RECEIVE_PIN 11

#define BUTTON_1_CODE 0x80 // Tecla 1: Preparar / Mover para frente
#define BUTTON_2_CODE 0x81 // Tecla 2: Iniciar / Varredura e Busca (START)
#define BUTTON_3_CODE 0x82 // Tecla 3: Parar Definitivo (STOP FIM)
#define BUTTON_4_CODE 0x83 // Tecla 4: Emergência / Reset

// --- PINOS DOS SENSORES ---
#define PIN_SENSOR_QRE_LINHA A0  // QRE1113 - Refletância
#define PIN_ULTRASSONICO_TRIG A4 // HC-SR04 Trigger
#define PIN_ULTRASSONICO_ECHO A3 // HC-SR04 Echo

// --- PINOS DA PONTE H L298N ---
const int IN1_MOTOR_ESQUERDO = 10;
const int IN2_MOTOR_ESQUERDO = 9;
const int IN3_MOTOR_DIREITO  = 6;
const int IN4_MOTOR_DIREITO  = 5;

// --- TIPOS E ESTRUTURAS PÚBLICAS ---
struct PinosMotor {
    int in1;
    int in2;
    int in3;
    int in4;
};

struct ConfigPWM {
    int maxPotencia; // PWM máximo de ataque (255)
    int re;          // PWM marcha ré (200)
    int giro;        // PWM giro (190)
};

struct EstadoSensor {
    int valorQRE;
    bool naBordaBranca;
    float distanciaCm;
};

// Enumeração dos Tipos de Estado do Robô (robotState)
enum robotState {
    ESTADO_PARADO,
    ESTADO_PREPARAR,
    ESTADO_BUSCAR,
    ESTADO_ATACAR,
    ESTADO_ESQUIVAR_BORDA,
    ESTADO_PARADO_DEFINITIVO // ESTADO FIM DO FLUXOGRAMA
};

// Constantes de Limiar
const int LIMIAR_BORDA_QRE = 700;
const float DISTANCIA_ATENCAO_CM = 20.0;

#endif // ROBOT_CONFIG_H

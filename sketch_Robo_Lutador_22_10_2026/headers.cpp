#include "headers.h"

// Definições globais de configuração padrão de hardware
PinosMotor pinosMotoresPadrao = {
    IN1_MOTOR_ESQUERDO,
    IN2_MOTOR_ESQUERDO,
    IN3_MOTOR_DIREITO,
    IN4_MOTOR_DIREITO
};

ConfigPWM configPwmPadrao = {
    255, // Potência Máxima Ataque
    200, // Potência Ré
    190  // Potência Giro
};

/*
 * ===================================================================================
 * CLASSE DE LOGGING ORIENTADA A OBJETOS (LOGGER POO)
 * SISTEMA DE LOGS FORMATADOS VIA SERIAL PARA TINKERCAD / ARDUINO NANO
 * ===================================================================================
 */

#ifndef LOGGER_H
#define LOGGER_H

#include <Arduino.h>

enum LogLevel {
    LOG_DEBUG,
    LOG_INFO,
    LOG_WARN,
    LOG_ERROR
};

class Logger {
private:
    bool ativado;
    LogLevel nivelMinimo;

    void imprimirPrefix(LogLevel nivel) {
        unsigned long ms = millis();
        Serial.print(F("["));
        Serial.print(ms / 1000.0, 2);
        Serial.print(F("s] "));

        switch (nivel) {
            case LOG_DEBUG: Serial.print(F("[DEBUG] ")); break;
            case LOG_INFO:  Serial.print(F("[INFO] "));  break;
            case LOG_WARN:  Serial.print(F("[⚠️ WARN] ")); break;
            case LOG_ERROR: Serial.print(F("[🚨 ERROR] ")); break;
        }
    }

public:
    Logger(bool habilitado = true, LogLevel nivel = LOG_INFO)
        : ativado(habilitado), nivelMinimo(nivel) {}

    void iniciar(long baudrate = 9600) {
        if (ativado) {
            Serial.begin(baudrate);
            delay(100);
            info(F("=== SISTEMA DE LOGS INICIALIZADO NO ARDUINO NANO ==="));
        }
    }

    void setAtivado(bool estado) { ativado = estado; }
    void setNivelMinimo(LogLevel nivel) { nivelMinimo = nivel; }

    void info(const String &msg) {
        if (ativado && nivelMinimo <= LOG_INFO) {
            imprimirPrefix(LOG_INFO);
            Serial.println(msg);
        }
    }

    void debug(const String &msg) {
        if (ativado && nivelMinimo <= LOG_DEBUG) {
            imprimirPrefix(LOG_DEBUG);
            Serial.println(msg);
        }
    }

    void warn(const String &msg) {
        if (ativado && nivelMinimo <= LOG_WARN) {
            imprimirPrefix(LOG_WARN);
            Serial.println(msg);
        }
    }

    void error(const String &msg) {
        if (ativado && nivelMinimo <= LOG_ERROR) {
            imprimirPrefix(LOG_ERROR);
            Serial.println(msg);
        }
    }

    void logSensor(const String &nomeSensor, float valor, const String &unidade) {
        if (ativado && nivelMinimo <= LOG_DEBUG) {
            imprimirPrefix(LOG_DEBUG);
            Serial.print(F("SENSOR ["));
            Serial.print(nomeSensor);
            Serial.print(F("]: "));
            Serial.print(valor);
            Serial.print(F(" "));
            Serial.println(unidade);
        }
    }
};

#endif // LOGGER_H

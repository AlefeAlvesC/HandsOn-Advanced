#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_PN532.h>
#include <HTTPClient.h>

// PN532 via I2C
#define SDA_PIN 21
#define SCL_PIN 22
Adafruit_PN532 nfc(SDA_PIN, SCL_PIN);

// WiFi
const char* ssid     = "CIT_Alunos";
const char* password = "alunos@2024";

HTTPClient http; // Instância do cliente HTTP

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado!");
  Serial.print("IP local: ");
  Serial.println(WiFi.localIP());

  nfc.begin();
  if (!nfc.getFirmwareVersion()) {
    Serial.println("PN532 não encontrado.");
    while (1);
  }

  nfc.SAMConfig();
  Serial.println("Leitor pronto.");
}

void loop() {
  uint8_t uid[7];
  uint8_t uidLength;

  if (nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength)) {
    Serial.print("Cartão detectado. UID: ");
    for (uint8_t i = 0; i < uidLength; i++) {
      Serial.print(uid[i], HEX);
      Serial.print(" ");
    }
    Serial.println();

    // Verifica se é o cartão A3 DC 61 10
    if (uidLength == 4 &&
        uid[0] == 0xA3 &&
        uid[1] == 0xDC &&
        uid[2] == 0x61 &&
        uid[3] == 0x10) {
      Serial.println("Cartão autorizado detectado! Enviando requisição HTTP...");

      // Enviar a requisição HTTP para o servidor Flask
      http.begin("ENDEREÇO_IP_LOCAL:5000/confirmar_entrega");
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST("{}");

      // Verifica a resposta do servidor
      if (httpResponseCode > 0) {
        Serial.printf("Resposta HTTP: %d\n", httpResponseCode);
        String payload = http.getString();
        Serial.println(payload);
      } else {
        Serial.printf("Erro na requisição HTTP: %d\n", httpResponseCode);
      }
      http.end(); // Finaliza a requisição HTTP

    } else {
      Serial.println("Cartão não autorizado.");
    }

    delay(2000); // Aguarda 2 segundos antes de verificar novamente
  }
}
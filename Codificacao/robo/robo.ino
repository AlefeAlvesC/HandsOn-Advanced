/********
 * RoboCore - Kit Robo Explorer - Robo Seguidor de Linha e Anticolisao
********/

#include <RoboCore_Vespa.h>
#include <NewPing.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

//area de conexão
const char* ssid = "CIT_Alunos";
const char* password = "alunos@2024";
const char* serverUrl = "http://172.22.68.230:5000/proxima-entrega"; // IP do servidor Flask + porta

//area motor
VespaMotors motores;

const int SENSOR_LINHA_ESQUERDO = 36;
const int SENSOR_LINHA_DIREITO = 39;

enum ROTAS {
  ROTA_VERDE = 1,
  ROTA_VERMELHO = 2,
  ROTA_PRETO = 3
};

struct Intervalo {
  int MIN;
  int MAX;
};

Intervalo intervalosPorRota[] = {
  {2200, 2400},    // ROTA_A
  {1700, 1900},  // ROTA_B
  {3000, 4100}   // ROTA_C
};

int leitura_esquerdo = 0;
int leitura_direito = 0;

const int LEITURA_LINHA = 3000;
//declaracao da variavel que armazena a velocidade em linha reta do robo
const int VELOCIDADE = 70; 
//declaracao da variavel que armazena o valor que sera somado a velocidade de rotacao dos motores
const int VELOCIDADE_SOMA = 30;
//declaracao da variavel que armazena o valor que sera subtraido da valocidade de rotacao dos motores
const int VELOCIDADE_SUBTRACAO = 50;
//declaracao da variavel que armazena o valor maximo de contagem de parada
const int CONTAGEM_MAXIMA = 10000;
//declaracao da variavel do contador para parar o robo caso ele fuja da pista


int contador_parada = 0;
int rota = 0;
String sala = "";

void setup() {
  Serial.begin(9600);

  WiFi.begin(ssid, password);

  // Conecta ao Wi-Fi
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Conectando ao WiFi...");
  }

  Serial.println("Conectado!");
}

void loop() {

  if (rota == 0) rota = verificarEntrega();
  else if (verificarEntregado()) retornarRobo();
  else if (rota != 0) seguidor_linha();
  
  
}

void seguidor_linha() {
  //realiza a leitura dos sensores
  leitura_esquerdo = analogRead(SENSOR_LINHA_ESQUERDO);
  leitura_direito = analogRead(SENSOR_LINHA_DIREITO);
  Serial.println(leitura_esquerdo);
  Serial.println(leitura_direito);

  //verifica se ambas as leituras dos sensores sao maiores que o valor de leitura de corte
  //ou seja se os dois sensores estao sobre a linha da pista
  if(((leitura_esquerdo > intervalosPorRota[rota - 1].MIN) && (leitura_esquerdo < intervalosPorRota[rota - 1].MAX)) && ((leitura_direito > intervalosPorRota[rota - 1].MIN) && (leitura_direito < intervalosPorRota[rota - 1].MAX))) { //se for verdadeiro
    //movimenta o robo para frente
    motores.forward(VELOCIDADE);
    contador_parada = 0; //zera o contador de parada
  }

  //verifica se ambas as leituras dos sensores sao menores que o valor de leitura de corte
  //ou seja se os dois sensores estao fora da linha da pista
  else if((leitura_esquerdo < intervalosPorRota[rota - 1].MIN) && (leitura_direito < intervalosPorRota[rota - 1].MIN)){//se for verdadeiro
    contador_parada++; //incrementa o contador de parada
  }

  //verifica se apenas a leitura do sensor da direita e menor que o valor de leitura de corte
  //ou seja se apenas o sensor da direta esta sobre a linha da pista
  else if(leitura_direito > intervalosPorRota[rota - 1].MIN) { //se for verdadeiro
    //gira o robo para a esquerda ajustando a velocidade dos motores
    motores.turn(VELOCIDADE+VELOCIDADE_SOMA, VELOCIDADE-VELOCIDADE_SUBTRACAO);
    contador_parada = 0; //zera o contador de parada
  }

  //verifica se apenas a leitura do sensor da esquerda e menor que o valor de leitura de corte
  //ou seja se apenas o sensor da esquerda esta sobre a linha da pista
  else if(leitura_esquerdo > intervalosPorRota[rota - 1].MIN) {
    //gira o robo para a direita ajustando a velocidade dos motores
    motores.turn(VELOCIDADE-VELOCIDADE_SUBTRACAO, VELOCIDADE+VELOCIDADE_SOMA);
    contador_parada = 0; //zera o contador de parada
  }

  //verifica se o contador de parada e maior ou igual que o valor de contagem maxima
  //ou seja se o robo ficou muito tempo fora da pista
  if(contador_parada >= CONTAGEM_MAXIMA){ //se for verdadeiro
    motores.stop(); //para o robo
    contador_parada = CONTAGEM_MAXIMA; //fixa a contagem de parada
  }

  //realiza um tempo de espera na execucao do codigo
  delay(0); //altere esse valor caso queira diminuir a sensibilidade do robo
}

bool verificarEntregado() {
  String url_sala = "http://172.22.68.230:5000/entrega_status?sala=" + sala;
  HTTPClient http;
  http.begin(url_sala);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String resposta = http.getString();
    if (resposta.indexOf("entregue") >= 0) {
      return true;
    }
  }
  return false;
}

void retornarRobo() {
  //entregarRemedio();
  motores.setSpeedLeft(100);

  while(((leitura_esquerdo < intervalosPorRota[rota - 1].MAX) && (leitura_esquerdo > intervalosPorRota[rota - 1].MIN)) || ((leitura_direito < intervalosPorRota[rota - 1].MAX) && (leitura_direito > intervalosPorRota[rota - 1].MIN))) {
    motores.setSpeedLeft(100);
    delay(100);
   }
  motores.stop();
  return;
}

int verificarEntrega() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    int httpCode = http.GET();

    if (httpCode > 0) {
      String payload = http.getString();
      Serial.println("Resposta do servidor:");
      Serial.println(payload);
      // Alocar espaço para o JSON (ajuste se o JSON for muito grande)
      const size_t capacidade = 512;
      StaticJsonDocument<capacidade> doc;

      DeserializationError erro = deserializeJson(doc, payload);

      if (erro) {
        Serial.print("Erro ao fazer parse do JSON: ");
        Serial.println(erro.c_str());
        return 0;
      }

      // Acessar os campos do JSON
      String sala = doc["sala"];
      String somenteNumeros = "";

      for (int i = 0; i < sala.length(); i++) {
        if (isDigit(sala[i])) {
          somenteNumeros += sala[i];
        }
      }

      Serial.println(somenteNumeros);  // Vai imprimir: 203
      sala = somenteNumeros;
      int numeroSala = somenteNumeros.toInt();
      return (numeroSala / 100);
      // Aqui você pode fazer parsing do JSON e usar sala/horário
    } else {
      Serial.println("Erro ao se conectar ao servidor");
    }

    http.end();
  } 
  return NULL;
}
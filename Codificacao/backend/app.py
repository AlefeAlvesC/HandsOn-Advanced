from flask import Flask, request, jsonify
from blockchain import Blockchain
from flask_cors import CORS
import requests
import hashlib
import json

FIREBASE_DB_URL = "URL_DO_SEU_FIREBASE"

app = Flask(__name__)
CORS(app)  # Permite comunicação entre frontend e backend

blockchain = Blockchain()

@app.route("/", methods=["GET"])
def home():
    return "API de Blockchain no ar"

#Registra um novo acesso ao blockchain
@app.route('/registrar', methods=['POST'])
def registrar_medicamento():
    data = request.get_json()
    sala = data.get('sala')
    medicamento = data.get('medicamento')
    nome_medico = data.get('nome_medico')
    nome_paciente = data.get('nome_paciente')
    horario = data.get('horario')

    if not sala or not medicamento or not nome_medico or not nome_paciente or not horario:
        return jsonify({'erro': 'Dados incompletos'}), 400

    bloco = blockchain.adicionar_bloco(sala, medicamento, nome_medico, nome_paciente, horario)

    # Envia para o Firebase
    bloco_dict = bloco.to_dict()
    try:
        response = requests.post(f"{FIREBASE_DB_URL}/blockchain.json", json=bloco_dict)
        response.raise_for_status()
    except Exception as e:
        print("Erro ao salvar bloco no Firebase:", e)


    return jsonify({
        'mensagem': 'Acesso registrado com sucesso na blockchain!',
        'bloco': bloco.to_dict()
    })

#Exibe as informações de todo o blockchain
@app.route('/blockchain', methods=['GET'])
def obter_blockchain():
    
    try:
        response = requests.get(f"{FIREBASE_DB_URL}/blockchain.json")
        response.raise_for_status()
        dados = response.json()

    # Transformar os blocos em uma lista ordenada por índice
        blocos = list(dados.values()) if dados else []
        blocos_ordenados = sorted(blocos, key=lambda b: b.get("index", 0))
        return jsonify(blocos_ordenados)
    
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar blockchain: {str(e)}"}), 500
    
@app.route("/validar_blockchain", methods=["GET"])
def validar_blockchain():
    try:
        #Dados referente ao blockchain
        response = requests.get(f"{FIREBASE_DB_URL}/blockchain.json")
        response.raise_for_status()
        dados_block = response.json()

        if not dados_block:
            return jsonify({"valido": True, "mensagem": "Blockchain vazia."})

        blocos = list(dados_block.values())
        blocos_ordenados = sorted(blocos, key=lambda b: b.get("index", 0))


        #Verifica a integridade dos dados do blockchain no firebase
        for i in range(1, len(blocos_ordenados)):
            anterior = blocos_ordenados[i - 1]
            atual = blocos_ordenados[i]

            
            # Verifica se o hash_anterior bate com o hash do bloco anterior
            if atual.get("hash_anterior") != anterior.get("hash"):
                return jsonify({"valido": False, "mensagem": f"Inconsistência no bloco {atual.get('index')}: hash_anterior incorreto."})

            # Recalcula o hash do bloco atual (exceto o próprio campo 'hash')
            bloco_dict = {"index": atual.get("index"),
                "sala": atual.get("sala"),
                "medicamento": atual.get("medicamento"),
                "nome_medico": atual.get("nome_medico"),
                "nome_paciente": atual.get("nome_paciente"),
                "horario": atual.get("horario"),
                "timestamp": atual.get("timestamp"),
                "hash_anterior": atual.get("hash_anterior")
            }
            bloco_serializado = json.dumps(bloco_dict, sort_keys=True).encode()
            hash_calculado = hashlib.sha256(bloco_serializado).hexdigest()

            if atual.get("hash") != hash_calculado:
                return jsonify({"valido": False, "mensagem": f"Inconsistência no bloco {atual.get('index')}: hash inválido."})

            
        #Dados de entrega
        response = response = requests.get(f"{FIREBASE_DB_URL}/entregas.json")
        response.raise_for_status()
        entregas = response.json()
        
        if not entregas:
            return jsonify({"valido": True, "mensagem": "Sem entregas."})

        # Verificar se os dados das entregas foram alterados
        for bloco in blocos_ordenados:
            paciente = bloco.get("nome_paciente")
            medico = bloco.get("nome_medico")
            sala = bloco.get("sala")
            horario = bloco.get("horario")

            # Verifica se existe entrega correspondente
            entrega_correspondente = None
            for entrega_id, entrega in entregas.items():
                if (
                    entrega.get("nome") == paciente and
                    entrega.get("medico") == medico and
                    entrega.get("sala") == sala and
                    entrega.get("horario") == horario
                ):
                    entrega_correspondente = entrega
                    break

            if not entrega_correspondente:
                return jsonify({
                    "valido": False,
                    "mensagem": f"Entrega referente ao paciente '{paciente}' não encontrada ou alterada."
                })

            # Verifica medicamento
            if entrega_correspondente.get("medicamento") != bloco.get("medicamento"):
                return jsonify({
                    "valido": False,
                    "mensagem": f"Medicamento da entrega do paciente '{paciente}' foi alterado."
                })    

        return jsonify({"valido": True, "mensagem": "Blockchain íntegra e dados de entrega consistentes."})

    except Exception as e:
        return jsonify({"valido": False, "mensagem": str(e)}), 500
    
    
#Faz uma requisição ao Firebase para receber os dados da entrega mais pendente  
@app.route('/proxima-entrega', methods=['GET'])
def proxima_entrega():
    try:
        response = requests.get(f"{FIREBASE_DB_URL}/entregas.json")
        response.raise_for_status()
        entregas = response.json()

        if not entregas:
            return jsonify({"mensagem": "Sem entregas pendentes"}), 204

        for key, entrega in entregas.items():
            if entrega.get("status") == "pendente":
                entrega_completa = entrega.copy()
                entrega_completa["id"] = key
                return jsonify(entrega_completa), 200

        return jsonify({"mensagem": "Sem entregas pendentes"}), 204

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

#Confirmar entrega com RFID.
@app.route('/confirmar_entrega', methods=['POST'])
def confirmar_entrega():
    try:
        ref = requests.get(f"{FIREBASE_DB_URL}/entregas.json")
        entregas = ref.json()

        if not entregas:
            return jsonify({"erro": "Nenhuma entrega encontrada"}), 404

        # Encontrar a entrega pendente com menor horário
        entrega_pendente = min(
            (e for e in entregas.items() if e[1].get("status") == "pendente"),
            key=lambda x: x[1].get("horario", ""),
            default=None
        )

        if not entrega_pendente:
            return jsonify({"erro": "Nenhuma entrega pendente"}), 404

        entrega_id = entrega_pendente[0]
        requests.patch(f"{FIREBASE_DB_URL}/entregas/{entrega_id}.json", json={"status": "entregue"})

        return jsonify({"mensagem": "Entrega confirmada com sucesso."})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

#Requisição feita pelo robo para saber o status de uma entrega
@app.route('/entrega_status', methods=['GET'])
def entrega_status():
    sala = request.args.get('sala')

    ref = requests.get(f"{FIREBASE_DB_URL}/entregas.json")
    entregas = ref.json()

    for entrega_id, dados in entregas.items():
        if dados.get("sala") == sala:
            return jsonify({"status": dados.get("status")})

    return jsonify({"erro": "Entrega não encontrada"}), 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
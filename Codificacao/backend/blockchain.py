import hashlib
import time
import json

# Classe para definir cada bloco da blockchain
class Bloco:
    def __init__(self, index, sala, medicamento, nome_medico, nome_paciente, horario, timestamp, hash_anterior):
        self.index = index
        self.sala = sala
        self.medicamento = medicamento
        self.nome_medico = nome_medico
        self.nome_paciente = nome_paciente
        self.horario = horario
        self.timestamp = timestamp
        self.hash_anterior = hash_anterior
        self.hash = self.gerar_hash()

    def gerar_hash(self):
        #bloco_conteudo = f"{self.index}{self.sala}{self.medicamento}{self.nome_medico}{self.nome_paciente}{self.horario}{self.timestamp}{self.hash_anterior}"
        #return hashlib.sha256(bloco_conteudo.encode()).hexdigest()
        # Dicionário com os dados do bloco, exceto o hash
        
        bloco_dict = {
            "index": self.index,
            "sala": self.sala,
            "medicamento": self.medicamento,
            "nome_medico": self.nome_medico,
            "nome_paciente": self.nome_paciente,
            "horario": self.horario,
            "timestamp": self.timestamp,
            "hash_anterior": self.hash_anterior
        }


        # Serializa em JSON ordenado e gera o hash
        bloco_serializado = json.dumps(bloco_dict, sort_keys=True).encode()
        return hashlib.sha256(bloco_serializado).hexdigest()
    
    def to_dict(self):
        return {
            "index": self.index,
            "sala": self.sala,
            "medicamento": self.medicamento,
            "nome_medico": self.nome_medico,
            "nome_paciente": self.nome_paciente,
            "horario": self.horario,
            "timestamp": self.timestamp,
            "hash_anterior": self.hash_anterior,
            "hash": self.hash
        }

# Classe para a Blockchain
class Blockchain:
    def __init__(self):
        self.chain = []
        self.criar_bloco_inicial()

    def criar_bloco_inicial(self):
        # Bloco inicial da blockchain (genesis block)
        bloco_inicial = Bloco(0, 0, "Início", "Sistema", "Paciente", "Horario", int(time.time()), "0")
        self.chain.append(bloco_inicial)

    def adicionar_bloco(self, sala, medicamento, nome_medico, nome_paciente, horario):
        # Criação de um novo bloco
        index = len(self.chain)
        timestamp = int(time.time())
        hash_anterior = self.chain[-1].hash
        novo_bloco = Bloco(index, sala, medicamento, nome_medico, nome_paciente, horario, timestamp, hash_anterior)
        self.chain.append(novo_bloco)
        return novo_bloco

    def verificar_integridade(self):
        # Verifica a integridade da cadeia de blocos
        for i in range(1, len(self.chain)):
            bloco_atual = self.chain[i]
            bloco_anterior = self.chain[i - 1]

            if bloco_atual.hash != bloco_atual.gerar_hash():
                return False
            if bloco_atual.hash_anterior != bloco_anterior.hash:
                return False
        return True

    def return_chain(self):
        # Retorna todos os blocos da blockchain
        return [bloco.to_dict() for bloco in self.chain]
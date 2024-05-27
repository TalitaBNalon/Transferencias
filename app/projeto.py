from flask import Flask, request, json, Response, jsonify
from pymongo import MongoClient
import os
import win32com.client as win32
import pythoncom
from dotenv import load_dotenv
import datetime 




#carregando as variáveis de ambiente
load_dotenv()

# usando pymongo para interagir com MongoDB e predefinindo o cliente
# conectando com o banco
#client = MongoClient(os.getenv("MONGO_URL"))
client = MongoClient("mongodb://localhost:27017/")
database = ["bank"]
collection = ["user"]
db = client['bank']


#criando um servidor para flask
app = Flask(__name__)

# Método GET
@app.route("/bank", methods=["GET"])
def read():
    try:
        # procurando todos os documentos da collection
        data = list(collection.find({}, {"_id": 0}))
        
        # verificando se a colection está vazia
        if not data:
            return jsonify({"Erro": "Nenhum dado encontrado"}), 404
        
        # retornando os documentos encontrados
        return jsonify(data), 200
    
    except Exception as e:
        # tratando exceções + mensagem de erro
        return jsonify({"Erro do Servidor Interno": str(e)}), 500









#Criando e inserindo um novo cliente no db
#Método POST
@app.route("/bank", methods=["POST"])
def create():
    try:
        # Definindo valores fixos
        id = 4
        cpf = "238.686.785-70"
        email = "olivia.domingues@germinare.org.br"
        balance = 5000
        type_user = "cliente"
        full_name = "Olivia Farias"

        # Verificando se todos os campos obrigatórios estão presentes
        if not all([id, cpf, email]):
            return jsonify({"Erro": "Os campos cpf, email, e id precisam obrigatoriamente serem preenchidos"}), 400

        # Verificando se já existe um usuário com o mesmo cpf, email ou id
        if db.collection.find_one({'$or': [{'cpf': cpf}, {'email': email}, {'id': id}]}):
            return jsonify({"Erro": "O cliente já existe"}), 400

        # Inserindo o novo usuário
        db.collection.insert_one({
            "id": id,
            "cpf": cpf,
            "email": email,
            "balance": balance,
            "type_user": type_user,
            "full_name": full_name
        })
        return jsonify({"Status": "Cliente inserido com sucesso!"}), 201

    except Exception as e:
        return jsonify({"Erro do Servidor Interno": str(e)}), 500










@app.route("/bank/transfer_money", methods=["PUT"])
def transfer_money():
    try:
        data = request.json
        value = data.get('value')
        id_payer = data.get('payer')
        id_payee = data.get('payee')

        # Verifica se os campos obrigatórios estão presentes
        if not all([value, id_payer, id_payee]):
            return jsonify({"Erro": "Valor, pagador e recebedor são obrigatórios!"}), 400
        
        if not validation_antifraud(id_payee, id_payer):
            return jsonify({"Erro": "Aviso fraude detectada"}), 403

        # Verifica se os IDs do pagador e recebedor são diferentes
        if id_payer == id_payee:
            return jsonify({"Erro": "Pagador e recebedor não podem ser a mesma pessoa!"}), 400

        # Busca o pagador e o recebedor no banco de dados
        payer = db.collection.find_one({"id": id_payer})
        payee = db.collection.find_one({"id": id_payee})

        # Verifica se pagador e recebedor foram encontrados
        if not payer:
            return jsonify({"Erro": "Pagador não encontrado"}), 404
        if not payee:
            return jsonify({"Erro": "Recebedor não encontrado"}), 404

        # Verifica se o pagador tem saldo suficiente e se é lojista
        if payer['balance'] < value:
            return jsonify({"Erro": "Saldo insuficiente"}), 400
        if payer['type_user'] == 'lojista':
            return jsonify({'Erro': 'O usuário não pode realizar transferência!'}), 403

        # Calcula os saldos atualizados
        new_payer_balance = payer['balance'] - value
        new_payee_balance = payee['balance'] + value

        # Atualiza os saldos no banco de dados
        db.collection.update_one({"id": id_payer}, {"$set": {"balance": new_payer_balance}})
        db.collection.update_one({"id": id_payee}, {"$set": {"balance": new_payee_balance}})



        # Envia email de confirmação
        email_transfer(value, payer, payee)

        
        return jsonify({"Status": "Transferência realizada com sucesso!"}), 200

    except Exception as e:
        return jsonify({"Erro do Servidor Interno": str(e)}), 500
    


import pythoncom
import win32com.client as win32

def email_transfer(value, payer, payee):
    try:
        pythoncom.CoInitialize()
        outlook = win32.Dispatch('outlook.application')
        email = outlook.CreateItem(0)

        nome_payer = payer.get('full_name')
        nome_payee = payee.get('full_name')
        email_payer = payer.get('email')
        email_payee = payee.get('email')

        email.To = email_payee + "; " + email_payer
        email.Subject = "Transferencia ocorrida PICPAY"
        email.HTMLBody = f"""
        <center><h2>Resumo da transferencia</h2></center>
        <hr></hr>

        <center><h1 style="color: #00A000"><strong>R${value}</strong></h1></center>
        <center><div style="display: inline-block">
            <p>Nome do remetente: <strong>{nome_payer}</strong></p>
            <p>Nome do destinatario: <strong>{nome_payee}</strong></p>
        </div></center>
        <hr></hr>
        <p><strong>Ass:</strong> Picpay de python ❇️</p>
        """

        email.Send()
    except Exception as e:
        print(f"Falha ao enviar email: {str(e)}")

def validation_antifraud(id_payee, id_payer):
    return True


    

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")




       # registrando a transação
        #transaction = {
        #    "value": value,
        #    "payer": id_payer,
        #    "payee": id_payee,
        #    "timestamp": datetime.datetime.utcnow()
        #}
        #db['transactions'].insert_one(transaction) 
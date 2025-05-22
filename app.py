import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__)

# Configuração do número WhatsApp e da chave de API Z-API
Z_API_URL = "https://z-api.io/whatsapp/sendMessage"
Z_API_KEY = "https://api.z-api.io/instances/3E18FB6338B7A08354CDBAA23289AB67/token/74CD58CE2ED12992EED4C996/send-text"

# Configuração da IA (Together AI ou outra API)
TOGETHER_AI_API_URL = "https://api.together.ai"
TOGETHER_AI_API_KEY = "tgp_v1_vtE5Ie1gbFyJttyMrVxRvYyXyTdmTF6TKsdMVEchacg"

# Definir a rota raiz para testar
@app.route('/')
def home():
    return "Servidor Flask está funcionando!"

# Definir o favicon.ico
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.getcwd(), 'favicon.ico')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    # Receber o número do usuário e a mensagem
    user_message = data.get('messages')[0].get('text')
    user_number = data.get('messages')[0].get('from')

    # Processar a mensagem com IA
    response_message = process_message_with_IA(user_message)

    # Enviar a resposta para o WhatsApp
    send_message_to_whatsapp(user_number, response_message)

    return jsonify({"status": "success"})


def process_message_with_IA(user_message):
    # Enviar a mensagem para a API da IA e obter a resposta
    headers = {"Authorization": f"Bearer {TOGETHER_AI_API_KEY}"}
    payload = {"message": user_message}

    response = requests.post(TOGETHER_AI_API_URL, json=payload, headers=headers)
    ai_response = response.json()

    return ai_response.get('response', 'Desculpe, não entendi.')


def send_message_to_whatsapp(user_number, message):
    payload = {
        "to": user_number,
        "message": message
    }

    headers = {"Authorization": f"Bearer {Z_API_KEY}"}

    response = requests.post(Z_API_URL, json=payload, headers=headers)
    return response.json()


if __name__ == "__main__":
    # Mudança importante: Altere o host para '0.0.0.0' e use a variável de ambiente para a porta
    port = int(os.environ.get('PORT', 5000))  # O Render define a porta automaticamente
    app.run(host='0.0.0.0', port=port, debug=True)

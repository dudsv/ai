from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ✅ SUA instância Z-API
ZAPI_INSTANCE = '3E18FB6338B7A08354CDBAA23289AB67'
ZAPI_TOKEN = '74CD58CE2ED12992EED4C996'

# ✅ Sua chave da Together AI
TOGETHER_API_KEY = 'tgp_v1_vtE5Ie1gbFyJttyMrVxRvYyXyTdmTF6TKsdMVEchacg'

# Palavras que disparam redirecionamento
TRIGGER_KEYWORDS = ['atendente', 'erro', 'humano', 'urgente', 'reclamar']

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    msg = data.get("message", "")
    phone = data.get("phone", "")

    if any(p in msg.lower() for p in TRIGGER_KEYWORDS):
        resposta = "🔁 Ok, estou te conectando com um atendente humano. Aguarde um momento..."
    else:
        resposta = consultar_ia(msg)

    enviar_resposta(phone, resposta)
    return jsonify({"status": "mensagem enviada"})

def consultar_ia(mensagem):
    payload = {
        "model": "gpt-4-turbo",
        "messages": [{"role": "user", "content": mensagem}],
        "temperature": 0.7
    }
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    r = requests.post("https://api.together.xyz/v1/chat/completions", json=payload, headers=headers)
    return r.json()['choices'][0]['message']['content']

def enviar_resposta(phone, message):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {"phone": phone, "message": message}
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)

@app.route("/", methods=["GET"])
def home():
    return "✅ Chatbot com Z-API + Together AI está ativo."

if __name__ == "__main__":
    app.run()


from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ZAPI_INSTANCE = '3E18FB6338B7A08354CDBAA23289AB67'
ZAPI_TOKEN = '74CD58CE2ED12992EED4C996'
TOGETHER_API_KEY = 'tgp_v1_wvt7O5cUciNA87wd6qiE684MtoDDUwUw9RPuPDHbs3E'

TRIGGER_KEYWORDS = ['atendente', 'humano', 'reclamar', 'erro', 'urgente', 'problema']

@app.route("/", methods=["GET"])
def home():
    return "✅ Servidor Flask com Z-API + Together AI rodando."

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📥 Dados recebidos do Z-API:", data)

    if not data or "message" not in data or "phone" not in data:
        print("❌ Dados incompletos.")
        return jsonify({"status": "erro", "msg": "dados ausentes"}), 400

    msg = data["message"]
    phone = data["phone"]

    resposta_ia = consultar_ia(msg)

    if any(p in msg.lower() for p in TRIGGER_KEYWORDS):
        resposta_ia += "\n\n🔁 Parece que você precisa de ajuda urgente. Estou encaminhando para um atendente humano, ok?"

    enviar_resposta(phone, resposta_ia)
    return jsonify({"status": "mensagem enviada"})

def consultar_ia(mensagem):
    print("🧠 Enviando para Together AI:", mensagem)
    payload = {
        "model": "gpt-4-turbo",
        "messages": [{"role": "user", "content": mensagem}],
        "temperature": 0.7
    }
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post("https://api.together.xyz/v1/chat/completions", json=payload, headers=headers)
        resposta = r.json()['choices'][0]['message']['content']
        print("✅ Resposta da IA:", resposta)
        return resposta
    except Exception as e:
        print("❌ Erro na Together AI:", e)
        return "Desculpe, algo deu errado. Tente novamente mais tarde."

def enviar_resposta(phone, message):
    print(f"📤 Enviando para {phone}: {message}")
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {
        "phone": phone,
        "message": message
    }
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print("❌ Erro ao enviar via Z-API:", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

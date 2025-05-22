
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ZAPI_INSTANCE = '3E18FB6338B7A08354CDBAA23289AB67'
ZAPI_TOKEN = '74CD58CE2ED12992EED4C996'
TOGETHER_API_KEY = 'tgp_v1_wvt7O5cUciNA87wd6qiE684MtoDDUwUw9RPuPDHbs3E'

TRIGGER_KEYWORDS = ['atendente', 'humano', 'reclamar', 'erro', 'urgente', 'suporte', 'problema']
contexto_por_usuario = {}

@app.route("/", methods=["GET"])
def home():
    return "✅ Chatbot natural com IA e redirecionamento inteligente."

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📥 Dados recebidos do Z-API:", data)

    # Correção segura para capturar a mensagem corretamente
    msg = None
    if "message" in data and isinstance(data["message"], str):
        msg = data["message"]
    elif "text" in data:
        if isinstance(data["text"], dict) and "body" in data["text"]:
            msg = data["text"]["body"]
        elif isinstance(data["text"], str):
            msg = data["text"]

    phone = data.get("phone") or data.get("from")

    if not msg or not phone:
        print("❌ Dados incompletos.")
        return jsonify({"status": "erro", "msg": "dados ausentes"}), 400

    if phone not in contexto_por_usuario:
        contexto_por_usuario[phone] = [{"role": "system", "content": "Você é um atendente virtual simpático, direto, prestativo e natural. Responda como um humano real, de forma empática, simples e clara."}]

    resposta = consultar_ia(msg, phone)

    if any(p in msg.lower() for p in TRIGGER_KEYWORDS):
        resposta += "\n\n🔁 Parece que você precisa de ajuda urgente. Estou te transferindo agora para um atendente humano, tudo bem?"

    enviar_resposta(phone, resposta)
    return jsonify({"status": "mensagem enviada"})

def consultar_ia(mensagem, telefone):
    print("🧠 Consultando IA com contexto:", mensagem)
    contexto_por_usuario[telefone].append({"role": "user", "content": mensagem})

    payload = {
        "model": "gpt-4-turbo",
        "messages": contexto_por_usuario[telefone][-10:],
        "temperature": 0.8
    }
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post("https://api.together.xyz/v1/chat/completions", json=payload, headers=headers)
        resposta = r.json()['choices'][0]['message']['content']
        contexto_por_usuario[telefone].append({"role": "assistant", "content": resposta})
        print("✅ Resposta da IA:", resposta)
        return resposta
    except Exception as e:
        print("❌ Erro na IA:", e)
        return "Desculpe, tive um problema ao responder. Pode tentar de novo?"

def enviar_resposta(phone, message):
    print(f"📤 Enviando para {phone}: {message}")
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {"phone": phone, "message": message}
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print("❌ Erro ao enviar via Z-API:", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ZAPI_INSTANCE   = '3E18FB6338B7A08354CDBAA23289AB67'
ZAPI_TOKEN      = '74CD58CE2ED12992EED4C996'
TOGETHER_API_KEY = 'tgp_v1_wvt7O5cUciNA87wd6qiE684MtoDDUwUw9RPuPDHbs3E'

TRIGGER_KEYWORDS = ['atendente', 'humano', 'reclamar', 'erro', 'urgente', 'suporte', 'problema']
contexto_por_usuario = {}

@app.route("/", methods=["GET"])
def home():
    return "✅ Chatbot natural e resiliente com Z-API + Together AI"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    print("📥 RAW JSON recebido do Z-API:", data)

    # Extração resiliente da mensagem
    msg = None
    if not isinstance(data, dict):
        msg = None
    else:
        if 'message' in data and isinstance(data['message'], str):
            msg = data['message']
        elif 'text' in data:
            if isinstance(data['text'], dict) and data['text'].get('body'):
                msg = data['text']['body']
            elif isinstance(data['text'], str):
                msg = data['text']
        elif 'body' in data:
            msg = data['body']
        # fallback: converte JSON inteiro em string
        else:
            msg = str(data)

    # Extração do telefone
    phone = None
    if isinstance(data, dict):
        phone = data.get('phone') or data.get('from') or data.get('sender')

    # Se não conseguir extrair, apenas loga e responde OK
    if not msg or not phone:
        print("⚠️ Não foi possível extrair 'msg' ou 'phone'. Ignorando.")
        return jsonify({"status": "ignored"}), 200

    # Inicializa contexto
    if phone not in contexto_por_usuario:
        contexto_por_usuario[phone] = [
            {
                "role": "system",
                "content": (
                    "Você é um atendente virtual simpático, direto, prestativo e natural. "
                    "Responda como um humano real, de forma empática, simples e clara."
                )
            }
        ]

    # Consulta IA
    resposta = consultar_ia(msg, phone)

    # Se chave crítica, adiciona nota de transferência
    if any(kw in msg.lower() for kw in TRIGGER_KEYWORDS):
        resposta += "\n\n🔁 Parece que você precisa de ajuda urgente. Estou te transferindo agora para um atendente humano, tudo bem?"

    enviar_resposta(phone, resposta)
    return jsonify({"status": "mensagem enviada"}), 200

def consultar_ia(mensagem, telefone):
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
        r.raise_for_status()
        texto = r.json()['choices'][0]['message']['content']
        contexto_por_usuario[telefone].append({"role": "assistant", "content": texto})
        print("✅ Resposta da IA:", texto)
        return texto
    except Exception as e:
        print("❌ Erro na IA:", e)
        return "Desculpe, tive um problema ao responder. Pode tentar de novo?"

def enviar_resposta(phone, message):
    print(f"📤 Enviando para {phone}: {message}")
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {"phone": phone, "message": message}
    try:
        requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    except Exception as e:
        print("❌ Erro ao enviar via Z-API:", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

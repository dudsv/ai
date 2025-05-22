from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ZAPI_INSTANCE    = '3E18FB6338B7A08354CDBAA23289AB67'
ZAPI_TOKEN       = '74CD58CE2ED12992EED4C996'
TOGETHER_API_KEY = 'tgp_v1_wvt7O5cUciNA87wd6qiE684MtoDDUwUw9RPuPDHbs3E'

TRIGGER_KEYWORDS = ['atendente','humano','reclamar','erro','urgente','suporte','problema']
contexto_por_usuario = {}

@app.route("/", methods=["GET"])
def home():
    return "✅ Chatbot natural e resiliente com Z-API + Together AI"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    print("📥 RAW JSON recebido do Z-API:", data)

    # Extrai msg de vários formatos
    msg = None
    if isinstance(data, dict):
        if 'message' in data and isinstance(data['message'], str):
            msg = data['message']
        elif 'text' in data:
            if isinstance(data['text'], dict) and 'body' in data['text']:
                msg = data['text']['body']
            elif isinstance(data['text'], str):
                msg = data['text']
        elif 'body' in data:
            msg = data['body']
    if msg is None:
        msg = str(data)

    # Extrai phone de vários campos
    phone = None
    if isinstance(data, dict):
        phone = data.get('phone') or data.get('from') or data.get('sender')

    if not msg or not phone:
        print("⚠️ Dados insuficientes (msg ou phone). Ignorando.")
        return jsonify({"status":"ignored"}),200

    # Contexto inicial
    if phone not in contexto_por_usuario:
        contexto_por_usuario[phone] = [{
            "role":"system",
            "content":(
              "Você é um atendente virtual simpático, direto, prestativo e natural. "
              "Responda como um humano real, de forma empática, simples e clara."
            )
        }]

    # Consulta IA
    contexto_por_usuario[phone].append({"role":"user","content":msg})
    try:
        r = requests.post(
            "https://api.together.xyz/v1/chat/completions",
            json={"model":"gpt-4-turbo","messages":contexto_por_usuario[phone][-10:],"temperature":0.8},
            headers={"Authorization":f"Bearer {TOGETHER_API_KEY}","Content-Type":"application/json"}
        )
        r.raise_for_status()
        resposta = r.json()['choices'][0]['message']['content']
        contexto_por_usuario[phone].append({"role":"assistant","content":resposta})
        print("✅ Resposta da IA:",resposta)
    except Exception as e:
        print("❌ Erro na IA:",e)
        resposta = "Desculpe, tive um problema. Por favor, tente novamente."

    # Nota de transferência se necessário
    if any(kw in msg.lower() for kw in TRIGGER_KEYWORDS):
        resposta += "\n\n🔁 Parece que você precisa de ajuda urgente. Estou te transferindo agora para um atendente humano, tudo bem?"

    # Envia e loga resposta da Z-API
    try:
        resp = requests.post(
            f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text",
            json={"phone":phone,"message":resposta},
            headers={"Content-Type":"application/json"}
        )
        print(f"📤 Z-API resposta HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        print("❌ Erro ao enviar via Z-API:",e)

    return jsonify({"status":"mensagem enviada"}),200

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)

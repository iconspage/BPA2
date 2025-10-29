from flask import Flask, request, jsonify
import requests
import os
from bs4 import BeautifulSoup

app = Flask(__name__)

# 🔹 WhatsApp Cloud API Config
ACCESS_TOKEN = "EAASZCI1ZAownwBP5Ya8mnNJNVbc3Oo2R3MrJbCLK7Fs2yLBqbDEzOaxZBouYGsgCVqQGWCsFqe9rS7M7spv09mCZBtJILoBdO2kPtjWT7pPgcVRtlRPjUivlcGPJZAh3CPwBESocCZBfhZB4XGYLgxwWxZCAoQ13QUQMQdjBoOMYSZAD8ljY9l7nfxN2VxGAMdoCiaAZDZD"
VERIFY_TOKEN = "mywhatsbot123"
PHONE_NUMBER_ID = "884166421438641"

# 🔹 OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-REPLACE_WITH_YOURS")

# 🔹 Memory to remember chat history
user_memory = {}

# 🔹 Product catalog (name → image URL)
PRODUCTS = {
    "engine oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Energy-Oil.jpg",
    "hydraulic oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1017-scaled.jpg",
    "gear oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0993-scaled.jpg",
    "diesel additive": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0968-scaled.jpg",
    "transmission fluid": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1008-2.jpg",
    "grease": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg"
}


# ✅ Verify webhook (Meta setup)
@app.route("/webhook", methods=["GET"])
def verify():
    verify_token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if verify_token == VERIFY_TOKEN:
        return challenge
    return "Verification failed", 403


# ✅ Handle incoming WhatsApp messages
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 Incoming data:", data)

    try:
        messages = data["entry"][0]["changes"][0]["value"].get("messages")
        if not messages:
            return jsonify(success=True)

        message = messages[0]
        from_number = message["from"]
        msg_type = message.get("type")

        if msg_type == "text":
            user_text = message["text"]["body"].lower().strip()
            print(f"💬 Message from {from_number}: {user_text}")

            # Initialize memory for new users
            if from_number not in user_memory:
                user_memory[from_number] = []

            user_memory[from_number].append({"user": user_text})

            # ✅ Handle product list request
            if "product list" in user_text or "show products" in user_text:
                product_names = "\n".join([f"• {p.title()}" for p in PRODUCTS.keys()])
                reply = (
                    "🛢 *Bucch Energy Product List:*\n"
                    f"{product_names}\n\n"
                    "Type any product name to see its image."
                )
                send_message(from_number, reply)
                return jsonify(success=True)

            # ✅ Handle individual product requests
            for product, link in PRODUCTS.items():
                if product in user_text:
                    send_image(from_number, link, f"🛢 Here’s our {product.title()} product image.")
                    return jsonify(success=True)

            # ✅ Otherwise — normal AI chat
            ai_reply = chat_with_ai(from_number, user_text)
            send_message(from_number, ai_reply)

        else:
            send_message(from_number, "⚠ I can only process text messages for now 🤖")

    except Exception as e:
        print("❌ Error handling webhook:", e)

    return jsonify(success=True)


# ✅ Send text message
def send_message(to, message):
    url = f"https://graph.facebook.com/v24.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📤 WhatsApp API response:", response.status_code, response.text)


# ✅ Send image message
def send_image(to, image_url, caption=""):
    url = f"https://graph.facebook.com/v24.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": image_url, "caption": caption}
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📸 Sent image response:", response.status_code, response.text)


# ✅ ChatGPT integration (with memory + live website data)
def chat_with_ai(user_id, prompt):
    try:
        history = user_memory.get(user_id, [])
        history_text = "\n".join(
            [f"User: {h['user']}\nBot: {h.get('bot', '')}" for h in history[-5:]]
        )

        # Try fetching website data
        try:
            site_url = "https://bucchenergy.com"
            html = requests.get(site_url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            website_text = ' '.join(p.get_text() for p in soup.find_all("p"))[:3000]
        except Exception as e:
            print("⚠️ Website fetch failed:", e)
            website_text = "(Could not fetch latest site data.)"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are PBA.Bucch — a professional assistant for Bucch Energy. "
                        "Provide accurate and friendly answers based on website info and memory."
                    )
                },
                {
                    "role": "user",
                    "content": f"Past chat:\n{history_text}\n\nUser now says: {prompt}\n\nWebsite info:\n{website_text}"
                }
            ]
        }

        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers, json=body)
        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()

        # Save bot reply to memory
        user_memory[user_id].append({"bot": reply})

        return reply + "\n\n— PBA.Bucch ⚡"

    except Exception as e:
        print("⚙️ AI error:", e)
        return "⚡ Sorry, I’m having trouble right now. Please try again!"


# ✅ Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

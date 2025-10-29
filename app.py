from flask import Flask, request, jsonify
import requests
import os
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

# 🔹 WhatsApp Cloud API Config
ACCESS_TOKEN = "EAASZCI1ZAownwBP5Ya8mnNJNVbc3Oo2R3MrJbCLK7Fs2yLBqbDEzOaxZBouYGsgCVqQGWCsFqe9rS7M7spv09mCZBtJILoBdO2kPtjWT7pPgcVRtlRPjUivlcGPJZAh3CPwBESocCZBfhZB4XGYLgxwWxZCAoQ13QUQMQdjBoOMYSZAD8ljY9l7nfxN2VxGAMdoCiaAZDZD"
VERIFY_TOKEN = "mywhatsbot123"
PHONE_NUMBER_ID = "884166421438641"

# 🔹 OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-REPLACE_WITH_YOURS")

# 🔹 Simple in-memory user context
user_memory = {}

# 🔹 Product image mapping
product_links = {
    "lubricant": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1017-scaled.jpg",
    "engine oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Energy-Oil.jpg",
    "diesel": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0968-scaled.jpg",
    "fuel": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg"
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

        if message.get("type") == "text":
            user_text = message["text"]["body"].strip().lower()
            print(f"💬 Message from {from_number}: {user_text}")

            # Check for product image request
            for keyword, link in product_links.items():
                if keyword in user_text or f"send {keyword}" in user_text or f"show {keyword}" in user_text or f"picture of {keyword}" in user_text:
                    caption = f"Here’s what our {keyword} product looks like ⚡"
                    send_image(from_number, link, caption)
                    send_message(from_number, f"Our {keyword} products are top quality and available across all Bucch Energy outlets.")
                    return jsonify(success=True)

            # Otherwise handle as normal chat
            ai_reply = chat_with_ai(user_text, from_number)
            send_message(from_number, ai_reply)

        else:
            send_message(from_number, "⚠ I can only read text messages for now 🤖")

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

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("📤 WhatsApp API response:", response.status_code, response.text)
    except Exception as e:
        print("❌ Failed to send message:", e)


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

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("📸 Image sent:", response.status_code, response.text)
    except Exception as e:
        print("❌ Failed to send image:", e)


# ✅ ChatGPT integration (more natural & stable)
def chat_with_ai(prompt, user_id):
    try:
        if user_id not in user_memory:
            user_memory[user_id] = []

        # Add user message
        user_memory[user_id].append({"user": prompt})

        # Use only recent conversation snippets (no “Bot:” prefix)
        history = user_memory[user_id][-5:]
        history_text = "\n".join([f"User: {h.get('user', '')}" for h in history])

        # Try to fetch live site info
        try:
            site_url = "https://bucchenergy.com"
            html = requests.get(site_url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            website_text = ' '.join(p.get_text() for p in soup.find_all("p"))[:3000]
        except Exception as e:
            print("⚠️ Website fetch failed:", e)
            website_text = "Bucch Energy provides high-quality fuels, lubricants, and petroleum services across West Africa."

        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": (
                    "You are PBA.Bucch — a friendly, human-like assistant for Bucch Energy. "
                    "Speak naturally like a person, not a robot. "
                    "You can use emojis occasionally and sound casual yet professional. "
                    f"Here’s info from the company website: {website_text}"
                )},
                {"role": "user", "content": f"{history_text}\n\nUser: {prompt}"}
            ]
        }

        # Retry mechanism
        for i in range(2):
            try:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers, json=body, timeout=20
                )
                data = response.json()
                if "choices" in data:
                    reply = data["choices"][0]["message"]["content"].strip()
                    user_memory[user_id].append({"bot": reply})
                    return reply
                else:
                    print("⚠️ AI incomplete response:", data)
            except Exception as e:
                print(f"⚠️ AI call failed (try {i+1}):", e)
                time.sleep(2)

        return "⚡ Sorry, I’m having trouble right now. Please try again!"

    except Exception as e:
        print("⚙️ AI error:", e)
        return "⚡ Sorry, I’m having trouble right now. Please try again!"


# ✅ Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

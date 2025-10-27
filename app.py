from flask import Flask, request, jsonify
import requests
import os
from bs4 import BeautifulSoup

app = Flask(__name__)

# 🔹 WhatsApp Cloud API Config
ACCESS_TOKEN = "EAASZCI1ZAownwBP0MuUtXDEAXwEbFK9bZChic3sruOcp7nbmD3pOlLqx52xE7aSkx7Va4gxLUYjkR1lPwXjT28p0tPxK9AqjO6GfrcfcoaD6ciheyRG4z4ZCUADtRz8JKmwOco5BCKjWdnGtrBTV6r8I8WccGpsznTF1Nn6jlycrTTlTIm7t5HyVRps70rd72sl7jFZBvF9sDHZC76ZCUItdgVxrSdPQkNzhSFdeK9HlsJPSUGGdN7UeJMBbzy4vIe5GToE8AfZAbu66bvPDvs7eRVSVkQZDZD"
VERIFY_TOKEN = "mywhatsbot123"
PHONE_NUMBER_ID = "884166421438641"

# 🔹 OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-REPLACE_WITH_YOURS")

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

        # Handle only text messages
        if message.get("type") == "text":
            user_text = message["text"]["body"]
            print(f"💬 Message from {from_number}: {user_text}")

            # Generate AI response
            ai_reply = chat_with_ai(user_text)

            # Send reply back to user
            send_message(from_number, ai_reply)

        else:
            send_message(from_number, "⚠ I can only read text messages for now 🤖")

    except Exception as e:
        print("❌ Error handling webhook:", e)

    return jsonify(success=True)


# ✅ Send message to WhatsApp
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


# ✅ ChatGPT integration (with live website fetching)
def chat_with_ai(prompt):
    try:
        # Try fetching live info from Bucch Energy’s website
        try:
            site_url = "https://bucchenergy.com"  # ← change to your actual website
            html = requests.get(site_url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")

            # Extract readable text from the website
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
                        "You are PBA.Bucch — a friendly and professional assistant for Bucch Energy. "
                        "Provide accurate and updated info, including from real-world sources when available. "
                        "Use the following website data as your knowledge reference:\n\n"
                        f"{website_text}\n\n"
                        "If the site text doesn’t contain the needed info, respond politely with what you know and suggest visiting the website."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers, json=body)
        data = response.json()

        reply = data["choices"][0]["message"]["content"]
        return reply.strip() + "\n\n— PBA.Bucch ⚡"

    except Exception as e:
        print("⚙️ AI error:", e)
        return "⚡ Sorry, I’m having trouble getting the latest info — please try again!"


# ✅ Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

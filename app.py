import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Environment variables
ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mywhatsbot123")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Verify webhook
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

# Handle incoming messages
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Incoming data:", data)

    # Check if message exists
    messages_data = data["entry"][0]["changes"][0]["value"].get("messages")
    if messages_data:
        message = messages_data[0]

        # Only process text messages
        if message.get("type") == "text":
            from_number = message["from"]
            text = message["text"]["body"]

            # Get AI response
            ai_reply = chat_with_ai(text)

            # Send reply back to WhatsApp
            send_message(from_number, ai_reply)

    return jsonify(success=True)

# ChatGPT integration
def chat_with_ai(prompt):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
    reply = response.json()["choices"][0]["message"]["content"]
    return reply

# Send WhatsApp message
def send_message(to, message):
    url = f"https://graph.facebook.com/v24.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    r = requests.post(url, headers=headers, json=data)
    print("WhatsApp API response:", r.status_code, r.text)

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

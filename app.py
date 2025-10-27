from flask import Flask, request, jsonify
import requests

app = Flask(__name__)  # ✅ fixed: double underscores

# 🔹 Replace these with your actual details
ACCESS_TOKEN = "EAASZCI1ZAownwBP0MuUtXDEAXwEbFK9bZChic3sruOcp7nbmD3pOlLqx52xE7aSkx7Va4gxLUYjkR1lPwXjT28p0tPxK9AqjO6GfrcfcoaD6ciheyRG4z4ZCUADtRz8JKmwOco5BCKjWdnGtrBTV6r8I8WccGpsznTF1Nn6jlycrTTlTIm7t5HyVRps70rd72sl7jFZBvF9sDHZC76ZCUItdgVxrSdPQkNzhSFdeK9HlsJPSUGGdN7UeJMBbzy4vIe5GToE8AfZAbu66bvPDvs7eRVSVkQZDZD"
VERIFY_TOKEN = "mywhatsbot123"
PHONE_NUMBER_ID = "884166421438641"

# ✅ Verify webhook (Meta uses this once during setup)
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
    print("Incoming data:", data)

    try:
        messages = data["entry"][0]["changes"][0]["value"].get("messages")
        if messages:
            message = messages[0]
            from_number = message["from"]

            # Handle text messages only
            if message.get("type") == "text":
                text = message["text"]["body"]
                print(f"Message from {from_number}: {text}")

                # Just reply something simple (can also echo)
                reply_text = f"You said: {text}"
                send_message(from_number, reply_text)
            else:
                send_message(from_number, "I can only read text messages for now 🤖")

    except Exception as e:
        print("Error handling webhook:", e)

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

    response = requests.post(url, headers=headers, json=payload)
    print("WhatsApp API response:", response.status_code, response.text)


# ✅ Run Flask app
if __name__ == "__main__":  # ✅ fixed: double underscores
    app.run(host="0.0.0.0", port=5000)

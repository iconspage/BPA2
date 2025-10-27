from flask import Flask, request, jsonify
import requests

app = Flask(_name_)

# 🔹 Replace these with your actual details
ACCESS_TOKEN = "EAASZCI1ZAownwBP2Pv81sVieaiJvAIf0RN92JL8QeB43ZBtFDNhf4s5kZCvoRYxqOks7AWKFYTHA41jgPeOCLMkG8pkUeWHXkCNEZB3Seyx3YOt9vg3IzeGd6R35Bn933eTamVaVllGYr8ZCKrqbEnNWX9LJ3m6i22pJdq6ODVSm5khvZCivbEZBZB4UWt6P9Jo6HZAIXgLNCSHTHENjZBO1ZAROrZBAjCZCBuQj1BMXFYlfKZB1VOCM4BW8e7aZCeQ0qHjOMqJUmXsjPpLxa4bIZB5iZAXKutZBecL"  # your WhatsApp Cloud API token
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
if _name_ == "_main_":
    app.run(host="0.0.0.0", port=5000)

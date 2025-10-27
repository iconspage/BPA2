from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# 🔹 Replace these with your actual details
ACCESS_TOKEN = "EAASZCI1ZAownwBP2Pv81sVieaiJvAIf0RN92JL8QeB43ZBtFDNhf4s5kZCvoRYxqOks7AWKFYTHA41jgPeOCLMkG8pkUeWHXkCNEZB3Seyx3YOt9vg3IzeGd6R35Bn933eTamVaVllGYr8ZCKrqbEnNWX9LJ3m6i22pJdq6ODVSm5khvZCivbEZBZB4UWt6P9Jo6HZAIXgLNCSHTHENjZBO1ZAROrZBAjCZCBuQj1BMXFYlfKZB1VOCM4BW8e7aZCeQ0qHjOMqJUmXsjPpLxa4bIZB5iZAXKutZBecL"
VERIFY_TOKEN = "mywhatsbot123"
PHONE_NUMBER_ID = "884166421438641"

# 🧠 Your OpenAI API key
OPENAI_API_KEY = "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"

# ✅ Verify webhook
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

            if message.get("type") == "text":
                text = message["text"]["body"]
                print(f"Message from {from_number}: {text}")

                # 💬 Get AI-generated reply
                ai_reply = chat_with_ai(text)
                send_message(from_number, ai_reply)
            else:
                send_message(from_number, "I can only read text messages for now 🤖")

    except Exception as e:
        print("Error handling webhook:", e)

    return jsonify(success=True)


# 🧠 ChatGPT (OpenAI) integration
def chat_with_ai(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful WhatsApp assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response_json = response.json()
        ai_message = response_json["choices"][0]["message"]["content"]
        return ai_message
    except Exception as e:
        print("OpenAI API error:", e)
        return "Sorry, I’m having trouble thinking right now 🤖"


# ✅ Send message back to WhatsApp
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
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

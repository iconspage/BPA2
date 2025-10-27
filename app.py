from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# 🔹 WhatsApp Config (your real details)
ACCESS_TOKEN = "EAASZCI1ZAownwBP2Pv81sVieaiJvAIf0RN92JL8QeB43ZBtFDNhf4s5kZCvoRYxqOks7AWKFYTHA41jgPeOCLMkG8pkUeWHXkCNEZB3Seyx3YOt9vg3IzeGd6R35Bn933eTamVaVllGYr8ZCKrqbEnNWX9LJ3m6i22pJdq6ODVSm5khvZCivbEZBZB4UWt6P9Jo6HZAIXgLNCSHTHENjZBO1ZAROrZBAjCZCBuQj1BMXFYlfKZB1VOCM4BW8e7aZCeQ0qHjOMqJUmXsjPpLxa4bIZB5iZAXKutZBecL"
VERIFY_TOKEN = "mywhatsbot123"
PHONE_NUMBER_ID = "884166421438641"

# 🔹 OpenAI key stored securely (in Render or local environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Webhook Verification (Meta checks this once)
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403


# ✅ Handle Incoming WhatsApp Messages
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Incoming data:", data)

    try:
        messages = data["entry"][0]["changes"][0]["value"].get("messages")
        if messages:
            message = messages[0]
            from_number = message["from"]

            # Handle text messages
            if message.get("type") == "text":
                text = message["text"]["body"].strip().lower()
                print(f"Message from {from_number}: {text}")

                # 🔹 Greeting detection
                greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
                if any(greet in text for greet in greetings):
                    reply_text = (
                        "Hello there! 👋 I'm *PBA.Bucch*, your virtual assistant from *Bucch Energy Limited*. ⚡\n\n"
                        "I’m here to assist you with information about our petroleum products, lubricants, "
                        "and clean energy solutions — including Base Oil, PMS, DPK, AGO, and LPG.\n\n"
                        "How may I assist you today?"
                    )
                    send_message(from_number, reply_text)
                else:
                    # Normal AI reply
                    ai_reply = chat_with_ai(text)
                    send_message(from_number, ai_reply)
            else:
                send_message(from_number, "⚠️ I can only process text messages for now.")
    except Exception as e:
        print("Error:", e)

    return jsonify(success=True)


# ✅ Send Message Function
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


# ✅ ChatGPT AI Integration (Now Bucch Energy Assistant Personality)
def chat_with_ai(prompt):
    try:
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
                        "You are PBA.Bucch — a friendly, professional customer-service assistant for "
                        "Bucch Energy Limited. Bucch Energy is a Nigerian oil & gas company specialising in "
                        "high-quality base oils and premium petroleum products (PMS, DPK, AGO, LPG) and manufacturing lubricants. "
                        "Your mission: help customers with product information, availability, orders, pricing, and delivery timelines.\n\n"
                        "Use the tone and values of the real company: Reliability, Innovation, Integrity, Environmental Responsibility, "
                        "Customer Focus, and Safety. Speak like an expert but approachable company rep — never like a bot.\n\n"
                        "Always reply naturally and politely. Never mention OpenAI, ChatGPT, or AI — you are Bucch Energy’s official virtual assistant.\n\n"
                        "If unsure about a question, say you’ll check and get back to the customer rather than inventing info.\n\n"
                        "End every response with this signature: “— PBA.Bucch ⚡”"
                    )
                },
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return reply

    except Exception as e:
        print("AI error:", e)
        return "⚡ Sorry, I’m having a little trouble replying right now — please try again!"


# ✅ Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

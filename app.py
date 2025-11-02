from flask import Flask, request, jsonify
import requests
import os
import time
import smtplib
from email.message import EmailMessage
from bs4 import BeautifulSoup

app = Flask(__name__)

# 🔹 WhatsApp Cloud API Config
ACCESS_TOKEN = "EAASZCI1ZAownwBP5Ya8mnNJNVbc3Oo2R3MrJbCLK7Fs2yLBqbDEzOaxZBouYGsgCVqQGWCsFqe9rS7M7spv09mCZBtJILoBdO2kPtjWT7pPgcVRtlRPjUivlcGPJZAh3CPwBESocCZBfhZB4XGYLgxwWxZCAoQ13QUQMQdjBoOMYSZAD8ljY9l7nfxN2VxGAMdoCiaAZDZD"
VERIFY_TOKEN = "mywhatsbot123"
PHONE_NUMBER_ID = "884166421438641"

# 🔹 Email config
EMAIL_FROM = "personalbusinessassisstant@gmail.com"
EMAIL_TO = "iconspage1@gmail.com"
EMAIL_PASSWORD = "lkzrsmwmpivkxdzu"

# 🔹 OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-REPLACE_WITH_YOURS")

# 🔹 Memory
user_memory = {}
user_state = {}

# ✅ ✅ ✅ Expanded Bucch Product Images (ONLY EDITED PART)
product_links = {
    # ✅ Fuel products
    "fuel": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0968-scaled.jpg",
    "pms": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0968-scaled.jpg",
    "petrol": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0968-scaled.jpg",
    "diesel": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg",
    "ago": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg",
    "kerosene": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg",

    # ✅ Engine Oils
    "engine oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0993-scaled.jpg",
    "synthetic engine oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0993-scaled.jpg",
    "premium engine oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Energy-Oil.jpg",

    # ✅ Gear / Transmission Oils
    "gear oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1008-2.jpg",
    "transmission oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0979-scaled.jpg",
    "transmission fluid": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0979-scaled.jpg",

    # ✅ Hydraulic Oils
    "hydraulic oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0970-scaled.jpg",
    "hydraulic fluid": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0970-scaled.jpg",

    # ✅ Drums
    "drum": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0997-scaled.jpg",
    "oil drum": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0997-scaled.jpg",
    "large drum": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0997-scaled.jpg",

    # ✅ Old ones you had
    "lubricant 1": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1017-scaled.jpg",
    "lubricant 2": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1008-2.jpg",
    "lubricant 3": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0993-scaled.jpg",
}

# -------------------------------------------------------------
# Email sender
# -------------------------------------------------------------
def send_order_email(order):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"New WhatsApp Order — Bucch Energy: {order.get('product','(no product)')}"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        msg.set_content(
            f"Product: {order.get('product')}\n"
            f"Quantity: {order.get('quantity')}\n"
            f"Customer name: {order.get('name')}\n"
            f"Phone: {order.get('phone')}\n"
            f"Address: {order.get('address')}\n"
            f"Notes: {order.get('notes')}\n"
            f"WhatsApp user ID: {order.get('user_id')}"
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(EMAIL_FROM, EMAIL_PASSWORD)
            s.send_message(msg)
        return True

    except Exception as e:
        print("Email error:", e)
        return False


# -------------------------------------------------------------
# Webhook verification
# -------------------------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403


# -------------------------------------------------------------
# Webhook receiver
# -------------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Incoming:", data)

    try:
        messages = data["entry"][0]["changes"][0]["value"].get("messages")
        if not messages:
            return jsonify(success=True)

        message = messages[0]
        from_number = message["from"]

        user_memory.setdefault(from_number, [])
        user_state.setdefault(from_number, {"stage": None, "order": {}})

        if message["type"] == "text":
            user_text = message["text"]["body"].lower().strip()
            print("Msg:", user_text)

            # ✅ Image matching FIRST
            for keyword, link in product_links.items():
                if keyword in user_text:
                    send_image(from_number, link, f"{keyword.title()} — Bucch Energy ⚡")
                    return jsonify(success=True)

            # ✅ Order flow
            if user_state[from_number]["stage"]:
                handle_order_message(from_number, user_text)
                return jsonify(success=True)

            # ✅ Start new order
            if user_text in ["order", "place order", "i want to order"]:
                user_state[from_number] = {"stage": "ask_product", "order": {"user_id": from_number}}
                send_message(from_number, "Sure — what product would you like to order?")
                return jsonify(success=True)

            # ✅ AI chat
            ai_reply = chat_with_ai(user_text, from_number)
            send_message(from_number, ai_reply)

        else:
            send_message(from_number, "I currently accept text only ✅")

    except Exception as e:
        print("Webhook error:", e)

    return jsonify(success=True)


# -------------------------------------------------------------
# State machine for order
# -------------------------------------------------------------
def handle_order_message(user_id, text):
    state = user_state[user_id]
    order = state["order"]

    if text == "cancel":
        user_state[user_id] = {"stage": None, "order": {}}
        send_message(user_id, "✅ Order cancelled.")
        return

    stage = state["stage"]

    if stage == "ask_product":
        order["product"] = text
        state["stage"] = "ask_quantity"
        send_message(user_id, "How many units?")
        return

    if stage == "ask_quantity":
        order["quantity"] = text
        state["stage"] = "ask_name"
        send_message(user_id, "Your full name?")
        return

    if stage == "ask_name":
        order["name"] = text
        state["stage"] = "ask_phone"
        send_message(user_id, "Phone number?")
        return

    if stage == "ask_phone":
        order["phone"] = text
        state["stage"] = "ask_address"
        send_message(user_id, "Delivery address?")
        return

    if stage == "ask_address":
        order["address"] = text
        state["stage"] = "ask_notes"
        send_message(user_id, "Any notes? (type 'no' if none)")
        return

    if stage == "ask_notes":
        order["notes"] = "" if text == "no" else text
        state["stage"] = "confirm"
        send_message(
            user_id,
            f"✅ Order summary:\n"
            f"Product: {order['product']}\n"
            f"Quantity: {order['quantity']}\n"
            f"Name: {order['name']}\n"
            f"Phone: {order['phone']}\n"
            f"Address: {order['address']}\n"
            f"Notes: {order['notes']}\n\n"
            f"Type 'confirm' to place order."
        )
        return

    if stage == "confirm":
        if text == "confirm":
            send_order_email(order)
            send_message(user_id, "✅ Order placed! Our sales team will contact you.")
        user_state[user_id] = {"stage": None, "order": {}}


# -------------------------------------------------------------
# WhatsApp text sender
# -------------------------------------------------------------
def send_message(to, message):
    url = f"https://graph.facebook.com/v24.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(url, json=payload, headers=headers)


# -------------------------------------------------------------
# WhatsApp image sender
# -------------------------------------------------------------
def send_image(to, image_url, caption=""):
    url = f"https://graph.facebook.com/v24.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": image_url, "caption": caption}
    }
    requests.post(url, json=payload, headers=headers)


# -------------------------------------------------------------
# AI Chat
# -------------------------------------------------------------
def chat_with_ai(prompt, user_id):
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are PBA.Bucch — Bucch Energy assistant."},
                    {"role": "user", "content": prompt}
                ]
            },
            headers=headers
        )

        return r.json()["choices"][0]["message"]["content"]

    except:
        return "⚠️ Having trouble responding."


# -------------------------------------------------------------
# Run server
# -------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

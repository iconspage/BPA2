from flask import Flask, request, jsonify
import requests
import os
import time
import smtplib
from email.message import EmailMessage
from bs4 import BeautifulSoup

app = Flask(__name__)

# -------------------------
# ✅ WhatsApp Cloud API Config
# -------------------------
ACCESS_TOKEN = "EAASZCI1ZAownwBP5Ya8mnNJNVbc3Oo2R3MrJbCLK7Fs2yLBqbDEzOaxZBouYGsgCVqQGWCsFqe9rS7M7spv09mCZBtJILoBdO2kPtjWT7pPgcVRtlRPjUivlcGPJZAh3CPwBESocCZBfhZB4XGYLgxwWxZCAoQ13QUQMQdjBoOMYSZAD8ljY9l7nfxN2VxGAMdoCiaAZDZD"
VERIFY_TOKEN = "mywhatsbot123"
PHONE_NUMBER_ID = "884166421438641"

# -------------------------
# ✅ Email configuration
# -------------------------
EMAIL_FROM = "personalbusinessassisstant@gmail.com"
EMAIL_TO = "iconspage1@gmail.com"
EMAIL_PASSWORD = "lkzrsmwmpivkxdzu"  # cleaned

# -------------------------
# ✅ OpenAI Key
# -------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-REPLACE_WITH_YOURS")

# -------------------------
# ✅ Memory & States
# -------------------------
user_memory = {}
user_state = {}

# ----------------------------------------------------
# ✅ FULL PRODUCT IMAGE DATABASE (all Bucch products)
# ----------------------------------------------------
product_links = {
    # ✅ Fuel products
    "fuel": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0968-scaled.jpg",
    "diesel": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg",
    "pms": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0968-scaled.jpg",
    "ago": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg",
    "kerosene": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg",

    # ✅ Lubricants
    "engine oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0993-scaled.jpg",
    "lubricant": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1017-scaled.jpg",
    "lubricant 1": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1017-scaled.jpg",
    "lubricant 2": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1008-2.jpg",
    "lubricant 3": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0993-scaled.jpg",

    # ✅ Gear / Transmission Oils
    "gear oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1008-2.jpg",
    "transmission oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0979-scaled.jpg",
    "transmission fluid": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0979-scaled.jpg",

    # ✅ Hydraulic Oils
    "hydraulic oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0970-scaled.jpg",
    "hydraulic fluid": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0970-scaled.jpg",

    # ✅ Drums / Bulk containers
    "drum": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0997-scaled.jpg",
    "oil drum": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0997-scaled.jpg",

    # ✅ General fallback
    "bucch": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Energy-Oil.jpg"
}

DEFAULT_IMAGE = "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Energy-Oil.jpg"


# ----------------------------------------------------
# ✅ EMAIL SENDER
# ----------------------------------------------------
def send_order_email(order):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"New WhatsApp Order — Bucch Energy: {order.get('product')}"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        msg.set_content(
            f"Product: {order.get('product')}\n"
            f"Quantity: {order.get('quantity')}\n"
            f"Name: {order.get('name')}\n"
            f"Phone: {order.get('phone')}\n"
            f"Address: {order.get('address')}\n"
            f"Notes: {order.get('notes')}\n"
            f"WhatsApp ID: {order.get('user_id')}"
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)

        return True
    except:
        return False


# ----------------------------------------------------
# ✅ WEBHOOK VERIFY
# ----------------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Invalid token", 403


# ----------------------------------------------------
# ✅ WEBHOOK RECEIVER
# ----------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        messages = data["entry"][0]["changes"][0]["value"].get("messages")
        if not messages:
            return jsonify(success=True)

        message = messages[0]
        from_number = message["from"]

        # Initialize memory
        user_memory.setdefault(from_number, [])
        user_state.setdefault(from_number, {"stage": None, "order": {}})

        if message["type"] == "text":
            user_text = message["text"]["body"].lower().strip()

            # ✅ First check for image requests
            for keyword, img_url in product_links.items():
                if keyword in user_text:
                    send_image(from_number, img_url, f"{keyword.title()} — Bucch Energy ⚡")
                    return jsonify(success=True)

            # ✅ If in order flow
            if user_state[from_number]["stage"]:
                handle_order_message(from_number, user_text)
                return jsonify(success=True)

            # ✅ Start order
            if user_text in ["order", "place order", "i want to order"]:
                user_state[from_number] = {"stage": "ask_product", "order": {"user_id": from_number}}
                send_message(from_number, "Great! What product would you like to order?")
                return jsonify(success=True)

            # ✅ Normal conversation
            ai_reply = chat_with_ai(user_text, from_number)
            send_message(from_number, ai_reply)

        else:
            send_message(from_number, "I currently support text only.")

    except Exception as e:
        print("Webhook error:", e)

    return jsonify(success=True)


# ----------------------------------------------------
# ✅ ORDER FLOW STATE MACHINE
# ----------------------------------------------------
def handle_order_message(user_id, text):
    state = user_state[user_id]
    order = state["order"]

    if text == "cancel":
        user_state[user_id] = {"stage": None, "order": {}}
        send_message(user_id, "Order cancelled ✅")
        return

    stage = state["stage"]

    if stage == "ask_product":
        order["product"] = text
        state["stage"] = "ask_quantity"
        return send_message(user_id, "How many units?")

    if stage == "ask_quantity":
        order["quantity"] = text
        state["stage"] = "ask_name"
        return send_message(user_id, "Your full name?")

    if stage == "ask_name":
        order["name"] = text
        state["stage"] = "ask_phone"
        return send_message(user_id, "Phone number?")

    if stage == "ask_phone":
        order["phone"] = text
        state["stage"] = "ask_address"
        return send_message(user_id, "Delivery address?")

    if stage == "ask_address":
        order["address"] = text
        state["stage"] = "ask_notes"
        return send_message(user_id, "Any notes? (type 'no' if none)")

    if stage == "ask_notes":
        order["notes"] = "" if text == "no" else text
        state["stage"] = "confirm"
        return send_message(
            user_id,
            f"✅ Order Summary:\n"
            f"Product: {order['product']}\n"
            f"Quantity: {order['quantity']}\n"
            f"Name: {order['name']}\n"
            f"Phone: {order['phone']}\n"
            f"Address: {order['address']}\n"
            f"Notes: {order['notes']}\n\n"
            f"Type 'confirm' to place order."
        )

    if stage == "confirm":
        if text == "confirm":
            if send_order_email(order):
                send_message(user_id, "✅ Order placed successfully! Our sales team will contact you.")
            else:
                send_message(user_id, "⚠️ Order received but email failed.")
        user_state[user_id] = {"stage": None, "order": {}}


# ----------------------------------------------------
# ✅ SEND WHATSAPP TEXT
# ----------------------------------------------------
def send_message(to, text):
    url = f"https://graph.facebook.com/v24.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload, headers=headers)


# ----------------------------------------------------
# ✅ SEND WHATSAPP IMAGE
# ----------------------------------------------------
def send_image(to, link, caption=""):
    url = f"https://graph.facebook.com/v24.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": link, "caption": caption}
    }
    requests.post(url, json=payload, headers=headers)


# ----------------------------------------------------
# ✅ GPT AI CHAT
# ----------------------------------------------------
def chat_with_ai(prompt, user_id):
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

        response = requests.post(
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

        reply = response.json()["choices"][0]["message"]["content"]
        return reply
    except:
        return "⚠️ I’m having issues responding right now."


# ----------------------------------------------------
# ✅ RUN SERVER
# ----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from flask import Flask, request, jsonify
import requests
import os
import time
import smtplib
from email.message import EmailMessage
from bs4 import BeautifulSoup

app = Flask(__name__)

# -----------------------------
# WhatsApp Cloud API Config
# -----------------------------
ACCESS_TOKEN = "EAASZCI1ZAownwBP5Ya8mnNJNVbc3Oo2R3MrJbCLK7Fs2yLBqbDEzOaxZBouYGsgCVqQGWCsFqe9rS7M7spv09mCZBtJILoBdO2kPtjWT7pPgcVRtlRPjUivlcGPJZAh3CPwBESocCZBfhZB4XGYLgxwWxZCAoQ13QUQMQdjBoOMYSZAD8ljY9l7nfxN2VxGAMdoCiaAZDZD"
VERIFY_TOKEN = "mywhatsbot123"
PHONE_NUMBER_ID = "884166421438641"

# -----------------------------
# Email Config
# -----------------------------
EMAIL_FROM = "personalbusinessassisstant@gmail.com"
EMAIL_TO = "iconspage1@gmail.com"
EMAIL_PASSWORD = "lkzrsmwmpivkxdzu"

# -----------------------------
# OpenAI Config
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-REPLACE_WITH_YOURS")

# -----------------------------
# Memory
# -----------------------------
user_memory = {}
user_state = {}  # now includes product_select state

# ===============================================================
# ✅ VERIFIED PRODUCT IMAGES + REAL NAMES (CLEAN, CORRECT)
# ===============================================================
product_links = {

    # ✅ Fuels
    "pms": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0968-scaled.jpg",
    "petrol": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0968-scaled.jpg",

    "ago": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg",
    "diesel": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg",

    "kerosene": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg",

    # ✅ Engine Oils
    "engine oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0993-scaled.jpg",
    "bucch engine oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0993-scaled.jpg",

    # ✅ Gear & Transmission Oils
    "gear oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1008-2.jpg",
    "bucch gear oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1008-2.jpg",

    "transmission fluid": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0979-scaled.jpg",

    # ✅ Hydraulic Oils
    "hydraulic oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0970-scaled.jpg",
    "hydraulic fluid": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0970-scaled.jpg",

    # ✅ Bulk Drums
    "oil drum": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0997-scaled.jpg",
    "drum": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0997-scaled.jpg",

    # ✅ Fallback brand image
    "bucch": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Energy-Oil.jpg"
}


DEFAULT_IMAGE = "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Energy-Oil.jpg"


# ===============================================================
# ✅ EMAIL SENDER — UNCHANGED
# ===============================================================
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
        print("Email Error:", e)
        return False


# ===============================================================
# ✅ WEBHOOK VERIFY — UNCHANGED
# ===============================================================
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403


# ===============================================================
# ✅ WEBHOOK RECEIVER — NEW FEATURE ADDED HERE
# ===============================================================
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

        # Ensure state
        user_memory.setdefault(from_number, [])
        user_state.setdefault(from_number, {"stage": None, "order": {}, "product_select": None})

        if message["type"] == "text":
            user_text = message["text"]["body"].lower().strip()
            print("User said:", user_text)

            # ======================================================
            # ✅ 1) NEW FEATURE: Detect ANY picture/photo request
            # ======================================================
            trigger_words = ("picture", "photo", "image", "show", "see", "view")

            if any(w in user_text for w in trigger_words):
                user_state[from_number]["product_select"] = "awaiting_choice"

                # Build the numbered product list
                product_list = "\n".join(
                    [f"{i+1}. {name.title()}" for i, name in enumerate(product_links.keys())]
                )

                send_message(
                    from_number,
                    "Sure! Which product picture would you like to see?\n\n"
                    "Reply with the **number** or the **product name**:\n\n"
                    f"{product_list}"
                )
                return jsonify(success=True)

            # ======================================================
            # ✅ 2) If user is selecting from the list
            # ======================================================
            if user_state[from_number]["product_select"] == "awaiting_choice":

                products = list(product_links.keys())

                # User chose by number
                if user_text.isdigit():
                    idx = int(user_text) - 1
                    if 0 <= idx < len(products):
                        chosen = products[idx]
                        link = product_links[chosen]
                        send_image(from_number, link, f"{chosen.title()} — Bucch Energy ⚡")
                        user_state[from_number]["product_select"] = None
                        return jsonify(success=True)
                    else:
                        send_message(from_number, "❌ Invalid number. Try again.")
                        return jsonify(success=True)

                # User chose by name
                for key in products:
                    if key in user_text:
                        send_image(from_number, product_links[key], f"{key.title()} — Bucch Energy ⚡")
                        user_state[from_number]["product_select"] = None
                        return jsonify(success=True)

                send_message(from_number, "❌ Not found. Please enter a number or product name.")
                return jsonify(success=True)

            # ======================================================
            # ✅ 3) ORDER FLOW (UNCHANGED)
            # ======================================================
            state = user_state[from_number]
            if state["stage"]:
                handle_order_message(from_number, user_text)
                return jsonify(success=True)

            if user_text in ("order", "place an order", "i want to order", "place order"):
                user_state[from_number] = {"stage": "ask_product", "order": {"user_id": from_number}, "product_select": None}
                send_message(from_number, "Sure — what product would you like to order?")
                return jsonify(success=True)

            # ======================================================
            # ✅ 4) NORMAL CHAT
            # ======================================================
            ai_reply = chat_with_ai(user_text, from_number)
            send_message(from_number, ai_reply)

        else:
            send_message(from_number, "I can only read text for now ✅")

    except Exception as e:
        print("Webhook Error:", e)

    return jsonify(success=True)


# ===============================================================
# ✅ CLEAN LABEL FUNCTION (unchanged)
# ===============================================================
def get_clean_label(keyword):

    mapping = {
        "pms": "PMS (Petrol)",
        "petrol": "PMS (Petrol)",
        "ago": "AGO (Diesel)",
        "diesel": "AGO (Diesel)",
        "kerosene": "Kerosene",
        "engine oil": "Bucch Engine Oil",
        "bucch engine oil": "Bucch Engine Oil",
        "gear oil": "Bucch Gear Oil",
        "bucch gear oil": "Bucch Gear Oil",
        "transmission fluid": "Transmission Fluid",
        "hydraulic oil": "Hydraulic Oil",
        "hydraulic fluid": "Hydraulic Oil",
        "oil drum": "Oil Drum (Bulk)",
        "drum": "Oil Drum (Bulk)",
    }

    return mapping.get(keyword, keyword.title())


# ===============================================================
# ✅ ORDER SYSTEM — UNCHANGED
# ===============================================================
def handle_order_message(user_id, text):

    state = user_state[user_id]
    stage = state["stage"]
    order = state["order"]

    if text == "cancel":
        user_state[user_id] = {"stage": None, "order": {}, "product_select": None}
        send_message(user_id, "✅ Order cancelled.")
        return

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
            "Type 'confirm' to place order."
        )
        return

    if stage == "confirm":
        if text == "confirm":
            send_order_email(order)
            send_message(user_id, "✅ Order placed! Our sales team will contact you.")
        user_state[user_id] = {"stage": None, "order": {}, "product_select": None}


# ===============================================================
# ✅ SEND WHATSAPP MSG
# ===============================================================
def send_message(to, message):
    url = f"https://graph.facebook.com/v24.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    try:
        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print("Send text error:", e)


# ===============================================================
# ✅ SEND WHATSAPP IMAGE
# ===============================================================
def send_image(to, link, caption=""):
    url = f"https://graph.facebook.com/v24.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": link, "caption": caption}
    }
    try:
        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print("Send image error:", e)


# ===============================================================
# ✅ AI CHAT — UNCHANGED
# ===============================================================
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
        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI Error:", e)
        return "⚠️ I’m having trouble right now. Please try again!"


# ===============================================================
# ✅ RUN SERVER
# ===============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

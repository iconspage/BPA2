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

# 🔹 Email config (sender account)
EMAIL_FROM = "personalbusinessassisstant@gmail.com"   # sender
EMAIL_TO = "iconspage1@gmail.com"                    # receiver
# App password you provided; remove any spaces just in case
EMAIL_PASSWORD = "lkzr smwm pivk xdzu".replace(" ", "")

# 🔹 OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-REPLACE_WITH_YOURS")

# 🔹 Simple in-memory user context and order states
user_memory = {}   # stores conversation history and bot/user replies
user_state = {}    # stores order flow states and partial order data per user

# 🔹 Product image mapping
product_links = {
    "lubricant 1": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1017-scaled.jpg",
    "lubricant 2": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1008-2.jpg",
    "lubricant 3": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0993-scaled.jpg",
    "engine oil": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Energy-Oil.jpg",
    "fuel 1": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot0968-scaled.jpg",
    "fuel 2": "https://bucchenergy.com/wp-content/uploads/2025/08/Bucch-Prouct-shoot1020-scaled.jpg"
}


# -----------------------
# Helper: send email order
# -----------------------
def send_order_email(order):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"New WhatsApp Order — Bucch Energy: {order.get('product','(no product)')}"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        body_lines = [
            f"New order received via WhatsApp:",
            "",
            f"Product: {order.get('product', '')}",
            f"Quantity: {order.get('quantity', '')}",
            f"Customer name: {order.get('name', '')}",
            f"Phone: {order.get('phone', '')}",
            f"Delivery address: {order.get('address', '')}",
            f"Additional notes: {order.get('notes', '')}",
            "",
            f"WhatsApp user id: {order.get('user_id', '')}",
            "",
            "— This email was sent automatically by the WhatsApp bot."
        ]
        msg.set_content("\n".join(body_lines))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print("✅ Order email sent.")
        return True
    except Exception as e:
        print("❌ Failed to send order email:", e)
        return False


# -----------------------
# Webhook verify
# -----------------------
@app.route("/webhook", methods=["GET"])
def verify():
    verify_token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if verify_token == VERIFY_TOKEN:
        return challenge
    return "Verification failed", 403


# -----------------------
# Webhook receive
# -----------------------
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

        # ensure memory structures exist
        if from_number not in user_memory:
            user_memory[from_number] = []
        if from_number not in user_state:
            user_state[from_number] = {"stage": None, "order": {}}

        if message.get("type") == "text":
            user_text = message["text"]["body"].strip().lower()
            print(f"💬 Message from {from_number}: {user_text}")

            # ---------- ORDER FLOW HANDLER ----------
            state = user_state[from_number]

            # If user is in the middle of an order, route input there
            if state["stage"] is not None:
                handle_order_message(from_number, user_text)
                return jsonify(success=True)

            # If user explicitly asks to start an order (only triggers on explicit "order" commands)
            if user_text in ("order", "place an order", "i want to order", "place order"):
                # initialize order state
                user_state[from_number] = {"stage": "ask_product", "order": {"user_id": from_number}}
                send_message(from_number, "Sure — I can help with that. Which product would you like to order? (Type product name)")
                return jsonify(success=True)

            # ---------- PRODUCT IMAGE MATCH ----------
            if any(keyword in user_text for keyword in product_links.keys()):
                for product, link in product_links.items():
                    if product in user_text:
                        send_image(from_number, link, f"Here’s the image for {product.title()} ⚡")
                        return jsonify(success=True)

            # ---------- NORMAL CHAT ----------
            ai_reply = chat_with_ai(user_text, from_number)
            send_message(from_number, ai_reply)

        else:
            send_message(from_number, "⚠ I can only read text messages for now 🤖")

    except Exception as e:
        print("❌ Error handling webhook:", e)

    return jsonify(success=True)


# -----------------------
# Order message state machine
# -----------------------
def handle_order_message(user_id, user_text):
    state = user_state[user_id]
    stage = state["stage"]
    order = state["order"]

    # user wants to cancel
    if user_text in ("cancel", "stop", "abort"):
        user_state[user_id] = {"stage": None, "order": {}}
        send_message(user_id, "Order canceled. If you need anything else, just type it in.")
        return

    if stage == "ask_product":
        order["product"] = user_text
        state["stage"] = "ask_quantity"
        send_message(user_id, f"How many units or litres of *{user_text}* would you like?")
        return

    if stage == "ask_quantity":
        order["quantity"] = user_text
        state["stage"] = "ask_name"
        send_message(user_id, "Great — may I have your full name, please?")
        return

    if stage == "ask_name":
        order["name"] = user_text
        state["stage"] = "ask_phone"
        send_message(user_id, "Thanks. What phone number can we reach you on?")
        return

    if stage == "ask_phone":
        order["phone"] = user_text
        state["stage"] = "ask_address"
        send_message(user_id, "Got it. What is the delivery address (city / street)?")
        return

    if stage == "ask_address":
        order["address"] = user_text
        state["stage"] = "ask_notes"
        send_message(user_id, "Any additional notes or instructions? If none, type 'no'.")
        return

    if stage == "ask_notes":
        order["notes"] = "" if user_text in ("no", "none") else user_text
        # summarize and ask for confirmation
        summary = (
            f"Order summary:\n"
            f"- Product: {order.get('product')}\n"
            f"- Quantity: {order.get('quantity')}\n"
            f"- Name: {order.get('name')}\n"
            f"- Phone: {order.get('phone')}\n"
            f"- Address: {order.get('address')}\n"
            f"- Notes: {order.get('notes')}\n\n"
            "Reply 'confirm' to place the order or 'cancel' to abort."
        )
        state["stage"] = "awaiting_confirmation"
        send_message(user_id, summary)
        return

    if stage == "awaiting_confirmation":
        if user_text in ("confirm", "yes", "y"):
            # finalize order: send email
            order["user_id"] = user_id
            sent = send_order_email(order)
            if sent:
                send_message(user_id, "✅ Your order has been placed! We emailed the details and our sales team will contact you soon.")
            else:
                send_message(user_id, "⚠️ Your order was received but I couldn't send the confirmation email — please contact sales directly.")
            # reset state
            user_state[user_id] = {"stage": None, "order": {}}
            return
        else:
            send_message(user_id, "Order not confirmed. If you want to cancel, type 'cancel'. To place a new order, type 'order'.")
            user_state[user_id] = {"stage": None, "order": {}}
            return

    # fallback
    send_message(user_id, "I didn't understand that. To cancel the order flow, type 'cancel'.")


# -----------------------
# Send text message
# -----------------------
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


# -----------------------
# Send image to WhatsApp
# -----------------------
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
        "image": {
            "link": image_url,
            "caption": caption
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("📸 Image sent:", response.status_code, response.text)
    except Exception as e:
        print("❌ Failed to send image:", e)


# -----------------------
# ChatGPT integration with retry & fallback (unchanged behavior)
# -----------------------
def chat_with_ai(prompt, user_id):
    try:
        if user_id not in user_memory:
            user_memory[user_id] = []

        user_memory[user_id].append({"user": prompt})

        history = user_memory[user_id][-5:]
        history_text = "\n".join(
            [f"User: {h.get('user', '')}\nBot: {h.get('bot', '')}" for h in history]
        )

        # Fetch live website data
        try:
            site_url = "https://bucchenergy.com"
            html = requests.get(site_url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            website_text = ' '.join(p.get_text() for p in soup.find_all("p"))[:3000]
        except Exception as e:
            print("⚠️ Website fetch failed:", e)
            website_text = "Bucch Energy provides fuels, lubricants, and petroleum products in West Africa."

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        # System message: avoid 'Bot:' prefixes
        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": (
                    "You are PBA.Bucch — a friendly and professional assistant for Bucch Energy. "
                    "Do not prefix your messages with 'Bot:', 'Assistant:', or anything similar. "
                    f"Reference info: {website_text}"
                )},
                {"role": "user", "content": f"{history_text}\n\nUser: {prompt}"}
            ]
        }

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
                    return reply + "\n\n— PBA.Bucch ⚡"
                else:
                    print("⚠️ AI incomplete response:", data)
            except Exception as e:
                print(f"⚠️ AI call failed (try {i+1}):", e)
                time.sleep(2)

        return "⚡ Sorry, I’m having trouble right now. Please try again!"

    except Exception as e:
        print("⚙️ AI error:", e)
        return "⚡ Sorry, I’m having trouble right now. Please try again!"


# -----------------------
# Run Flask app
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

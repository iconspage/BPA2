from flask import Flask, request, jsonify
import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

app = Flask(__name__)

# 🔹 WhatsApp Config (real credentials)
ACCESS_TOKEN = "EAASZCI1ZAownwBP2Pv81sVieaiJvAIf0RN92JL8QeB43ZBtFDNhf4s5kZCvoRYxqOks7AWKFYTHA41jgPeOCLMkG8pkUeWHXkCNEZB3Seyx3YOt9vg3IzeGd6R35Bn933eTamVaVllGYr8ZCKrqbEnNWX9LJ3m6i22pJdq6ODVSm5khvZCivbEZBZB4UWt6P9Jo6HZAIXgLNCSHTHENjZBO1ZAROrZBAjCZCBuQj1BMXFYlfKZB1VOCM4BW8e7aZCeQ0qHjOMqJUmXsjPpLxa4bIZB5iZAXKutZBecL"
VERIFY_TOKEN = "mywhatsbot123"
PHONE_NUMBER_ID = "884166421438"

# 🔹 OpenAI key stored securely
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔹 Cache storage
cached_data = {"text": "", "timestamp": 0}
CACHE_DURATION = 60 * 60 * 3  # 3 hours


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

            if message.get("type") == "text":
                text = message["text"]["body"]
                print(f"Message from {from_number}: {text}")

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


# ✅ Full-Site Crawl with Caching
def get_website_text():
    global cached_data
    now = time.time()

    # Use cache if not expired
    if cached_data["text"] and now - cached_data["timestamp"] < CACHE_DURATION:
        print("🔄 Using cached website content")
        return cached_data["text"]

    print("🌐 Crawling Bucch Energy website...")
    base_url = "https://bucchenergy.com"
    visited = set()
    all_text = []

    def crawl(url, depth=0):
        if depth > 1 or url in visited:
            return
        visited.add(url)

        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text(separator=" ").lower()
            all_text.append((url, text))

            for a in soup.find_all("a", href=True):
                link = urljoin(base_url, a["href"])
                if urlparse(link).netloc == urlparse(base_url).netloc:
                    crawl(link, depth + 1)
        except Exception as e:
            print(f"Error crawling {url}:", e)

    crawl(base_url)

    # Store in cache
    combined_text = "\n\n".join([f"{url}\n{text}" for url, text in all_text])
    cached_data = {"text": combined_text, "timestamp": now}
    print("✅ Website content cached.")
    return combined_text


# ✅ Search Function
def search_website(query):
    site_text = get_website_text()
    query = query.lower()
    matches = []

    for block in site_text.split("\n\n"):
        if query in block:
            snippet_start = block.find(query)
            snippet = block[snippet_start:snippet_start+500].strip()
            lines = block.split("\n", 1)
            url = lines[0] if lines else "Unknown"
            matches.append(f"🔎 Found match on {url}:\n\n{snippet}...")

    return "\n\n".join(matches[:2]) if matches else None


# ✅ ChatGPT AI Integration
def chat_with_ai(prompt):
    try:
        # Step 1: Try searching Bucch’s website first
        site_result = search_website(prompt)
        if site_result:
            return site_result + "\n\nWould you like me to confirm stock or delivery options?\n\n— PBA.Bucch ⚡"

        # Step 2: Fall back to ChatGPT AI
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
                        "You are PBA.Bucch — a friendly and professional customer service assistant "
                        "for Bucch Energy, a company that provides clean energy products and battery solutions. "
                        "You help customers with product information, availability, and orders. "
                        "Always reply naturally and politely. "
                        "Never mention OpenAI, ChatGPT, or AI — you are just Bucch Energy’s virtual assistant."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return reply + "\n\n— PBA.Bucch ⚡"

    except Exception as e:
        print("AI error:", e)
        return "⚡ Sorry, I’m having a little trouble replying right now — please try again!"


# ✅ Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

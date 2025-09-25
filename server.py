import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS


app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Токен и чат берём из переменных окружения
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# Фоллбек на ваш chat_id, если переменная окружения не задана
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "338788514")


def send_to_telegram(text: str) -> tuple[bool, str]:
    """Отправка текста в Telegram-бота."""
    if not BOT_TOKEN:
        return False, "BOT_TOKEN not set"
    if not CHAT_ID:
        return False, "CHAT_ID not set"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=10)
    except Exception as e:
        return False, f"requests_error: {e}"
    if not resp.ok:
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        return False, str(err)
    return True, ""


@app.route("/api/lead", methods=["POST", "OPTIONS"]) 
def lead():
    # Preflight CORS
    if request.method == "OPTIONS":
        return ("", 200)
    """Приём заявки с формы и пересылка в Telegram."""
    # Поддержим и form-data, и JSON
    src = request.form if request.form else (request.json or {})

    name = (src.get("your-name") or "").strip()
    email = (src.get("your-email") or "").strip()
    phone = (src.get("your-phone") or "").strip()
    message = (src.get("your-message") or "").strip()

    text = (
        "📩 <b>Новая заявка с сайта</b>\n"
        f"👤 Имя: {name or '-'}\n"
        f"✉️ Email: {email or '-'}\n"
        f"📞 Телефон: {phone or '-'}\n"
        f"📝 Сообщение: {message or '-'}"
    )

    ok, err = send_to_telegram(text)
    if ok:
        return jsonify({"ok": True})
    # лог в stdout контейнера
    print("Telegram API error:", err, flush=True)
    return jsonify({"ok": False, "error": "telegram_failed", "details": err}), 500


if __name__ == "__main__":
    # Отдаём статический сайт и API на одном порту
    @app.get('/')
    def index():
        return send_from_directory('.', 'index.html')

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))



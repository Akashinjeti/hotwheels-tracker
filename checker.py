"""
checker.py — HotWheels Restock Checker
Runs headless via GitHub Actions every 15 minutes
No Streamlit needed — pure Python
Built by Akash Injeti ⚡
"""

import os
import json
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─── CONFIG ────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = "1695508762"
SMTP_EMAIL         = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD      = os.environ.get("SMTP_PASSWORD", "")
PINCODE            = "500081"
LAT, LON           = "17.4065", "78.4772"   # Hyderabad

# State file — tracks previous status to detect OUT→IN transition
STATE_FILE = "last_state.json"

PLATFORMS = {
    "blinkit": {
        "name":  "Blinkit",
        "emoji": "🟡",
        "link":  "https://blinkit.com/s/?q=hot+wheels",
    },
    "zepto": {
        "name":  "Zepto",
        "emoji": "🟣",
        "link":  "https://www.zeptonow.com/search?query=hot+wheels",
    },
    "swiggy": {
        "name":  "Swiggy Instamart",
        "emoji": "🟠",
        "link":  "https://www.swiggy.com/instamart/search?query=hot+wheels",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-IN,en;q=0.9",
}

# ─── HELPERS ───────────────────────────────────────────────────
def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"blinkit": "outofstock", "zepto": "outofstock", "swiggy": "outofstock"}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️  No Telegram token")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message,
                  "parse_mode": "HTML", "disable_web_page_preview": False},
            timeout=10
        )
        ok = r.status_code == 200
        print(f"  📱 Telegram: {'✅ sent' if ok else '❌ failed'}")
        return ok
    except Exception as e:
        print(f"  📱 Telegram error: {e}")
        return False

def send_email(subject, body_html):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("⚠️  No SMTP config")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"HotWheels Tracker 🚗 <{SMTP_EMAIL}>"
        msg["To"]      = SMTP_EMAIL
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(SMTP_EMAIL, SMTP_PASSWORD)
            s.sendmail(SMTP_EMAIL, SMTP_EMAIL, msg.as_string())
        print(f"  📧 Email: ✅ sent to {SMTP_EMAIL}")
        return True
    except Exception as e:
        print(f"  📧 Email error: {e}")
        return False

def fire_alerts(platform_key, products):
    p    = PLATFORMS[platform_key]
    now  = datetime.now().strftime("%d %b %Y, %H:%M")
    lines= "\n".join([f"• {x['name']} — {x['price']}" for x in products])

    # Telegram
    tg_msg = f"""{p['emoji']} <b>🚗 HOT WHEELS RESTOCKED on {p['name'].upper()}!</b>

📍 Pincode: {PINCODE} · Hyderabad
⏰ {now}

<b>In Stock Now:</b>
{lines}

🛒 <a href="{p['link']}">Order Now on {p['name']}</a>

<i>⚡ Hurry — they sell out fast!</i>"""
    send_telegram(tg_msg)

    # Email
    product_rows = "".join([
        f'<div style="padding:.5rem 0;border-bottom:1px solid #222;">'
        f'<b style="color:#FFD700;">{x["name"]}</b> — '
        f'<span style="color:#00C896;">{x["price"]}</span></div>'
        for x in products
    ])
    email_html = f"""
    <div style="font-family:Arial,sans-serif;background:#0a0a0a;color:#F0F0F0;padding:2rem;max-width:500px;margin:0 auto;border-radius:12px;">
      <h1 style="color:#FFD700;letter-spacing:4px;margin:0;">🚗 HOTWHEELS</h1>
      <h2 style="color:#00C896;margin:.5rem 0;">Restocked on {p['name']}!</h2>
      <p style="color:#666;">Detected at <b style="color:#fff;">{now}</b><br>
         Pincode: <b style="color:#fff;">{PINCODE}</b> · Hyderabad</p>
      <div style="background:#141414;border:1px solid #222;border-radius:8px;padding:1rem;margin:1rem 0;">
        {product_rows}
      </div>
      <a href="{p['link']}"
         style="display:inline-block;background:#FFD700;color:#000;font-weight:700;
                padding:14px 32px;border-radius:8px;text-decoration:none;
                letter-spacing:1px;margin-top:1rem;font-size:1rem;">
        🛒 ORDER NOW
      </a>
      <p style="color:#333;font-size:.72rem;margin-top:2rem;border-top:1px solid #1a1a1a;padding-top:1rem;">
        HotWheels Tracker · Built by Akash Injeti · Pincode {PINCODE}
      </p>
    </div>"""
    send_email(f"🚗 Hot Wheels RESTOCKED on {p['name']}! ({PINCODE})", email_html)

# ─── PLATFORM CHECKERS ─────────────────────────────────────────
def check_blinkit():
    products = []
    try:
        r = requests.get(
            "https://blinkit.com/v2/search/",
            params={"q": "hot wheels", "page_no": 1, "page_size": 20},
            headers={**HEADERS, "app_version": "3.0",
                     "auth_key": "2a9ef3e3db36bed41e357a8fe83e1fe1",
                     "lat": LAT, "lon": LON},
            timeout=15
        )
        if r.status_code == 200:
            for obj in r.json().get("objects", []):
                for item in obj.get("items", []):
                    name = item.get("name","") or item.get("title","")
                    if "hot wheel" in name.lower() or "hotwheels" in name.lower():
                        products.append({
                            "name": name,
                            "price": f"₹{item.get('price', item.get('mrp','?'))}",
                            "in_stock": item.get("in_stock", item.get("available", False))
                        })
    except: pass

    if not products:
        try:
            r = requests.get("https://blinkit.com/s/?q=hot+wheels",
                             headers=HEADERS, timeout=15)
            txt = r.text.lower()
            if "hot wheel" in txt or "hotwheels" in txt:
                oos = any(x in txt for x in ["out of stock","notify me","sold out"])
                products.append({"name":"Hot Wheels","price":"—","in_stock": not oos})
        except: pass

    return products

def check_zepto():
    products = []
    try:
        r = requests.get(
            "https://api.zeptonow.com/api/v3/search/",
            params={"query":"hot wheels","page_number":0,"page_size":20,"pincode":PINCODE},
            headers={**HEADERS, "store_id":"1","requestid":"tracker","appversion":"11.0.0"},
            timeout=15
        )
        if r.status_code == 200:
            for section in r.json().get("data",{}).get("sections",[]):
                for item in section.get("items",[]):
                    name = item.get("name","") or item.get("product",{}).get("name","")
                    if "hot wheel" in name.lower() or "hotwheels" in name.lower():
                        products.append({
                            "name": name,
                            "price": f"₹{item.get('discounted_price', item.get('mrp','?'))}",
                            "in_stock": not item.get("is_out_of_stock", True)
                        })
    except: pass

    if not products:
        try:
            r = requests.get("https://www.zeptonow.com/search?query=hot+wheels",
                             headers=HEADERS, timeout=15)
            txt = r.text.lower()
            if "hot wheel" in txt or "hotwheels" in txt:
                oos = any(x in txt for x in ["out of stock","notify me","sold out"])
                products.append({"name":"Hot Wheels","price":"—","in_stock": not oos})
        except: pass

    return products

def check_swiggy():
    products = []
    try:
        r = requests.get(
            "https://www.swiggy.com/api/instamart/search",
            params={"query":"hot wheels","pageNumber":0,"pageSize":20,"lat":LAT,"lng":LON},
            headers={**HEADERS, "Referer":"https://www.swiggy.com/"},
            timeout=15
        )
        if r.status_code == 200:
            for item in r.json().get("data",{}).get("products",[]):
                name = item.get("display_name","") or item.get("name","")
                if "hot wheel" in name.lower() or "hotwheels" in name.lower():
                    products.append({
                        "name": name,
                        "price": f"₹{item.get('price','?')}",
                        "in_stock": item.get("inStock", item.get("available", False))
                    })
    except: pass

    if not products:
        try:
            r = requests.get("https://www.swiggy.com/instamart/search?query=hot+wheels",
                             headers=HEADERS, timeout=15)
            txt = r.text.lower()
            if "hot wheel" in txt or "hotwheels" in txt:
                oos = any(x in txt for x in ["out of stock","notify me","sold out"])
                products.append({"name":"Hot Wheels","price":"—","in_stock": not oos})
        except: pass

    return products

# ─── MAIN ──────────────────────────────────────────────────────
if __name__ == "__main__":
    now = datetime.now().strftime("%d %b %Y, %H:%M:%S")
    print(f"\n🚗 HotWheels Checker — {now}")
    print(f"📍 Pincode: {PINCODE} · Hyderabad\n")

    # Load previous state
    prev_state = load_state()
    new_state  = dict(prev_state)

    checkers = {
        "blinkit": check_blinkit,
        "zepto":   check_zepto,
        "swiggy":  check_swiggy,
    }

    for key, fn in checkers.items():
        p = PLATFORMS[key]
        print(f"Checking {p['emoji']} {p['name']}...")
        try:
            products   = fn()
            in_stock   = [x for x in products if x.get("in_stock")]
            new_status = "instock" if in_stock else "outofstock"
            prev_status= prev_state.get(key, "outofstock")

            print(f"  Status: {new_status} (was: {prev_status})")

            # ── Only alert on OUT → IN transition ──
            if prev_status == "outofstock" and new_status == "instock":
                print(f"  🔥 RESTOCK DETECTED on {p['name']}! Firing alerts...")
                fire_alerts(key, in_stock)
            elif new_status == "instock":
                print(f"  ✅ Still in stock (no alert — already knew)")
            else:
                print(f"  ❌ Out of stock")

            new_state[key] = new_status

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Save new state for next run
    save_state(new_state)
    print(f"\n✅ Done — state saved for next check\n")

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
SMTP_EMAIL    = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
PINCODE       = "500081"
LAT, LON      = "17.4065", "78.4772"   # Hyderabad

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
    count = len(products)
    car_names = ", ".join([x['name'] for x in products])
    print(f"  🚗 Cars in stock: {car_names}")

    # Build product rows for email
    product_rows_html = "".join([
        f"""<tr>
          <td style="padding:10px 14px;border-bottom:1px solid #1a1a1a;font-size:1.1rem;">🚗</td>
          <td style="padding:10px 14px;border-bottom:1px solid #1a1a1a;">
            <b style="color:#FFD700;">{x['name']}</b>
          </td>
          <td style="padding:10px 14px;border-bottom:1px solid #1a1a1a;text-align:right;">
            <span style="color:#00C896;font-weight:700;">{x['price']}</span>
          </td>
        </tr>"""
        for x in products
    ])

    email_html = f"""
    <div style="font-family:Arial,sans-serif;background:#0a0a0a;color:#F0F0F0;
                max-width:520px;margin:0 auto;">

      <!-- Header -->
      <div style="background:linear-gradient(135deg,#1a1200,#111);padding:2rem;
                  text-align:center;border-bottom:3px solid #FFD700;">
        <div style="font-size:3rem;">🚗</div>
        <h1 style="color:#FFD700;letter-spacing:5px;margin:.3rem 0;font-size:2rem;">HOTWHEELS</h1>
        <div style="color:#666;letter-spacing:3px;font-size:.72rem;">RESTOCK ALERT · {PINCODE} HYDERABAD</div>
      </div>

      <!-- Platform + time -->
      <div style="background:#111;padding:1rem 1.5rem;border-bottom:1px solid #222;
                  display:flex;justify-content:space-between;align-items:center;">
        <div>
          <span style="font-size:1.2rem;">{p['emoji']}</span>
          <b style="color:#E8E8E8;margin-left:.4rem;">{p['name']}</b>
        </div>
        <div style="display:flex;align-items:center;gap:1rem;">
          <span style="color:#555;font-size:.78rem;">⏰ {now}</span>
          <span style="background:rgba(0,200,150,.15);color:#00C896;font-weight:700;
                       font-size:.72rem;padding:3px 10px;border-radius:20px;">
            {count} IN STOCK
          </span>
        </div>
      </div>

      <!-- Cars -->
      <div style="padding:1.5rem;">
        <div style="color:#555;font-size:.68rem;letter-spacing:2px;
                    text-transform:uppercase;margin-bottom:.8rem;">Cars Available Right Now</div>
        <table style="width:100%;border-collapse:collapse;background:#141414;border-radius:10px;overflow:hidden;">
          {product_rows_html}
        </table>
      </div>

      <!-- CTA -->
      <div style="padding:0 1.5rem 2rem;text-align:center;">
        <a href="{p['link']}"
           style="display:inline-block;background:#FFD700;color:#000;font-weight:700;
                  padding:14px 40px;border-radius:8px;text-decoration:none;
                  letter-spacing:2px;font-size:1rem;width:80%;box-sizing:border-box;">
          🛒 ORDER NOW ON {p['name'].upper()}
        </a>
        <div style="color:#222;font-size:.7rem;margin-top:1.5rem;">
          HotWheels Tracker · Built by Akash Injeti · Runs 24/7
        </div>
      </div>
    </div>"""

    subject = f"🚗 {count} Hot Wheels on {p['name']}! — {car_names[:50]}{'...' if len(car_names)>50 else ''}"
    send_email(subject, email_html)
    print(f"  ✅ Email alert sent for {p['name']}!")

# ─── PLATFORM CHECKERS ─────────────────────────────────────────

def extract_names_from_html(html):
    import re
    names = []
    p1 = re.findall(r'"(?:name|title|product_name|display_name)"\s*:\s*"([^"]*[Hh]ot [Ww]heels[^"]{0,60})"', html)
    names.extend(p1)
    p2 = re.findall(r'>([^<]*[Hh]ot [Ww]heels[^<]{3,60})<', html)
    names.extend([n.strip() for n in p2])
    seen, clean = set(), []
    for n in names:
        n = n.strip()
        if n not in seen and 8 < len(n) < 100:
            seen.add(n)
            clean.append(n)
    return clean[:8]

def extract_names_from_html(html):
    import re as _re
    names = []
    p1 = _re.findall(r'"(?:name|title|display_name)"\s*:\s*"([^"]*[Hh]ot [Ww]heels[^"]{0,60})"', html)
    names.extend(p1)
    p2 = _re.findall(r'>([^<]*[Hh]ot [Ww]heels[^<]{3,60})<', html)
    names.extend([n.strip() for n in p2])
    seen, clean = set(), []
    for n in names:
        n = n.strip()
        if n not in seen and 8 < len(n) < 100:
            seen.add(n)
            clean.append(n)
    return clean[:8]

def check_blinkit():
    products = []
    try:
        r = requests.get(
            "https://blinkit.com/v2/search/",
            params={"q":"hot wheels","page_no":1,"page_size":20},
            headers={**HEADERS,"app_version":"3.0","auth_key":"2a9ef3e3db36bed41e357a8fe83e1fe1","lat":LAT,"lon":LON},
            timeout=15)
        if r.status_code == 200:
            for obj in r.json().get("objects",[]):
                for item in obj.get("items",[]):
                    name = item.get("name","") or item.get("title","")
                    if "hot wheel" in name.lower():
                        products.append({"name":name,"price":"Rs."+str(item.get("price",item.get("mrp","?"))),"in_stock":item.get("in_stock",item.get("available",False))})
    except: pass
    if not products:
        try:
            r = requests.get("https://blinkit.com/s/?q=hot+wheels",headers=HEADERS,timeout=15)
            txt = r.text
            if "hot wheel" in txt.lower():
                oos = any(x in txt.lower() for x in ["out of stock","notify me","sold out"])
                for n in (extract_names_from_html(txt) or ["Hot Wheels (check Blinkit)"]):
                    products.append({"name":n,"price":"Check app","in_stock":not oos})
        except: pass
    return products

def check_zepto():
    products = []
    try:
        r = requests.get(
            "https://api.zeptonow.com/api/v3/search/",
            params={"query":"hot wheels","page_number":0,"page_size":20,"pincode":PINCODE},
            headers={**HEADERS,"store_id":"1","requestid":"tracker","appversion":"11.0.0"},
            timeout=15)
        if r.status_code == 200:
            for section in r.json().get("data",{}).get("sections",[]):
                for item in section.get("items",[]):
                    name = item.get("name","") or item.get("product",{}).get("name","") or item.get("display_name","")
                    if "hot wheel" in name.lower():
                        price = item.get("discounted_price") or item.get("mrp") or "?"
                        products.append({"name":name,"price":"Rs."+str(price),"in_stock":not item.get("is_out_of_stock",True)})
    except: pass
    if not products:
        try:
            r = requests.get("https://www.zeptonow.com/search?query=hot+wheels",headers=HEADERS,timeout=15)
            txt = r.text
            if "hot wheel" in txt.lower():
                oos = any(x in txt.lower() for x in ["out of stock","notify me","sold out"])
                for n in (extract_names_from_html(txt) or ["Hot Wheels (check Zepto)"]):
                    products.append({"name":n,"price":"Check app","in_stock":not oos})
        except: pass
    return products

def check_swiggy():
    products = []
    try:
        r = requests.get(
            "https://www.swiggy.com/api/instamart/search",
            params={"query":"hot wheels","pageNumber":0,"pageSize":20,"lat":LAT,"lng":LON},
            headers={**HEADERS,"Referer":"https://www.swiggy.com/"},
            timeout=15)
        if r.status_code == 200:
            data = r.json().get("data",{})
            items = data.get("products",[]) or data.get("items",[])
            for item in items:
                name = item.get("display_name","") or item.get("name","")
                if "hot wheel" in name.lower():
                    products.append({"name":name,"price":"Rs."+str(item.get("price",item.get("mrp","?"))),"in_stock":item.get("inStock",item.get("available",False))})
    except: pass
    if not products:
        try:
            r = requests.get("https://www.swiggy.com/instamart/search?query=hot+wheels",headers=HEADERS,timeout=15)
            txt = r.text
            if "hot wheel" in txt.lower():
                oos = any(x in txt.lower() for x in ["out of stock","notify me","sold out"])
                for n in (extract_names_from_html(txt) or ["Hot Wheels (check Swiggy)"]):
                    products.append({"name":n,"price":"Check app","in_stock":not oos})
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

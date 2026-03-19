import streamlit as st
import requests
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="🚗 HotWheels Tracker",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CONSTANTS ─────────────────────────────────────────────────
TELEGRAM_CHAT_ID = "1695508762"
PINCODE          = "500081"
LAT, LON         = "17.4065", "78.4772"   # Hyderabad coords for pincode 500081

PLATFORMS = {
    "blinkit": {
        "name":  "Blinkit",
        "emoji": "🟡",
        "color": "#F0C000",
        "link":  "https://blinkit.com/s/?q=hot+wheels",
    },
    "zepto": {
        "name":  "Zepto",
        "emoji": "🟣",
        "color": "#8B5CF6",
        "link":  "https://www.zeptonow.com/search?query=hot+wheels",
    },
    "swiggy": {
        "name":  "Swiggy Instamart",
        "emoji": "🟠",
        "color": "#FC8019",
        "link":  "https://www.swiggy.com/instamart/search?query=hot+wheels",
    },
}

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-IN,en;q=0.9",
}

# ─── STYLES ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@700&display=swap');

:root{--red:#E8001C;--yellow:#FFD700;--bg:#0a0a0a;--s1:#141414;--border:#222;--text:#F0F0F0;--dim:#555;--green:#00C896;}
html,body,[class*="css"],.stApp,div[data-testid="stAppViewContainer"],.main,.appview-container{background:#0a0a0a!important;}
*{font-family:'DM Sans',sans-serif;color:var(--text);}
#MainMenu,footer,header{visibility:hidden!important;}
.block-container{padding:1.5rem 2.5rem 3rem!important;max-width:1200px!important;}

/* HEADER */
.hw-header{text-align:center;padding:2rem 0 1.5rem;border-bottom:1px solid var(--border);margin-bottom:2rem;}
.hw-logo{font-family:'Bebas Neue',sans-serif;font-size:3.5rem;letter-spacing:6px;line-height:1;}
.hw-logo .hot{color:#E8001C;}.hw-logo .wheels{color:#FFD700;}

/* PLATFORM CARD */
.platform-card{background:var(--s1);border-radius:16px;padding:1.5rem;border:2px solid var(--border);transition:all .2s;}
.platform-card.instock{border-color:var(--green);background:rgba(0,200,150,.05);}
.platform-card.outofstock{border-color:#1a1a1a;}
.platform-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;}
.platform-name{font-family:'Bebas Neue',sans-serif;font-size:1.3rem;letter-spacing:3px;}
.platform-badge{font-size:.65rem;font-weight:700;padding:3px 10px;border-radius:20px;letter-spacing:1px;}
.badge-instock{background:rgba(0,200,150,.15);color:var(--green);}
.badge-outofstock{background:rgba(255,255,255,.05);color:var(--dim);}
.badge-checking{background:rgba(255,215,0,.1);color:#FFD700;}
.platform-time{font-size:.68rem;color:var(--dim);letter-spacing:1px;margin-top:.3rem;}

/* PRODUCT ROW */
.product-row{display:flex;align-items:center;justify-content:space-between;padding:.5rem .8rem;background:#0f0f0f;border-radius:8px;margin-bottom:.4rem;font-size:.8rem;}
.product-row-name{flex:1;color:var(--text);font-weight:500;}
.product-row-price{font-family:'JetBrains Mono',monospace;font-weight:700;margin:0 .8rem;}
.product-row-status{font-size:.65rem;padding:2px 8px;border-radius:20px;font-weight:600;}
.row-instock{background:rgba(0,200,150,.12);color:var(--green);}
.row-oos{background:rgba(255,255,255,.05);color:var(--dim);}

/* OVERALL STATUS */
.overall-status{border-radius:16px;padding:1.5rem 2rem;text-align:center;margin-bottom:1.5rem;border:2px solid;}
.overall-status.any-instock{background:rgba(0,200,150,.08);border-color:var(--green);}
.overall-status.all-oos{background:rgba(232,0,28,.03);border-color:#1a1a1a;}
.status-big{font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:4px;}

/* METRICS */
.metric-row{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin:1.5rem 0;}
.metric{background:var(--s1);border:1px solid var(--border);border-radius:12px;padding:1rem;text-align:center;}
.metric-val{font-family:'Bebas Neue',sans-serif;font-size:1.8rem;letter-spacing:2px;}
.metric-lbl{font-size:.6rem;color:var(--dim);letter-spacing:2px;text-transform:uppercase;margin-top:2px;}
.y{color:#FFD700;} .g{color:var(--green);} .r{color:var(--red);} .p{color:#8B5CF6;}

/* LOG */
.log-row{display:flex;justify-content:space-between;align-items:center;padding:.5rem .8rem;border-bottom:1px solid #1a1a1a;font-size:.75rem;}
.log-row:last-child{border-bottom:none;}
.log-time{color:var(--dim);font-family:'JetBrains Mono',monospace;font-size:.68rem;}
.log-found{color:var(--green);font-weight:700;}
.log-empty{color:var(--dim);}
.log-platform{font-size:.65rem;padding:1px 6px;border-radius:10px;margin-left:.4rem;}

/* BUTTONS */
.stButton>button{background:#FFD700!important;color:#000!important;font-weight:700!important;border:none!important;border-radius:8px!important;letter-spacing:1px!important;white-space:nowrap!important;}
.stButton>button p{color:#000!important;}
.stButton>button:hover{opacity:.85!important;}

/* LIVE BADGE */
.live-badge{display:inline-flex;align-items:center;gap:.4rem;background:rgba(232,0,28,.1);border:1px solid rgba(232,0,28,.3);color:#FF4560;font-size:.72rem;padding:4px 12px;border-radius:20px;letter-spacing:1px;font-weight:600;}
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ──────────────────────────────────────────────
for k,v in [
    ("tracking", False),
    ("check_count", 0),
    ("found_count", 0),
    ("last_check_time", None),
    ("log", []),
    ("alert_sent_blinkit", False),
    ("alert_sent_zepto", False),
    ("alert_sent_swiggy", False),
    ("results", {
        "blinkit": {"status": "unknown", "products": [], "last_check": None},
        "zepto":   {"status": "unknown", "products": [], "last_check": None},
        "swiggy":  {"status": "unknown", "products": [], "last_check": None},
    }),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─── ALERT HELPERS ─────────────────────────────────────────────
def send_telegram(token, message):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message,
                  "parse_mode": "HTML", "disable_web_page_preview": False},
            timeout=10
        )
        return r.status_code == 200
    except: return False

def send_email(smtp_email, smtp_pass, subject, body_html):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"HotWheels Tracker 🚗 <{smtp_email}>"
        msg["To"]      = smtp_email
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(smtp_email, smtp_pass)
            s.sendmail(smtp_email, smtp_email, msg.as_string())
        return True
    except: return False

def fire_alerts(platform_key, products, token, smtp_email, smtp_pass):
    p    = PLATFORMS[platform_key]
    now  = datetime.now().strftime("%H:%M:%S")
    lines= "\n".join([f"• {x['name']} — {x['price']}" for x in products])
    link = p["link"]

    tg = f"""{p['emoji']} <b>HOT WHEELS ON {p['name'].upper()}!</b> 🔥

📍 Pincode: {PINCODE} · Hyderabad
⏰ {now}

<b>In Stock:</b>
{lines}

🛒 <a href="{link}">Order Now on {p['name']}</a>

<i>Hurry — they sell out fast! 🚗</i>"""
    send_telegram(token, tg)

    email_html = f"""
    <div style="font-family:Arial;background:#0a0a0a;color:#F0F0F0;padding:2rem;max-width:500px;border-radius:12px;">
      <h1 style="color:#FFD700;letter-spacing:4px;">🚗 HOTWHEELS ALERT!</h1>
      <h2 style="color:#00C896;">In Stock on {p['name']}!</h2>
      <p style="color:#888;">Detected at <b style="color:#fff;">{now}</b> · Pincode <b style="color:#fff;">{PINCODE}</b></p>
      <div style="background:#141414;border-radius:8px;padding:1rem;margin:1rem 0;">
        {"".join([f'<div style="padding:.4rem 0;border-bottom:1px solid #222;"><b style="color:#FFD700;">{x["name"]}</b> — <span style="color:#00C896;">{x["price"]}</span></div>' for x in products])}
      </div>
      <a href="{link}" style="display:inline-block;background:#FFD700;color:#000;font-weight:700;padding:12px 28px;border-radius:8px;text-decoration:none;margin-top:1rem;">🛒 ORDER NOW ON {p['name'].upper()}</a>
      <p style="color:#333;font-size:.75rem;margin-top:1.5rem;">HotWheels Tracker · Built by Akash Injeti</p>
    </div>"""
    send_email(smtp_email, smtp_pass, f"🚗 Hot Wheels on {p['name']}! ({PINCODE})", email_html)

# ─── PLATFORM CHECKERS ─────────────────────────────────────────
def check_blinkit():
    products = []
    try:
        # API attempt
        r = requests.get(
            "https://blinkit.com/v2/search/",
            params={"q": "hot wheels", "page_no": 1, "page_size": 20},
            headers={**COMMON_HEADERS,
                     "app_version": "3.0",
                     "auth_key": "2a9ef3e3db36bed41e357a8fe83e1fe1",
                     "lat": LAT, "lon": LON},
            timeout=12
        )
        if r.status_code == 200:
            data = r.json()
            for obj in data.get("objects", []):
                for item in obj.get("items", []):
                    name = item.get("name","") or item.get("title","")
                    if "hot wheel" in name.lower() or "hotwheels" in name.lower():
                        products.append({
                            "name": name,
                            "price": f"₹{item.get('price', item.get('mrp','?'))}",
                            "in_stock": item.get("in_stock", item.get("available", False))
                        })
    except: pass

    # Fallback: page scrape
    if not products:
        try:
            r = requests.get("https://blinkit.com/s/?q=hot+wheels",
                             headers=COMMON_HEADERS, timeout=12)
            txt = r.text.lower()
            if "hot wheel" in txt or "hotwheels" in txt:
                oos = any(x in txt for x in ["out of stock","notify me","sold out","currently unavailable"])
                products.append({"name":"Hot Wheels (Blinkit page)","price":"—","in_stock": not oos})
        except: pass

    return products

def check_zepto():
    products = []
    try:
        r = requests.get(
            "https://api.zeptonow.com/api/v3/search/",
            params={"query": "hot wheels", "page_number": 0, "page_size": 20,
                    "pincode": PINCODE},
            headers={**COMMON_HEADERS,
                     "store_id": "1",
                     "requestid": "tracker",
                     "appversion": "11.0.0"},
            timeout=12
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get("data", {}).get("sections", [])
            for section in items:
                for item in section.get("items", []):
                    name = item.get("name","") or item.get("product",{}).get("name","")
                    if "hot wheel" in name.lower() or "hotwheels" in name.lower():
                        products.append({
                            "name": name,
                            "price": f"₹{item.get('discounted_price', item.get('mrp','?'))}",
                            "in_stock": not item.get("is_out_of_stock", True)
                        })
    except: pass

    # Fallback scrape
    if not products:
        try:
            r = requests.get(
                "https://www.zeptonow.com/search?query=hot+wheels",
                headers=COMMON_HEADERS, timeout=12
            )
            txt = r.text.lower()
            if "hot wheel" in txt or "hotwheels" in txt:
                oos = any(x in txt for x in ["out of stock","notify me","sold out"])
                products.append({"name":"Hot Wheels (Zepto page)","price":"—","in_stock": not oos})
        except: pass

    return products

def check_swiggy():
    products = []
    try:
        r = requests.get(
            "https://www.swiggy.com/api/instamart/search",
            params={"query": "hot wheels", "pageNumber": 0, "pageSize": 20,
                    "lat": LAT, "lng": LON},
            headers={**COMMON_HEADERS,
                     "Referer": "https://www.swiggy.com/",
                     "_csrf": "csrf"},
            timeout=12
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get("data", {}).get("products", [])
            for item in items:
                name = item.get("display_name","") or item.get("name","")
                if "hot wheel" in name.lower() or "hotwheels" in name.lower():
                    products.append({
                        "name": name,
                        "price": f"₹{item.get('price','?')}",
                        "in_stock": item.get("inStock", item.get("available", False))
                    })
    except: pass

    # Fallback scrape
    if not products:
        try:
            r = requests.get(
                "https://www.swiggy.com/instamart/search?query=hot+wheels",
                headers=COMMON_HEADERS, timeout=12
            )
            txt = r.text.lower()
            if "hot wheel" in txt or "hotwheels" in txt:
                oos = any(x in txt for x in ["out of stock","notify me","sold out"])
                products.append({"name":"Hot Wheels (Swiggy page)","price":"—","in_stock": not oos})
        except: pass

    return products

# ─── MAIN CHECK FUNCTION ───────────────────────────────────────
def run_check(token, smtp_email, smtp_pass):
    now = datetime.now().strftime("%H:%M:%S")
    st.session_state.check_count += 1
    st.session_state.last_check_time = datetime.now().strftime("%d %b %Y, %H:%M:%S")

    checkers = {
        "blinkit": check_blinkit,
        "zepto":   check_zepto,
        "swiggy":  check_swiggy,
    }

    any_found = False

    for key, fn in checkers.items():
        try:
            products = fn()
            in_stock  = [p for p in products if p.get("in_stock")]
            new_status = "instock" if in_stock else "outofstock"

            # Get PREVIOUS status before updating
            prev_status = st.session_state.results.get(key, {}).get("status", "outofstock")

            # Update results
            st.session_state.results[key] = {
                "status":     new_status,
                "products":   products,
                "last_check": now,
            }

            # ── ONLY alert on OUT → IN transition (new restock!) ──
            just_restocked = (prev_status == "outofstock" and new_status == "instock")

            if in_stock:
                any_found = True
                if just_restocked:
                    # NEW restock detected — fire alert!
                    st.session_state.found_count += 1
                    fire_alerts(key, in_stock, token, smtp_email, smtp_pass)
                    st.session_state.log.insert(0, {
                        "time": now, "platform": key,
                        "status": "found",
                        "label": f"🔥 RESTOCK! {len(in_stock)} item(s) on {PLATFORMS[key]['name']}"
                    })
                else:
                    # Still in stock from before — no alert
                    st.session_state.log.insert(0, {
                        "time": now, "platform": key,
                        "status": "found",
                        "label": f"Still in stock on {PLATFORMS[key]['name']}"
                    })
            else:
                if prev_status == "instock":
                    # Just went OUT of stock
                    st.session_state.log.insert(0, {
                        "time": now, "platform": key,
                        "status": "empty",
                        "label": f"Went out of stock on {PLATFORMS[key]['name']}"
                    })
                else:
                    # Still out of stock — silent log
                    st.session_state.log.insert(0, {
                        "time": now, "platform": key,
                        "status": "empty",
                        "label": f"Out of stock on {PLATFORMS[key]['name']}"
                    })

        except Exception as e:
            st.session_state.log.insert(0, {
                "time": now, "platform": key,
                "status": "empty",
                "label": f"Error ({key}): {str(e)[:30]}"
            })

    st.session_state.log = st.session_state.log[:60]
    return any_found

# ─── UI ────────────────────────────────────────────────────────
# Header
st.markdown("""
<div class="hw-header">
  <div class="hw-logo"><span class="hot">HOT</span><span class="wheels">WHEELS</span></div>
  <div style="font-family:'Bebas Neue',sans-serif;font-size:1.1rem;letter-spacing:4px;color:#555;">
    MULTI-PLATFORM RESTOCK TRACKER
  </div>
  <div style="font-size:.75rem;color:#444;letter-spacing:2px;margin-top:.3rem;">
    📍 PINCODE 500081 · HYDERABAD &nbsp;·&nbsp; BLINKIT · ZEPTO · SWIGGY INSTAMART
  </div>
</div>""", unsafe_allow_html=True)

# Secrets
tg_token   = st.secrets.get("TELEGRAM_BOT_TOKEN","")
smtp_email = st.secrets.get("SMTP_EMAIL","")
smtp_pass  = st.secrets.get("SMTP_PASSWORD","")

if not tg_token:
    st.warning("⚠️ Add TELEGRAM_BOT_TOKEN to Streamlit secrets")

# ── OVERALL STATUS ──
results   = st.session_state.results
any_stock = any(v["status"] == "instock" for v in results.values())
checked   = any(v["status"] != "unknown" for v in results.values())

if any_stock:
    platforms_with_stock = [PLATFORMS[k]["name"] for k,v in results.items() if v["status"]=="instock"]
    st.markdown(f"""
    <div class="overall-status any-instock">
      <div style="font-size:2rem;">🚗🔥</div>
      <div class="status-big" style="color:var(--green);">IN STOCK!</div>
      <div style="color:#00C896;font-size:.85rem;margin-top:.3rem;">Found on: {' · '.join(platforms_with_stock)}</div>
    </div>""", unsafe_allow_html=True)
elif checked:
    st.markdown(f"""
    <div class="overall-status all-oos">
      <div style="font-size:2rem;">🔴</div>
      <div class="status-big" style="color:#333;">OUT OF STOCK</div>
      <div style="color:#444;font-size:.8rem;margin-top:.3rem;">Checked all 3 platforms · Last: {st.session_state.last_check_time}</div>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="overall-status all-oos">
      <div style="font-size:2rem;">⏳</div>
      <div class="status-big" style="color:#333;">NOT STARTED</div>
      <div style="color:#444;font-size:.8rem;margin-top:.3rem;">Press Start Tracking or Check Now</div>
    </div>""", unsafe_allow_html=True)

# ── METRICS ──
found_count = sum(1 for v in results.values() if v["status"]=="instock")
st.markdown(f"""
<div class="metric-row">
  <div class="metric"><div class="metric-val y">{st.session_state.check_count}</div><div class="metric-lbl">Total Checks</div></div>
  <div class="metric"><div class="metric-val g">{st.session_state.found_count}</div><div class="metric-lbl">Times Found</div></div>
  <div class="metric"><div class="metric-val p">{found_count}/3</div><div class="metric-lbl">Platforms Live</div></div>
  <div class="metric"><div class="metric-val r">3</div><div class="metric-lbl">Platforms Tracked</div></div>
</div>""", unsafe_allow_html=True)

# ── CONTROLS ──
c1,c2,c3,c4 = st.columns([2,1,1,1])
with c1:
    interval = st.selectbox("Check every", [2,5,10,15,30], index=1, key="interval", label_visibility="collapsed")
    st.caption(f"⏱️ Check interval: every {interval} min")
with c2:
    if not st.session_state.tracking:
        if st.button("▶️ START", use_container_width=True):
            st.session_state.tracking = True; st.rerun()
    else:
        if st.button("⏹️ STOP", use_container_width=True):
            st.session_state.tracking = False; st.rerun()
with c3:
    if st.button("🔍 CHECK NOW", use_container_width=True):
        with st.spinner("Checking all 3 platforms..."):
            run_check(tg_token, smtp_email, smtp_pass)
        st.rerun()
with c4:
    if st.button("🗑️ RESET", use_container_width=True):
        for k in ["check_count","found_count","log","alert_sent_blinkit","alert_sent_zepto","alert_sent_swiggy"]:
            st.session_state[k] = [] if k=="log" else False if "alert" in k else 0
        st.session_state.results = {k:{"status":"unknown","products":[],"last_check":None} for k in PLATFORMS}
        st.rerun()

# ── LIVE TRACKING BADGE ──
if st.session_state.tracking:
    st.markdown(f'<div style="text-align:center;margin:.5rem 0;"><span class="live-badge">🔴 LIVE — Blinkit + Zepto + Swiggy · Every {interval} min · Alerts ON</span></div>', unsafe_allow_html=True)

# ── 3 PLATFORM CARDS ──
st.markdown("<br>", unsafe_allow_html=True)
cols = st.columns(3)
for i, (key, pinfo) in enumerate(PLATFORMS.items()):
    with cols[i]:
        res     = results[key]
        status  = res["status"]
        prods   = res["products"]
        in_stk  = [p for p in prods if p.get("in_stock")]
        last_t  = res.get("last_check") or "—"
        card_cls= "instock" if status=="instock" else "outofstock"
        b_cls   = "badge-instock" if status=="instock" else ("badge-checking" if status=="unknown" else "badge-outofstock")
        b_txt   = "IN STOCK ✅" if status=="instock" else ("CHECKING..." if status=="unknown" else "OUT OF STOCK")

        st.markdown(f"""
        <div class="platform-card {card_cls}">
          <div class="platform-header">
            <div>
              <div class="platform-name" style="color:{pinfo['color']};">{pinfo['emoji']} {pinfo['name']}</div>
              <div class="platform-time">Last: {last_t}</div>
            </div>
            <span class="platform-badge {b_cls}">{b_txt}</span>
          </div>""", unsafe_allow_html=True)

        if prods:
            for p in prods[:4]:
                s_cls = "row-instock" if p.get("in_stock") else "row-oos"
                s_txt = "✅ Stock" if p.get("in_stock") else "❌ OOS"
                st.markdown(f"""
                <div class="product-row">
                  <span class="product-row-name">🚗 {p['name'][:28]}{'...' if len(p['name'])>28 else ''}</span>
                  <span class="product-row-price" style="color:{pinfo['color']};">{p['price']}</span>
                  <span class="product-row-status {s_cls}">{s_txt}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align:center;padding:1rem;color:#333;font-size:.8rem;">No data yet — hit Check Now</div>', unsafe_allow_html=True)

        st.markdown(f'<div style="margin-top:.8rem;"><a href="{pinfo["link"]}" target="_blank" style="color:{pinfo["color"]};font-size:.72rem;letter-spacing:1px;text-decoration:none;">🛒 Open {pinfo["name"]} →</a></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── TRACKING LOOP ──
if st.session_state.tracking:
    with st.spinner(f"Checking all platforms... next in {interval} min"):
        run_check(tg_token, smtp_email, smtp_pass)
        time.sleep(interval * 60)
    st.rerun()

# ── CHECK LOG ──
if st.session_state.log:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Bebas Neue\',sans-serif;font-size:1rem;letter-spacing:2px;color:#555;margin-bottom:.6rem;">📋 CHECK LOG</div>', unsafe_allow_html=True)
    st.markdown('<div style="background:#141414;border:1px solid #222;border-radius:12px;overflow:hidden;">', unsafe_allow_html=True)
    for entry in st.session_state.log[:30]:
        cls  = "log-found" if entry["status"]=="found" else "log-empty"
        icon = "🟢" if entry["status"]=="found" else "🔴"
        pkey = entry.get("platform","")
        pcolor = PLATFORMS.get(pkey,{}).get("color","#555")
        pemoji = PLATFORMS.get(pkey,{}).get("emoji","")
        st.markdown(f"""
        <div class="log-row">
          <span class="log-time">{entry['time']}</span>
          <span style="font-size:.7rem;color:{pcolor};">{pemoji} {PLATFORMS.get(pkey,{}).get('name','')}</span>
          <span class="{cls}">{icon} {entry['label']}</span>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# FOOTER
st.markdown("""
<div style="text-align:center;margin:2.5rem 0 1rem;color:#333;font-size:.7rem;letter-spacing:1px;">
  🚗 HotWheels Tracker &nbsp;·&nbsp; Built by <b style="color:#555;">Akash Injeti</b>
  &nbsp;·&nbsp; Blinkit · Zepto · Swiggy Instamart
</div>""", unsafe_allow_html=True)

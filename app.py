import html
import json
import re
from datetime import date, timedelta

import requests
import streamlit as st
from supabase import create_client

import agreements as ag
import calendar_view as cal
from lang_data import DAYS, LANGS

APP_NAME = "AI Voice Contract"
TAGLINE = "Record voice contracts for anything and keep a clear record."
TAGLINE_HI = "बोलिए · रिकॉर्ड कीजिए · वादा पक्का"

try:
    API_KEY = st.secrets["GNANI_API_KEY"]
except Exception:
    API_KEY = ""  # no secrets file = mock mode (no API call, no credits used)

KEYTERMS = []  # optional, e.g. ["शर्मा", "Sharma"]; leave empty unless you tested it

SCENARIOS = {
    "Electrician / plumber": dict(
        icon=":material/build:", amount=True,
        msg="{name}, job quote ₹{amt}, to be completed by {due}",
        example="Sharma ji ke ghar ki wiring ka kaam, 3000 rupaye, agle budhvar tak poora karenge."),
    "Shopkeeper credit": dict(
        icon=":material/storefront:", amount=True,
        msg="{name}, ₹{amt} on credit, due {due}",
        example="Sharma ji ko 2 kilo atta diya, 500 rupaye udhaar, agle somvar tak denge."),
    "Friend or family loan": dict(
        icon=":material/handshake:", amount=True,
        msg="{name}, loan of ₹{amt}, to be returned by {due}",
        example="Sharma ji ko 2000 rupaye diye, agle shukravar tak lauta denge."),
    "Rent / deposit": dict(
        icon=":material/home:", amount=True,
        msg="{name}, ₹{amt} rent or deposit, due {due}",
        example="Sharma ji ka kiraya 8000 rupaye, agle somvar tak denge."),
    "Freelance work": dict(
        icon=":material/work:", amount=True,
        msg="{name}, ₹{amt} for the agreed work, payment by {due}",
        example="Sharma ji ka logo ka kaam, 3000 rupaye, agle budhvar tak denge."),
    "Borrowed item": dict(
        icon=":material/inventory_2:", amount=False,
        msg="{name}, borrowed item to be returned by {due}",
        example="Sharma ji ne meri drill machine li, agle shanivar tak lautayenge."),
}

MOCK_TRANSCRIBE = "शर्मा जी को 2 किलो आटा दिया है, 500 उधार अगले सोमवार तक देंगे।"
MOCK_VERBATIM = "शर्मा जी को दो किलो आटा दिया है, पाँच सौ उधार अगले सोमवार तक देंगे।"

# ---- inline line icons (Lucide-style SVG) ----
_PATHS = {
    "mic": '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "rupee": '<path d="M6 3h12"/><path d="M6 8h12"/><path d="m6 13 8.5 8"/><path d="M6 13h3"/><path d="M9 13c6.667 0 6.667-10 0-10"/>',
    "calendar": '<rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/>',
    "file": '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/>',
    "message": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "phone": '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
}


def icon(name, size=18, color="currentColor"):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:middle;margin-right:6px">{_PATHS[name]}</svg>'
    )


IC_MIC = icon("mic", 34, "#fff")
IC_USER = icon("user", 16)
IC_RUPEE = icon("rupee", 16)
IC_CAL = icon("calendar", 16)
IC_FILE = icon("file", 19, "#9A3412")
IC_MSG = icon("message", 19, "#9A3412")
IC_PHONE = icon("phone", 14)
IC_CHECK = icon("check", 14, "#fff")
IC_YES = icon("check", 14, "#16A34A")
IC_OK = icon("check-circle", 22, "#4D7C0F")

FOOT = (
    '<div class="foot">Reference record only, not legal advice. '
    "Message send, confirmation and reminders are simulated in this demo.</div>"
)

st.set_page_config(page_title=APP_NAME, page_icon=":material/mic:", layout="centered")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700&family=Mukta:wght@400;600;700&display=swap');
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.4rem; max-width: 900px;}
.hero, .card, .stp, .phone, .calok, .foot {font-family: 'Mukta', sans-serif;}
.hero {
  background: radial-gradient(rgba(255,255,255,.20) 1.6px, transparent 1.7px) 0 0/18px 18px,
              linear-gradient(135deg,#9A3412,#EA580C 55%,#F59E0B);
  color:#fff; padding:30px 32px; border-radius:24px; margin-bottom:16px;
  box-shadow:0 8px 26px rgba(154,52,18,.25);}
.hero h1 {margin:0; font-family:'Baloo 2','Mukta',sans-serif; font-size:2.4rem; color:#fff; letter-spacing:-.3px;}
.hero .hi {font-size:1.15rem; font-weight:700; margin-top:2px; color:#FFF3D6;}
.hero p {margin:6px 0 0; opacity:.95; font-size:1.05rem;}
.badge {display:inline-block; background:rgba(255,255,255,.22); padding:4px 12px;
        border-radius:999px; font-size:.78rem; margin:12px 6px 0 0;}
.stp {display:flex; gap:10px; margin:6px 0 14px;}
.stp-i {flex:1; display:flex; align-items:center; justify-content:center; gap:8px; padding:10px 6px;
        border-radius:14px; background:#F6E6CC; color:#8A6A4B; font-weight:700; font-size:.92rem;}
.stp-i span {width:24px; height:24px; border-radius:50%; background:#D9BF9B; color:#fff;
             display:flex; align-items:center; justify-content:center; font-size:.8rem;}
.stp-i span svg {margin:0 !important;}
.stp-i.done {background:#E3EBC8; color:#4D7C0F;} .stp-i.done span {background:#65A30D;}
.stp-i.now {background:#FFE0B8; color:#B45309;} .stp-i.now span {background:#EA580C;}
.card {border-radius:20px; padding:20px 22px; border:1px solid #F0DDC2; background:#FFFDF8;
       color:#3B2A1E; box-shadow:0 4px 16px rgba(180,83,9,.10); min-height:200px;}
.card h4 {margin:0 0 12px; font-family:'Baloo 2','Mukta',sans-serif; font-size:1.08rem; color:#7C2D12;}
.pill {display:inline-block; background:#FFE0B8; color:#9A3412; padding:2px 10px;
       border-radius:999px; font-size:.72rem; font-weight:700; margin-left:8px; vertical-align:middle;}
.row {display:flex; justify-content:space-between; padding:9px 0; border-bottom:1px dashed #EBD5B3;}
.row:last-of-type {border-bottom:none;}
.row span {color:#8A6A4B;} .row b {color:#3B2A1E;}
.quote {border-left:5px solid #EA580C; padding:10px 14px; color:#5A3A22; font-style:italic;
        line-height:1.7; background:#FFF1DA; border-radius:0 12px 12px 0; font-family:'Mukta',sans-serif;}
.small {color:#8A6A4B; font-size:.82rem; margin-top:12px;}
.phone {background:#ECE5DD; border-radius:22px; padding:16px; max-width:420px; margin:8px 0 12px;
        border:1px solid #E0D3C2;}
.phone .top {color:#7A6A58; font-size:.75rem; margin-bottom:10px;}
.bubble {background:#DCF8C6; color:#2B2B2B; padding:10px 13px; border-radius:12px 12px 2px 12px;
         font-size:.93rem; line-height:1.5; margin-left:auto; max-width:92%; box-shadow:0 1px 1px rgba(0,0,0,.1);}
.reply {background:#fff; color:#2B2B2B; padding:8px 14px; border-radius:12px 12px 12px 2px;
        font-size:.93rem; margin-top:8px; width:fit-content; box-shadow:0 1px 1px rgba(0,0,0,.1);}
.calok {display:flex; gap:16px; align-items:center; background:#F3F7E4; border:1px solid #D4E3A6;
        border-radius:20px; padding:16px 20px; color:#3F5D0C;}
.cal-date {background:#fff; border-radius:12px; padding:8px 16px; text-align:center;
           border:1px solid #D4E3A6; line-height:1.15;}
.cal-date span {display:block; font-size:.75rem; color:#C2410C; font-weight:700;}
.cal-date b {font-size:1.7rem; color:#3B2A1E;}
.foot {text-align:center; color:#A68B6B; font-size:.78rem; margin-top:28px;}
</style>
""",
    unsafe_allow_html=True,
)


def _supabase_config():
    try:
        settings = st.secrets["supabase"]
        url = settings["url"].strip()
        anon_key = settings["anon_key"].strip()
    except (KeyError, FileNotFoundError):
        return None
    if not url or not anon_key:
        return None
    return url, anon_key


supabase_config = _supabase_config()
if not supabase_config:
    st.error(
        "Supabase is not configured. Create a Supabase project, run "
        "`supabase/schema.sql` in its SQL Editor, then add the project URL "
        "and anon key under `[supabase]` in `.streamlit/secrets.toml`. "
        "See `SUPABASE_SETUP.md`."
    )
    st.stop()

if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(*supabase_config)
supabase = st.session_state.supabase


def _account_name(user, email):
    metadata = getattr(user, "user_metadata", None) or {}
    return (
        metadata.get("full_name")
        or metadata.get("name")
        or email.partition("@")[0]
        or "there"
    )


def _set_auth_notice(kind, message):
    st.session_state.auth_notice = {"kind": kind, "message": message}


def _show_auth_notice():
    notice = st.session_state.pop("auth_notice", None)
    if notice:
        getattr(st, notice["kind"])(notice["message"])


if not st.session_state.get("user_id"):
    st.title("AI Voice Contract")
    st.write("Sign in to save and view your agreements.")
    _show_auth_notice()
    sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])

    with sign_in_tab:
        with st.form("sign_in_form"):
            email = st.text_input("Email", key="sign_in_email")
            password = st.text_input("Password", type="password", key="sign_in_password")
            sign_in = st.form_submit_button("Sign in", type="primary")
        if sign_in:
            try:
                result = supabase.auth.sign_in_with_password(
                    {"email": email.strip(), "password": password}
                )
                if not result.user:
                    st.error("Sign in did not return a user. Check the email and password.")
                else:
                    signed_in_email = result.user.email or email.strip()
                    st.session_state.user_id = str(result.user.id)
                    st.session_state.user_email = signed_in_email
                    st.session_state.user_name = _account_name(result.user, signed_in_email)
                    _set_auth_notice(
                        "success", f"Welcome back, {st.session_state.user_name}!"
                    )
                    st.rerun()
            except Exception as exc:
                st.error(f"Sign in failed: {exc}")

    with sign_up_tab:
        with st.form("sign_up_form"):
            display_name = st.text_input("Your name", key="sign_up_name")
            new_email = st.text_input("Email", key="sign_up_email")
            new_password = st.text_input(
                "Password (at least 8 characters)", type="password", key="sign_up_password"
            )
            confirm_password = st.text_input(
                "Confirm password", type="password", key="sign_up_confirm_password"
            )
            sign_up = st.form_submit_button("Create account", type="primary")
        if sign_up:
            if not display_name.strip():
                st.error("Enter your name to create an account.")
            elif not new_email.strip():
                st.error("Enter your email address.")
            elif len(new_password) < 8:
                st.error("Use a password with at least 8 characters.")
            elif new_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                try:
                    result = supabase.auth.sign_up(
                        {
                            "email": new_email.strip(),
                            "password": new_password,
                            "options": {"data": {"full_name": display_name.strip()}},
                        }
                    )
                    if result.session and result.user:
                        signed_up_email = result.user.email or new_email.strip()
                        st.session_state.user_id = str(result.user.id)
                        st.session_state.user_email = signed_up_email
                        st.session_state.user_name = _account_name(
                            result.user, signed_up_email
                        )
                        _set_auth_notice(
                            "success",
                            f"Account created. Welcome, {st.session_state.user_name}!",
                        )
                        st.rerun()
                    else:
                        _set_auth_notice(
                            "success",
                            "Account created. If email confirmation is enabled, "
                            "confirm your address before signing in.",
                        )
                        st.rerun()
                except Exception as exc:
                    st.error(f"Account creation failed: {exc}")
    st.stop()

with st.sidebar:
    st.markdown("### :material/account_circle: Your account")
    st.write(f"**{st.session_state.get('user_name', 'User')}**")
    st.caption(st.session_state.get("user_email", ""))
    if st.button("Sign out", icon=":material/logout:"):
        try:
            supabase.auth.sign_out()
        except Exception as exc:
            st.error(f"Sign out failed: {exc}")
        else:
            for key in (
                "user_id", "user_email", "user_name", "agreements", "agreements_user_id",
                "entries", "entries_user_id", "clip", "sent", "confirmed",
                "verbatim", "transcribe", "lang", "f_name", "f_amount", "f_due",
                "f_found", "cur_id",
            ):
                st.session_state.pop(key, None)
            st.session_state.mic_n = st.session_state.get("mic_n", 0) + 1
            _set_auth_notice("success", "You have been signed out.")
            st.rerun()


def esc(x):
    return html.escape(str(x))


def call(audio_bytes, fmt):
    form = {"model": "prisma-v3.0", "language_code": "indic-auto", "format": fmt}
    if KEYTERMS:
        form["keyterms"] = json.dumps(KEYTERMS, ensure_ascii=False)
    r = requests.post(
        "https://api.vachana.ai/stt/v3",
        headers={"X-API-Key-ID": API_KEY.strip()},
        files={"audio_file": ("audio.wav", audio_bytes, "audio/wav")},
        data=form,
        timeout=60,
    )
    r.raise_for_status()
    j = r.json()
    return j["transcript"], j.get("detected_language_code")


def extract_name(text):
    word = r"(?:[A-Za-z][A-Za-z'-]*|[\u0900-\u097F]+)"
    phrase = rf"{word}(?:\s+{word}){{0,1}}"
    cues = (
        rf"(?P<name>{phrase})\s+(?:ji|जी)(?=\s|[,.!?।]|$)",
        rf"(?P<name>{phrase})\s+(?:ke\s+ghar|के\s+घर|के\s+यहाँ|के\s+यहां)",
        rf"(?P<name>{phrase})\s+(?:ko|को|ने)(?=\s|[,.!?।]|$)",
    )
    for cue in cues:
        match = re.search(cue, text, re.IGNORECASE)
        if match:
            return match.group("name").strip()
    return None


def extract(text):
    t = text.lower()
    nums = [int(n) for n in re.findall(r"\d+", t)]
    name = extract_name(text)
    due, today = None, date.today()
    for idx, words in DAYS.items():
        if any(w in t for w in words):
            due = today + timedelta(days=(idx - today.weekday()) % 7 or 7)
            break
    return {"name": name, "amount": max(nums) if nums else None, "due": due}


def build_msg(scn, name, amt, due_txt):
    body = scn["msg"].format(name=name or "Customer", amt=amt, due=due_txt)
    return f"{APP_NAME}: {body}. Reply YES to confirm."


def do_send(kind, has_amount):
    s = st.session_state
    amt = int(s.f_amount) if has_amount else 0
    s.cur_id = ag.add(
        kind, (s.f_name or "").strip() or "Customer", amt, s.f_due, s.transcribe, s.verbatim, s.lang
    )
    s.sent = True


def do_confirm():
    s = st.session_state
    s.confirmed = True
    a = ag.confirm(s.cur_id)
    if a and a["due"]:
        cal.add_entry(a["party"], a["amount"], date.fromisoformat(a["due"]), 1)


def do_reset():
    s = st.session_state
    s.mic_n += 1
    s.clip = None


ag.init()
cal.init()
st.session_state.setdefault("mic_n", 0)

mode = "LIVE · Prisma v3.0" if API_KEY else "MOCK MODE · no API call"
_show_auth_notice()
user_name = st.session_state.get("user_name", "there")
st.markdown(
    f"""
<div class="hero">
  <h1>{IC_MIC}Welcome, {esc(user_name)}</h1>
  <div class="hi">{esc(TAGLINE_HI)}</div>
  <p>Your agreements, all in one place.</p>
  <span class="badge">Electricians &amp; plumbers</span><span class="badge">Shopkeepers</span><span class="badge">Friends &amp; family</span><span class="badge">Rent</span><span class="badge">Freelancers</span><br>
  <span class="badge">{mode}</span><span class="badge">10 Indian languages · auto-detected</span>
</div>
""",
    unsafe_allow_html=True,
)

agreements = st.session_state.agreements
with st.container(border=True):
    st.subheader("Your overview")
    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Agreements", len(agreements), help="All your saved agreements")
    metric_b.metric(
        "Awaiting confirmation",
        sum(item["status"] == "Pending" for item in agreements),
    )
    metric_c.metric(
        "Confirmed",
        sum(item["status"] == "Confirmed" for item in agreements),
    )

tab_rec, tab_ag, tab_cal = st.tabs(
    [":material/mic: New agreement", ":material/folder_open: Agreements", ":material/calendar_month: Calendar"]
)

# Render the other tabs first so st.stop() in the recording tab doesn't hide them.
with tab_ag:
    ag.render()

with tab_cal:
    cal.render()

with tab_rec:
    slot = st.empty()

    def stepper(done):
        out = ""
        labels = ["Speak · बोलिए", "Send · भेजिए", "Confirm · पक्का करें"]
        for i, label in enumerate(labels, 1):
            cls = "done" if i <= done else ("now" if i == done + 1 else "")
            num = IC_CHECK if i <= done else str(i)
            out += f'<div class="stp-i {cls}"><span>{num}</span>{label}</div>'
        slot.markdown(f'<div class="stp">{out}</div>', unsafe_allow_html=True)

    scn_label = st.radio(
        "Kind of agreement",
        list(SCENARIOS),
        format_func=lambda k: f"{SCENARIOS[k]['icon']} {k}",
        horizontal=True,
        label_visibility="collapsed",
    )
    scn = SCENARIOS[scn_label]

    with st.container(border=True):
        st.markdown("**1 · Speak**")
        st.caption(f"Try saying: “{scn['example']}” ")
        audio = st.audio_input(
            "Record a voice message (max 30 s)", sample_rate=16000, key=f"mic_{st.session_state.mic_n}"
        )

    if not audio:
        stepper(0)
        st.markdown(FOOT, unsafe_allow_html=True)
        st.stop()

    data = audio.getvalue()
    key = hash(data)

    # Call Prisma once per recording (not on every click) to save credits.
    if st.session_state.get("clip") != key:
        if API_KEY:
            with st.spinner("Listening…"):
                try:
                    verbatim, _ = call(data, "verbatim")  # sequential: some accounts allow 1 active request
                    transcribe, lang = call(data, "transcribe")
                except requests.HTTPError as e:
                    st.error(f"Prisma error: {e.response.status_code} {e.response.text}")
                    st.stop()
        else:
            verbatim, transcribe, lang = MOCK_VERBATIM, MOCK_TRANSCRIBE, "hi-IN"
        r0 = extract(transcribe)
        st.session_state.update(
            clip=key, verbatim=verbatim, transcribe=transcribe, lang=lang,
            sent=False, confirmed=False, cur_id=None,
            f_name=r0["name"] or "",
            f_amount=int(r0["amount"] or 0),
            f_due=r0["due"] or (date.today() + timedelta(days=7)),
            f_found=bool(r0["due"]),
        )

    verbatim = st.session_state.verbatim
    transcribe = st.session_state.transcribe
    lang = st.session_state.lang
    sent = st.session_state.sent
    confirmed = st.session_state.confirmed
    lang_name = LANGS.get(lang, lang or "Auto")

    stepper(3 if confirmed else 2 if sent else 1)

    with st.container(border=True):
        st.markdown("**2 · Check the details** · fix anything the AI got wrong")
        e1, e2, e3 = st.columns(3)
        name = e1.text_input("Who", key="f_name", disabled=sent)
        if scn["amount"]:
            amount = e2.number_input("Amount (₹)", min_value=0, step=50, key="f_amount", disabled=sent)
        else:
            amount = 0
        due = e3.date_input("Due date", key="f_due", disabled=sent)
        if not st.session_state.f_found:
            st.caption(":material/warning: No due date was heard, so a default is shown. Please set it.")

    due_txt = due.strftime("%d %b %Y")
    amount_row = (
        f'<div class="row"><span>{IC_RUPEE}Amount</span><b>₹{esc(amount)}</b></div>' if scn["amount"] else ""
    )
    c1, c2 = st.columns(2)
    c1.markdown(
        f"""
<div class="card"><h4>{IC_FILE}Structured record<span class="pill">{esc(lang_name)}</span></h4>
<div class="row"><span>{IC_USER}Who</span><b>{esc(name or '-')}</b></div>
{amount_row}
<div class="row"><span>{IC_CAL}Due</span><b>{esc(due_txt)}</b></div>
<div class="small">{esc(transcribe)}</div></div>
""",
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"""
<div class="card"><h4>{IC_MSG}Original words<span class="pill">verbatim</span></h4>
<div class="quote">{esc(verbatim)}</div>
<div class="small">Exactly as spoken, kept for reference.</div></div>
""",
        unsafe_allow_html=True,
    )

    st.write("")
    st.button(
        "Send for confirmation", icon=":material/send:", on_click=do_send,
        args=(scn_label, scn["amount"]), disabled=sent, type="primary", use_container_width=True,
    )

    if sent:
        reply = f'<div class="reply">YES {IC_YES}</div>' if confirmed else ""
        st.markdown(
            f"""
<div class="phone"><div class="top">{IC_PHONE}Message preview · simulated send</div>
<div class="bubble">{esc(build_msg(scn, name, amount, due_txt))}</div>{reply}</div>
""",
            unsafe_allow_html=True,
        )
        st.button(
            "Simulate: other party replies YES", icon=":material/reply:",
            on_click=do_confirm, disabled=confirmed,
        )

    if confirmed:
        st.markdown(
            f"""
<div class="calok"><div class="cal-date"><span>{due:%a}</span><b>{due:%d}</b><span style="color:#8A6A4B">{due:%b}</span></div>
<div><b>{IC_OK}Saved and added to calendar</b><br>{esc(name or 'Customer')} · due {due:%d %b}. Reminder set for the day before. See the Agreements and Calendar tabs.</div></div>
""",
            unsafe_allow_html=True,
        )
        st.button("Record another", icon=":material/mic:", on_click=do_reset)

    st.markdown(FOOT, unsafe_allow_html=True)
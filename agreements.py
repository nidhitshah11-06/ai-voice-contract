import html
from datetime import date, datetime

import streamlit as st

from lang_data import LANGS

TABLE = "agreements"


def _client():
    return st.session_state.supabase


def _normalize(row):
    created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
    confirmed_at = row.get("confirmed_at")
    if confirmed_at:
        confirmed_at = datetime.fromisoformat(confirmed_at.replace("Z", "+00:00"))
    return {
        "id": row["id"],
        "kind": row["kind"],
        "party": row["party"],
        "amount": row["amount"],
        "due": row["due"],
        "transcript": row["transcript"],
        "verbatim": row["verbatim"],
        "lang": row["lang"],
        "status": row["status"],
        "created": created.astimezone().strftime("%Y-%m-%d %H:%M"),
        "confirmed_at": (
            confirmed_at.astimezone().strftime("%Y-%m-%d %H:%M") if confirmed_at else None
        ),
    }


def init():
    user_id = st.session_state.user_id
    if st.session_state.get("agreements_user_id") != user_id:
        response = (
            _client().table(TABLE).select("*").order("created_at", desc=True).execute()
        )
        st.session_state.agreements = [_normalize(row) for row in response.data]
        st.session_state.agreements_user_id = user_id


def add(kind, party, amount, due, transcript, verbatim, lang):
    init()
    response = _client().table(TABLE).insert(
        {
            "kind": kind,
            "party": party,
            "amount": amount,
            "due": due.isoformat() if due else None,
            "transcript": transcript,
            "verbatim": verbatim,
            "lang": lang,
        }
    ).execute()
    if not response.data:
        raise RuntimeError("Supabase did not return the saved agreement.")
    a = _normalize(response.data[0])
    st.session_state.agreements.insert(0, a)
    return a["id"]


def confirm(aid):
    init()
    existing = next(
        (agreement for agreement in st.session_state.agreements if agreement["id"] == aid),
        None,
    )
    if existing is None:
        return None
    confirmed_at = datetime.now().astimezone().isoformat()
    (
        _client()
        .table(TABLE)
        .update({"status": "Confirmed", "confirmed_at": confirmed_at})
        .eq("id", aid)
        .eq("user_id", st.session_state.user_id)
        .execute()
    )
    updated = {**existing, "status": "Confirmed", "confirmed_at": confirmed_at}
    st.session_state.agreements = [
        updated if agreement["id"] == aid else agreement
        for agreement in st.session_state.agreements
    ]
    return updated


def remove(aid):
    (
        _client()
        .table(TABLE)
        .delete()
        .eq("id", aid)
        .eq("user_id", st.session_state.user_id)
        .execute()
    )
    st.session_state.agreements = [
        agreement for agreement in st.session_state.agreements if agreement["id"] != aid
    ]


def _record_text(a):
    due = date.fromisoformat(a["due"]).strftime("%d %b %Y") if a["due"] else "-"
    lines = [
        "AI VOICE CONTRACT - reference record (not legal advice)",
        f"ID: {a['id']}",
        f"Kind: {a['kind']}",
        f"Party: {a['party']}",
        f"Amount: Rs {a['amount']}" if a["amount"] else "Amount: -",
        f"Due: {due}",
        f"Status: {a['status']}",
        f"Language: {LANGS.get(a['lang'], a['lang'] or '-')}",
        f"Recorded: {a['created']}",
        "",
        "Clean transcript:",
        a["transcript"],
        "",
        "Original words (verbatim):",
        a["verbatim"],
    ]
    return "\n".join(lines)


def render():
    init()
    items = st.session_state.agreements

    m1, m2, m3 = st.columns(3)
    m1.metric("Agreements", len(items))
    m2.metric("Pending", sum(a["status"] == "Pending" for a in items))
    m3.metric("Confirmed", sum(a["status"] == "Confirmed" for a in items))

    f1, f2 = st.columns([3, 2])
    q = f1.text_input("Search by name", key="ag_q", placeholder="Search…")
    status = f2.selectbox("Status", ["All", "Pending", "Confirmed"], key="ag_s")

    shown = [
        a for a in items
        if (status == "All" or a["status"] == status) and q.strip().lower() in a["party"].lower()
    ]
    if not shown:
        st.info("No agreements yet. Record one in the New agreement tab.", icon=":material/info:")
        return

    for a in shown:
        due = date.fromisoformat(a["due"]).strftime("%d %b %Y") if a["due"] else "-"
        amt = f" · ₹{a['amount']}" if a["amount"] else ""
        ic = "check_circle" if a["status"] == "Confirmed" else "schedule"
        with st.expander(f":material/{ic}: {a['party']}{amt} · due {due} · {a['kind']}"):
            st.markdown(
                f"**Status:** {a['status']} · **Language:** "
                f"{LANGS.get(a['lang'], a['lang'] or '-')} · **Recorded:** {a['created']}"
            )
            st.markdown("**Original words (verbatim)**")
            st.markdown(
                f'<div class="quote">{html.escape(a["verbatim"])}</div>', unsafe_allow_html=True
            )
            st.caption(f"Clean transcript: {a['transcript']}")
            d1, d2 = st.columns(2)
            d1.download_button(
                "Download record", icon=":material/download:", data=_record_text(a),
                file_name=f"agreement_{a['id']}.txt", key=f"dl_{a['id']}",
            )
            d2.button(
                "Delete", icon=":material/delete:", key=f"rm_{a['id']}",
                on_click=remove, args=(a["id"],),
            )
import calendar
import html
from datetime import date, timedelta

import streamlit as st

TABLE = "calendar_entries"
REMIND = {"Same day": 0, "1 day before": 1, "2 days before": 2, "1 week before": 7}
LABEL = {v: k for k, v in REMIND.items()}

CSS = """<style>
.cal-grid {width:100%; border-collapse:separate; border-spacing:4px; table-layout:fixed;}
.cal-grid th {color:#8A6A4B; font-size:.78rem; padding:4px 0;}
.cal-grid td {vertical-align:top; height:92px; padding:6px; border-radius:12px; background:#FFFDF8;
              border:1px solid #F0DDC2; overflow:hidden;}
.cal-grid td.out {opacity:.4;}
.cal-grid td.today {background:#FFF1DA; border:2px solid #EA580C;}
.dn {font-weight:700; font-size:.82rem; color:#3B2A1E; margin-bottom:3px;}
.chip {font-size:.68rem; padding:2px 5px; border-radius:6px; margin-top:2px; white-space:nowrap;
       overflow:hidden; text-overflow:ellipsis;}
.chip.due {background:#FFE0B8; color:#9A3412;}
.chip.past {background:#FBD5D0; color:#B42318;}
.chip.rem {background:#F4EDB0; color:#6B5300;}
.more {font-size:.66rem; color:#8A6A4B; margin-top:2px;}
.legend {color:#8A6A4B; font-size:.8rem; margin:4px 0 10px;}
.lg {display:inline-block; width:11px; height:11px; border-radius:3px; margin:0 5px 0 12px; vertical-align:-1px;}
.lg:first-child {margin-left:0;}
.lg.due {background:#FFE0B8;} .lg.past {background:#FBD5D0;} .lg.rem {background:#F4EDB0;}
</style>"""


def _lbl(e):
    return f"{e['title']} ₹{e['amount']}" if e["amount"] else e["title"]


def init():
    user_id = st.session_state.user_id
    if st.session_state.get("entries_user_id") != user_id:
        response = (
            st.session_state.supabase.table(TABLE)
            .select("*")
            .order("due")
            .execute()
        )
        st.session_state.entries = response.data
        st.session_state.entries_user_id = user_id
    today = date.today()
    st.session_state.setdefault("cal_y", today.year)
    st.session_state.setdefault("cal_m", today.month)


def add_entry(title, amount, due, remind_days=1):
    init()
    iso = due.isoformat()
    for e in st.session_state.entries:  # skip exact duplicates
        if e["title"] == title and e["amount"] == amount and e["due"] == iso:
            return
    response = (
        st.session_state.supabase.table(TABLE)
        .insert({"title": title, "amount": amount, "due": iso, "remind": remind_days})
        .execute()
    )
    if not response.data:
        raise RuntimeError("Supabase did not return the saved calendar entry.")
    st.session_state.entries.extend(response.data)


def _remove(eid):
    (
        st.session_state.supabase.table(TABLE)
        .delete()
        .eq("id", eid)
        .eq("user_id", st.session_state.user_id)
        .execute()
    )
    st.session_state.entries = [e for e in st.session_state.entries if e["id"] != eid]


def _shift(delta):
    y, m = st.session_state.cal_y, st.session_state.cal_m + delta
    if m < 1:
        y, m = y - 1, 12
    elif m > 12:
        y, m = y + 1, 1
    st.session_state.cal_y, st.session_state.cal_m = y, m


def _today():
    t = date.today()
    st.session_state.cal_y, st.session_state.cal_m = t.year, t.month


def _seed():
    t = date.today()
    for name, amt, off in [("Verma", 1200, -35), ("Patil", 350, -9), ("Shah", 800, 4), ("Khan", 2000, 21)]:
        add_entry(name, amt, t + timedelta(days=off), 1)


def _clear():
    (
        st.session_state.supabase.table(TABLE)
        .delete()
        .eq("user_id", st.session_state.user_id)
        .execute()
    )
    st.session_state.entries = []


def render():
    init()
    st.markdown(CSS, unsafe_allow_html=True)
    y, m = st.session_state.cal_y, st.session_state.cal_m
    today = date.today()
    entries = st.session_state.entries

    by_day = {}
    for e in entries:
        d = date.fromisoformat(e["due"])
        by_day.setdefault(d, []).append(("due", e))
        if e["remind"] > 0:
            by_day.setdefault(d - timedelta(days=e["remind"]), []).append(("rem", e))

    n1, n2, n3, n4 = st.columns([1.3, 3.4, 1.3, 1.3])
    n1.button("Prev", icon=":material/chevron_left:", on_click=_shift, args=(-1,),
              key="cal_prev", use_container_width=True)
    n2.markdown(
        f"<h3 style='text-align:center;margin:0;color:#7C2D12'>{calendar.month_name[m]} {y}</h3>",
        unsafe_allow_html=True,
    )
    n3.button("Today", icon=":material/today:", on_click=_today, key="cal_today", use_container_width=True)
    n4.button("Next", icon=":material/chevron_right:", on_click=_shift, args=(1,),
              key="cal_next", use_container_width=True)

    rows = ""
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(y, m):
        cells = ""
        for d in week:
            cls = ("out " if d.month != m else "") + ("today" if d == today else "")
            items = by_day.get(d, [])
            chips = ""
            for kind, e in items[:2]:
                label = html.escape(_lbl(e))
                if kind == "rem":
                    chips += f'<div class="chip rem">Remind · {label}</div>'
                else:
                    c = "past" if d < today else "due"
                    chips += f'<div class="chip {c}">{label}</div>'
            if len(items) > 2:
                chips += f'<div class="more">+{len(items) - 2} more</div>'
            cells += f'<td class="{cls.strip()}"><div class="dn">{d.day}</div>{chips}</td>'
        rows += f"<tr>{cells}</tr>"
    head = "".join(f"<th>{n}</th>" for n in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    st.markdown(f'<table class="cal-grid"><tr>{head}</tr>{rows}</table>', unsafe_allow_html=True)
    st.markdown(
        '<div class="legend"><span class="lg due"></span>Due date'
        '<span class="lg past"></span>Past due'
        '<span class="lg rem"></span>Reminder day</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### :material/notifications: Reminders, next 7 days")
    soon = []
    for e in entries:
        d = date.fromisoformat(e["due"])
        r = d - timedelta(days=e["remind"])
        if today <= r <= today + timedelta(days=7):
            soon.append((r, d, e))
    if soon:
        for r, d, e in sorted(soon, key=lambda x: x[0]):
            st.write(f"**{r:%a %d %b}** · {_lbl(e)} (due {d:%d %b})")
    else:
        st.caption("No reminders in the next 7 days.")

    st.markdown(f"#### Entries in {calendar.month_name[m]}")
    month_entries = sorted(
        [e for e in entries if e["due"][:7] == f"{y}-{m:02d}"], key=lambda e: e["due"]
    )
    if not month_entries:
        st.caption("Nothing this month.")
    for e in month_entries:
        a, b = st.columns([6, 2])
        d = date.fromisoformat(e["due"])
        a.write(f"**{d:%a %d %b}** · {_lbl(e)} · reminder: {LABEL.get(e['remind'], '')}")
        b.button("Delete", icon=":material/delete:", key=f"del_{e['id']}",
                 on_click=_remove, args=(e["id"],))

    with st.expander(":material/add: Add entry"):
        with st.form("add_form", clear_on_submit=True):
            t = st.text_input("Who / what")
            amt = st.number_input("Amount (₹)", min_value=0, step=50)
            dd = st.date_input("Due date", value=today)
            rr = st.selectbox("Reminder", list(REMIND))
            if st.form_submit_button("Add to calendar") and t.strip():
                add_entry(t.strip(), int(amt), dd, REMIND[rr])
                st.rerun()

    with st.expander(":material/science: Demo data"):
        st.button("Load sample entries (past + future)", on_click=_seed)
        st.button("Clear all entries", on_click=_clear)
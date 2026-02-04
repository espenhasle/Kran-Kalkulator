import streamlit as st
import pandas as pd
import datetime as dt
import holidays
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path as _Path

# ===========================
# Sideoppsett + stil
# ===========================
st.set_page_config(page_title="KranKalkulator", page_icon="⚓", layout="wide")

CSS = """
<style>
:root{
  --kh-navy:#0B2E3A;
  --kh-teal:#2E6F77;
  --kh-sea:#A7C4C2;
  --kh-mist:#F2F5F4;
  --kh-warn:#B23A2A;
}
.block-container{padding-top: 1.4rem;}
.kh-hero{
  background: linear-gradient(135deg, rgba(46,111,119,0.18), rgba(167,196,194,0.18));
  border: 1px solid rgba(46,111,119,0.20);
  padding: 1.0rem 1.1rem;
  border-radius: 18px;
}
.kh-hero h1{color: var(--kh-navy); margin: 0;}
.kh-hero p{color: rgba(11,46,58,0.85); margin: .25rem 0 0 0; font-size: 0.98rem;}
.kh-card{
  background: white;
  border: 1px solid rgba(46,111,119,0.18);
  border-radius: 16px;
  padding: 0.9rem 0.95rem;
}
.small-muted{color: rgba(11,46,58,0.65); font-size: .9rem;}
.err{color: var(--kh-warn); font-weight: 600;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ===========================
# Logo (støtter både Assets/ og assets/)
# ===========================
LOGO_CANDIDATES = [
    _Path("assets/kristiansand_havn.png"),
    _Path("assets/kristiansand_havn.jpg"),
    _Path("Assets/kristiansand_havn.png"),
    _Path("Assets/kristiansand_havn.jpg"),
    _Path("assets/kristiansand_havn.png.png"),
    _Path("Assets/kristiansand_havn.png.png"),
]

def _find_logo() -> Optional[str]:
    for p in LOGO_CANDIDATES:
        if p.exists():
            return str(p)
    return None

LOGO_PATH = _find_logo()

# ===========================
# Helligdager (automatisk)
# ===========================
NO_HOLIDAYS = holidays.country_holidays("NO")

def is_holiday(d: dt.date) -> bool:
    return d in NO_HOLIDAYS

def is_weekend(d: dt.date) -> bool:
    return d.weekday() >= 5  # 5=lør, 6=søn

# ===========================
# Regler
# ===========================
@dataclass(frozen=True)
class Rules:
    day_start: dt.time          # 07:30
    day_end: dt.time            # 15:00
    ot50_end: dt.time           # 21:00
    night_end: dt.time          # 07:30 (neste dag)

DEFAULT_RULES = Rules(
    day_start=dt.time(7, 30),
    day_end=dt.time(15, 0),
    ot50_end=dt.time(21, 0),
    night_end=dt.time(7, 30),
)

# ===========================
# Parsing / hjelpefunksjoner
# ===========================
def _to_date(x) -> Optional[dt.date]:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, dt.date) and not isinstance(x, dt.datetime):
        return x
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

def _to_time(x) -> Optional[dt.time]:
    """Aksepterer:
    - dt.time / dt.datetime
    - 'HH:MM'
    - 'HHMM' (0730)
    - 'HMM' (730)
    - 'H.MM' / 'H,MM' (7.30)
    - '7' / '07' -> 07:00
    """
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, dt.time):
        return x
    if isinstance(x, dt.datetime):
        return x.time()

    s = str(x).strip()
    if not s:
        return None

    s = s.replace(".", ":").replace(",", ":")

    if ":" in s:
        try:
            hh, mm = s.split(":")
            return dt.time(int(hh), int(mm))
        except Exception:
            return None

    if s.isdigit():
        try:
            if len(s) == 4:      # 0730
                hh, mm = int(s[:2]), int(s[2:])
            elif len(s) == 3:    # 730
                hh, mm = int(s[0]), int(s[1:])
            elif len(s) <= 2:    # 7 / 07
                hh, mm = int(s), 0
            else:
                return None
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                return dt.time(hh, mm)
        except Exception:
            return None

    return None

def _to_timedelta(x) -> dt.timedelta:
    """Aksepterer:
    - dt.timedelta
    - 'HH:MM'
    - 'HHMM' (0130 -> 1t 30m)
    - 'HMM' (130 -> 1t 30m)
    - 'MM' (minutter)
    """
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return dt.timedelta(0)
    if isinstance(x, dt.timedelta):
        return x

    s = str(x).strip()
    if not s:
        return dt.timedelta(0)

    s = s.replace(".", ":").replace(",", ":")

    if ":" in s:
        try:
            hh, mm = s.split(":")
            return dt.timedelta(hours=int(hh), minutes=int(mm))
        except Exception:
            return dt.timedelta(0)

    if s.isdigit():
        try:
            if len(s) == 4:      # 0130
                hh, mm = int(s[:2]), int(s[2:])
                return dt.timedelta(hours=hh, minutes=mm)
            if len(s) == 3:      # 130
                hh, mm = int(s[0]), int(s[1:])
                return dt.timedelta(hours=hh, minutes=mm)
            return dt.timedelta(minutes=int(s))  # ellers minutter
        except Exception:
            return dt.timedelta(0)

    return dt.timedelta(0)

def combine(d: dt.date, t: dt.time) -> dt.datetime:
    return dt.datetime.combine(d, t)

def hours(td: dt.timedelta) -> float:
    return round(td.total_seconds() / 3600.0, 2)

def split_work_by_windows(start_dt: dt.datetime, end_dt: dt.datetime, rules: Rules, day: dt.date) -> Dict[str, dt.timedelta]:
    """Fordeler tid på ordinær / OT50 / OT100 (ukedag), eller helg/helligdag."""
    if end_dt <= start_dt:
        return {}

    total = end_dt - start_dt

    if is_holiday(day):
        return {"holiday": total}
    if is_weekend(day):
        return {"weekend": total}

    d0 = day
    ord_start = combine(d0, rules.day_start)
    ord_end = combine(d0, rules.day_end)
    ot50_end = combine(d0, rules.ot50_end)
    night_start = ot50_end
    night_end = combine(d0 + dt.timedelta(days=1), rules.night_end)

    def overlap(a1, a2, b1, b2):
        s = max(a1, b1)
        e = min(a2, b2)
        return max(dt.timedelta(0), e - s)

    ord_td = overlap(start_dt, end_dt, ord_start, ord_end)
    ot50_td = overlap(start_dt, end_dt, ord_end, ot50_end)

    # OT100: 21:00 -> 07:30 + evt før 07:30 samme dag
    ot100_td = overlap(start_dt, end_dt, night_start, night_end)
    ot100_td += overlap(start_dt, end_dt, combine(d0, dt.time(0, 0)), ord_start)

    return {"ord": ord_td, "ot50": ot50_td, "ot100": ot100_td}

def compute_row(date_val: Any, start_t: Any, end_t: Any, meal_td: Any, wait_td: Any, rules: Rules) -> Dict[str, Any]:
    d = _to_date(date_val)
    s = _to_time(start_t)
    e = _to_time(end_t)
    meal = _to_timedelta(meal_td)
    wait = _to_timedelta(wait_td)

    if not d or not s or not e:
        return {"_error": "Dato, start og slutt må fylles inn."}

    start_dt = combine(d, s)
    end_dt = combine(d, e)
    if end_dt <= start_dt:
        end_dt += dt.timedelta(days=1)  # over midnatt

    total_td = end_dt - start_dt
    billed_td = total_td - meal - wait
    if billed_td < dt.timedelta(0):
        billed_td = dt.timedelta(0)

    buckets = split_work_by_windows(start_dt, end_dt, rules, d)

    return {
        "Totalt timer": hours(total_td),
        "Ordinær (07:30-15:00)": hours(buckets.get("ord", dt.timedelta(0))),
        "Overtid 50% (15:00-21:00)": hours(buckets.get("ot50", dt.timedelta(0))),
        "Overtid 100% (21:00-07:30)": hours(buckets.get("ot100", dt.timedelta(0))),
        "Overtid 100% Helg": hours(buckets.get("weekend", dt.timedelta(0))),
        "Overtid 133% Helligdag": hours(buckets.get("holiday", dt.timedelta(0))),
        "Spisetid (t)": hours(meal),
        "Ventetid (t)": hours(wait),
        "Fakturerbar Krantid (t)": hours(billed_td),
    }

# ===========================
# Sidebar (innstillinger)
# ===========================
with st.sidebar:
    st.markdown("## ⚙️ Innstillinger")
    st.caption("Juster tidsvinduer ved behov.")

    c1, c2, c3 = st.columns(3)
    with c1:
        day_start = st.time_input("Ordinær start", DEFAULT_RULES.day_start, step=dt.timedelta(minutes=15))
    with c2:
        day_end = st.time_input("Ordinær slutt", DEFAULT_RULES.day_end, step=dt.timedelta(minutes=15))
    with c3:
        ot50_end = st.time_input("OT 50% slutt", DEFAULT_RULES.ot50_end, step=dt.timedelta(minutes=15))

    rules = Rules(day_start=day_start, day_end=day_end, ot50_end=ot50_end, night_end=DEFAULT_RULES.night_end)

    with st.expander("📌 Tips", expanded=False):
        st.markdown(
            "- Du kan skrive klokkeslett som **0730**, **730**, **07:30**, **7.30**.\n"
            "- Hvis slutt er tidligere enn start, tolkes det som **over midnatt**.\n"
            "- Helg: all tid blir *Overtid 100% Helg*.\n"
            "- Helligdag: all tid blir *Overtid 133% Helligdag*.\n"
            "- Fakturerbar = totalt − spisetid − ventetid."
        )

# ===========================
# Header
# ===========================
top_left, top_right = st.columns([0.22, 0.78], vertical_alignment="center")
with top_left:
    if LOGO_PATH:
        st.image(LOGO_PATH, use_container_width=True)
with top_right:
    st.markdown(
        """
<div class="kh-hero">
  <h1>⚓ KranKalkulator</h1>
  <p>Registrer økter og få automatisk fordeling på ordinær/overtid + fakturerbar krantid.</p>
</div>
""",
        unsafe_allow_html=True,
    )

st.write("")

# ===========================
# Inndata (bruk tekstfelt for Start/Slutt for å støtte 0730)
# ===========================
default = pd.DataFrame(
    [{
        "Dato": dt.date.today(),
        "Start": "0730",
        "Slutt": "1500",
        "Spisetid (HH:MM)": "0100",
        "Ventetid (HH:MM)": "0000",
        "Kommentar (valgfritt)": "",
    }]
)

left, right = st.columns([1.05, 1.0], gap="large")

with left:
    st.markdown('<div class="kh-card">', unsafe_allow_html=True)
    st.subheader("📝 Registreringer")

    edited = st.data_editor(
        default,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Dato": st.column_config.DateColumn(format="YYYY-MM-DD", help="Dato for økten"),
            "Start": st.column_config.TextColumn(help="F.eks 0730 / 07:30 / 7.30"),
            "Slutt": st.column_config.TextColumn(help="F.eks 1530 / 15:30 (kan være neste dag)"),
            "Spisetid (HH:MM)": st.column_config.TextColumn(help="F.eks 0100 / 01:00 / 60 (min)"),
            "Ventetid (HH:MM)": st.column_config.TextColumn(help="F.eks 0030 / 00:30 / 15 (min)"),
            "Kommentar (valgfritt)": st.column_config.TextColumn(help="Fri tekst (tas med i eksport)"),
        },
    )
    st.caption("Hvis slutt < start, tolkes økten som over midnatt.")
    st.markdown("</div>", unsafe_allow_html=True)

# ===========================
# Beregn out_df (VIKTIG: før oppsummering)
# ===========================
rows = []
errors = 0

for _, r in edited.iterrows():
    out = compute_row(
        r.get("Dato"),
        r.get("Start"),
        r.get("Slutt"),
        r.get("Spisetid (HH:MM)"),
        r.get("Ventetid (HH:MM)"),
        rules,
    )

    base = {
        "Dato": _to_date(r.get("Dato")),
        "Start": str(r.get("Start") or "").strip(),
        "Slutt": str(r.get("Slutt") or "").strip(),
        "Spisetid": r.get("Spisetid (HH:MM)"),
        "Ventetid": r.get("Ventetid (HH:MM)"),
        "Kommentar": r.get("Kommentar (valgfritt)"),
    }

    if "_error" in out:
        errors += 1
        base["Feil"] = out["_error"]
        rows.append(base)
    else:
        base["Feil"] = ""
        rows.append({**base, **out})

out_df = pd.DataFrame(rows)

with right:
    st.markdown('<div class="kh-card">', unsafe_allow_html=True)
    st.subheader("📊 Resultat (forhåndsvisning)")
    if errors:
        st.markdown(f'<div class="err">⚠️ {errors} rad(er) mangler dato/start/slutt.</div>', unsafe_allow_html=True)
    st.dataframe(out_df, use_container_width=True, height=360)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# ===========================
# Oppsummering + eksport
# ===========================
st.markdown('<div class="kh-card">', unsafe_allow_html=True)
st.subheader("✅ Oppsummering")

numeric_cols = [
    "Totalt timer",
    "Ordinær (07:30-15:00)",
    "Overtid 50% (15:00-21:00)",
    "Overtid 100% (21:00-07:30)",
    "Overtid 100% Helg",
    "Overtid 133% Helligdag",
    "Spisetid (t)",
    "Ventetid (t)",
    "Fakturerbar Krantid (t)",
]
existing_numeric_cols = [c for c in numeric_cols if c in out_df.columns]
totals = out_df[existing_numeric_cols].sum(numeric_only=True) if existing_numeric_cols else pd.Series(dtype=float)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Fakturerbar krantid (t)", f"{totals.get('Fakturerbar Krantid (t)', 0):.2f}")
k2.metric("Totalt (t)", f"{totals.get('Totalt timer', 0):.2f}")
k3.metric("Ordinær (t)", f"{totals.get('Ordinær (07:30-15:00)', 0):.2f}")
k4.metric("Overtid totalt (t)", f"{(totals.get('Overtid 50% (15:00-21:00)', 0)+totals.get('Overtid 100% (21:00-07:30)', 0)+totals.get('Overtid 100% Helg', 0)+totals.get('Overtid 133% Helligdag', 0)):.2f}")

with st.expander("Se summeringstabell", expanded=False):
    st.dataframe(pd.DataFrame([totals]).T.rename(columns={0: "Sum (t)"}), use_container_width=True)

st.markdown('<p class="small-muted">Eksporten inkluderer også eventuelle kommentarer per rad.</p>', unsafe_allow_html=True)

st.download_button(
    "⬇️ Last ned som CSV",
    data=out_df.to_csv(index=False).encode("utf-8"),
    file_name="kran_kalkulator.csv",
    mime="text/csv",
)

st.markdown("</div>", unsafe_allow_html=True)

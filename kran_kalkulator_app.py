import streamlit as st
import pandas as pd
import datetime as dt
from dataclasses import dataclass
from typing import Optional, Dict, Any

# ---------------------------
# Sideoppsett + "havnefarger"
# ---------------------------
st.set_page_config(
    page_title="KranKalkulator",
    page_icon="⚓",
    layout="wide",
)

CSS = """
<style>
:root{
  --kh-navy:#0B2E3A;
  --kh-teal:#2E6F77;
  --kh-sea:#A7C4C2;
  --kh-mist:#F2F5F4;
  --kh-sand:#E6D8C3;
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
.kh-kpi{
  display:flex; gap: .75rem; flex-wrap:wrap;
}
.kh-kpi .k{
  background: var(--kh-mist);
  border: 1px solid rgba(46,111,119,0.14);
  border-radius: 14px;
  padding: 0.65rem 0.75rem;
  min-width: 210px;
}
.kh-kpi .k .t{font-size: .82rem; color: rgba(11,46,58,0.7);}
.kh-kpi .k .v{font-size: 1.3rem; font-weight: 700; color: var(--kh-navy);}
.small-muted{color: rgba(11,46,58,0.65); font-size: .9rem;}
.err{color: var(--kh-warn); font-weight: 600;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------
# Helligdager (samme liste som i Excel-arket)
# ---------------------------
HOLIDAYS = set([
    '2025-01-01','2025-04-13','2025-04-17','2025-04-18','2025-04-20','2025-04-21','2025-05-01','2025-05-17','2025-05-29','2025-06-08','2025-06-09','2025-12-25','2025-12-26',
    '2026-01-01','2026-03-29','2026-04-02','2026-04-03','2026-04-05','2026-04-06','2026-05-01','2026-05-14','2026-05-17','2026-05-24','2026-05-25','2026-12-25','2026-12-26',
])

# ---------------------------
# Regler (kan justeres i sidebar)
# ---------------------------
@dataclass(frozen=True)
class Rules:
    day_start: dt.time          # 07:30
    day_end: dt.time            # 15:00
    ot50_end: dt.time           # 21:00
    night_end: dt.time          # 07:30 (neste dag)
    weekend_multiplier: str     # kun label
    holiday_multiplier: str     # kun label

DEFAULT_RULES = Rules(
    day_start=dt.time(7, 30),
    day_end=dt.time(15, 0),
    ot50_end=dt.time(21, 0),
    night_end=dt.time(7, 30),
    weekend_multiplier="100%",
    holiday_multiplier="133%",
)

# ---------------------------
# Hjelpefunksjoner
# ---------------------------
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
    """Aksepterer dt.time eller 'HH:MM'."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, dt.time):
        return x
    if isinstance(x, dt.datetime):
        return x.time()
    s = str(x).strip()
    if not s:
        return None
    try:
        hh, mm = s.split(":")
        return dt.time(int(hh), int(mm))
    except Exception:
        return None

def _to_timedelta(x) -> dt.timedelta:
    """Aksepterer dt.timedelta eller 'HH:MM' eller 'MM'."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return dt.timedelta(0)
    if isinstance(x, dt.timedelta):
        return x
    s = str(x).strip()
    if not s:
        return dt.timedelta(0)
    try:
        if ":" in s:
            hh, mm = s.split(":")
            return dt.timedelta(hours=int(hh), minutes=int(mm))
        return dt.timedelta(minutes=int(s))
    except Exception:
        return dt.timedelta(0)

def is_holiday(d: dt.date) -> bool:
    return d.strftime("%Y-%m-%d") in HOLIDAYS

def is_weekend(d: dt.date) -> bool:
    return d.weekday() >= 5  # 5=Sat, 6=Sun

def combine(d: dt.date, t: dt.time) -> dt.datetime:
    return dt.datetime.combine(d, t)

def hours(td: dt.timedelta) -> float:
    return round(td.total_seconds() / 3600.0, 2)

def split_work_by_windows(
    start_dt: dt.datetime,
    end_dt: dt.datetime,
    rules: Rules,
    day: dt.date,
) -> Dict[str, dt.timedelta]:
    """
    Fordeler tid på:
    - Ordinær (07:30-15:00)
    - OT 50% (15:00-21:00)
    - OT 100% (21:00-07:30)
    Helg: alt -> Helg 100%
    Helligdag: alt -> Helligdag 133%
    """
    if end_dt <= start_dt:
        return {}

    total = end_dt - start_dt

    # Helg / helligdag: hele økta i egen bøtte
    if is_holiday(day):
        return {"holiday": total}
    if is_weekend(day):
        return {"weekend": total}

    d0 = day
    # Vinduer samme dag
    ord_start = combine(d0, rules.day_start)
    ord_end = combine(d0, rules.day_end)
    ot50_end = combine(d0, rules.ot50_end)

    # Nattvindu (21:00 -> 07:30 neste dag)
    night_start = ot50_end
    night_end = combine(d0 + dt.timedelta(days=1), rules.night_end)

    def overlap(a1, a2, b1, b2):
        s = max(a1, b1)
        e = min(a2, b2)
        return max(dt.timedelta(0), e - s)

    ord_td = overlap(start_dt, end_dt, ord_start, ord_end)
    ot50_td = overlap(start_dt, end_dt, ord_end, ot50_end)
    ot100_td = overlap(start_dt, end_dt, night_start, night_end)

    # Rest (før 07:30 samme dag) håndteres som OT 100%
    pre_day_start = overlap(start_dt, end_dt, combine(d0, dt.time(0, 0)), ord_start)
    ot100_td += pre_day_start

    return {"ord": ord_td, "ot50": ot50_td, "ot100": ot100_td}

def compute_row(
    date_val: Any,
    start_t: Any,
    end_t: Any,
    meal_td: Any,
    wait_td: Any,
    rules: Rules,
) -> Dict[str, Any]:
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
        # Antar over midnatt
        end_dt += dt.timedelta(days=1)

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
        f"Overtid 100% Helg": hours(buckets.get("weekend", dt.timedelta(0))),
        f"Overtid 133% Helligdag": hours(buckets.get("holiday", dt.timedelta(0))),
        "Spisetid (t)": hours(meal),
        "Ventetid (t)": hours(wait),
        "Fakturerbar Krantid (t)": hours(billed_td),
    }

# ---------------------------
# Sidebar: regler + hjelpetekst
# ---------------------------
with st.sidebar:
    st.markdown("## ⚙️ Innstillinger")
    st.caption("Du kan justere tidsvinduene her hvis dere endrer satser/regler senere.")

    c1, c2, c3 = st.columns(3)
    with c1:
        day_start = st.time_input("Ordinær start", DEFAULT_RULES.day_start, step=dt.timedelta(minutes=15))
    with c2:
        day_end = st.time_input("Ordinær slutt", DEFAULT_RULES.day_end, step=dt.timedelta(minutes=15))
    with c3:
        ot50_end = st.time_input("OT 50% slutt", DEFAULT_RULES.ot50_end, step=dt.timedelta(minutes=15))

    rules = Rules(
        day_start=day_start,
        day_end=day_end,
        ot50_end=ot50_end,
        night_end=DEFAULT_RULES.night_end,  # fast (07:30)
        weekend_multiplier=DEFAULT_RULES.weekend_multiplier,
        holiday_multiplier=DEFAULT_RULES.holiday_multiplier,
    )

    with st.expander("📌 Hvordan lese resultatet", expanded=False):
        st.markdown(
            """
- **Ordinær / OT** beregnes automatisk basert på dato og klokkeslett.
- **Helg:** all tid går til *Overtid 100% Helg*.
- **Helligdag:** all tid går til *Overtid 133% Helligdag*.
- **Fakturerbar krantid** = *Totalt* − *spisetid* − *ventetid*.
            """.strip()
        )

# ---------------------------
# Topp / intro
# ---------------------------
st.markdown(
    """
<div class="kh-hero">
  <h1>⚓ KranKalkulator</h1>
  <p>Legg inn økter under, så får du automatisk fordeling på ordinær / overtid og fakturerbar krantid.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

# ---------------------------
# Inndata
# ---------------------------
default = pd.DataFrame(
    [
        {
            "Dato": dt.date.today(),
            "Start": dt.time(7, 30),
            "Slutt": dt.time(15, 0),
            "Spisetid (HH:MM)": "01:00",
            "Ventetid (HH:MM)": "00:00",
            "Kommentar (valgfritt)": "",
        }
    ]
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
            "Start": st.column_config.TimeColumn(format="HH:mm", help="Starttid"),
            "Slutt": st.column_config.TimeColumn(format="HH:mm", help="Sluttid (kan være neste dag)"),
            "Spisetid (HH:MM)": st.column_config.TextColumn(help="Varighet, f.eks 01:00 (eller 30 for 30 min)"),
            "Ventetid (HH:MM)": st.column_config.TextColumn(help="Varighet, f.eks 00:30 (eller 15 for 15 min)"),
            "Kommentar (valgfritt)": st.column_config.TextColumn(help="Fri tekst (vises også i eksport)"),
        },
    )

    st.caption("Tips: Hvis **slutt** er tidligere enn **start**, tolkes det som over midnatt.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="kh-card">', unsafe_allow_html=True)
    st.subheader("📊 Resultat (forhåndsvisning)")

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
            "Start": _to_time(r.get("Start")).strftime("%H:%M") if _to_time(r.get("Start")) else None,
            "Slutt": _to_time(r.get("Slutt")).strftime("%H:%M") if _to_time(r.get("Slutt")) else None,
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

    if errors:
        st.markdown(f'<div class="err">⚠️ {errors} rad(er) mangler dato/start/slutt.</div>', unsafe_allow_html=True)

    st.dataframe(out_df, use_container_width=True, height=360)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# ---------------------------
# Oppsummering + eksport
# ---------------------------
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

totals = out_df[numeric_cols].sum(numeric_only=True)

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

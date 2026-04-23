# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import datetime as dt
import io
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
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
  --kh-success:#2E7D6B;
  --kh-gold:#C9A14A;
}
.block-container{padding-top: 1.2rem; max-width: 1400px;}

/* Hero */
.kh-hero{
  background: linear-gradient(135deg, rgba(46,111,119,0.18), rgba(167,196,194,0.18));
  border: 1px solid rgba(46,111,119,0.20);
  padding: 1.0rem 1.2rem;
  border-radius: 18px;
}
.kh-hero h1{color: var(--kh-navy); margin: 0; font-size: 1.8rem;}
.kh-hero p{color: rgba(11,46,58,0.85); margin: .25rem 0 0 0; font-size: 0.98rem;}

/* Seksjonskort */
.kh-card{
  background: white;
  border: 1px solid rgba(46,111,119,0.18);
  border-radius: 16px;
  padding: 1.0rem 1.2rem;
  margin-bottom: 0.9rem;
}
.kh-section-title{
  color: var(--kh-navy);
  font-weight: 700;
  font-size: 1.15rem;
  margin: 0 0 .8rem 0;
  padding-bottom: .45rem;
  border-bottom: 2px solid var(--kh-sea);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: .4rem;
}
.kh-chips{
  display: flex;
  gap: .35rem;
  flex-wrap: wrap;
  align-items: center;
}
.kh-chip{
  font-size: .78rem;
  font-weight: 500;
  padding: .2rem .6rem;
  border-radius: 999px;
  text-transform: none;
  letter-spacing: 0;
  border: 1px solid transparent;
}
.kh-chip.period{color: var(--kh-teal); background: var(--kh-mist); border-color: rgba(46,111,119,0.2);}
.kh-chip.hellig{color: #7a3a00; background: #fff2d6; border-color: #e0b265;}

/* Fakturagrunnlag-hero */
.kh-invoice-hero{
  background: linear-gradient(135deg, #0B2E3A 0%, #2E6F77 100%);
  color: white;
  border-radius: 18px;
  padding: 1.3rem 1.5rem;
  box-shadow: 0 4px 18px rgba(11,46,58,0.22);
  margin-bottom: 1rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}
.kh-invoice-hero .block .label{
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: .08em;
  opacity: .85;
  margin-bottom: .35rem;
}
.kh-invoice-hero .block .value{
  font-size: 2.6rem;
  font-weight: 700;
  line-height: 1;
}
.kh-invoice-hero .block .unit{
  font-size: 1.1rem;
  font-weight: 400;
  opacity: .85;
  margin-left: .35rem;
}
.kh-invoice-hero .block .sub{
  font-size: .88rem;
  opacity: .82;
  margin-top: .55rem;
}
.kh-invoice-hero .divider{
  width: 1px;
  background: rgba(255,255,255,0.22);
}

/* Rate-tabell */
.kh-rate-table{
  border: 1px solid rgba(46,111,119,0.18);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: .6rem;
}
.kh-rate-row{
  display: grid;
  grid-template-columns: 2.2fr 1fr 1fr 1.2fr;
  gap: 1rem;
  padding: .8rem 1rem;
  border-bottom: 1px solid rgba(46,111,119,0.10);
  align-items: center;
  font-variant-numeric: tabular-nums;
}
.kh-rate-row:last-child{border-bottom: none;}
.kh-rate-row.header{
  font-weight: 600;
  color: var(--kh-navy);
  background: var(--kh-mist);
  border-bottom: 2px solid var(--kh-teal);
  font-size: .80rem;
  text-transform: uppercase;
  letter-spacing: .05em;
}
.kh-rate-row.total{
  font-weight: 700;
  background: rgba(46,111,119,0.08);
  border-top: 2px solid var(--kh-teal);
  color: var(--kh-navy);
  font-size: 1.02rem;
}
.kh-rate-row.zero{opacity: 0.42;}
.kh-rate-name{color: var(--kh-navy);}
.kh-right{text-align: right;}
.kh-muted-val{color: rgba(11,46,58,0.55);}

/* Deductions boks */
.kh-deduct-row{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: .8rem;
  margin-top: .6rem;
}
.kh-deduct-item{
  background: var(--kh-mist);
  border-radius: 10px;
  padding: .7rem .9rem;
  border-left: 3px solid var(--kh-teal);
}
.kh-deduct-item .lbl{font-size: .82rem; color: rgba(11,46,58,0.7);}
.kh-deduct-item .val{font-size: 1.3rem; font-weight: 600; color: var(--kh-navy); font-variant-numeric: tabular-nums;}

.small-muted{color: rgba(11,46,58,0.65); font-size: .88rem;}
.err{color: var(--kh-warn); font-weight: 600; padding: .3rem 0;}

/* Responsiv */
@media (max-width: 760px){
  .kh-invoice-hero{grid-template-columns: 1fr; gap: .8rem;}
  .kh-invoice-hero .divider{display: none;}
  .kh-rate-row{grid-template-columns: 1.6fr 1fr 1fr; gap: .5rem; font-size: .9rem;}
  .kh-rate-row .kh-hide-mobile{display: none;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ===========================
# Logoer
# ===========================
CRANE_CANDIDATES = [
    _Path("assets/kran.png"),
    _Path("Assets/kran.png"),
]
HARBOR_CANDIDATES = [
    _Path("assets/kristiansand_havn.png"),
    _Path("Assets/kristiansand_havn.png"),
    _Path("assets/kristiansand_havn.jpg"),
    _Path("Assets/kristiansand_havn.jpg"),
    _Path("assets/kristiansand_havn.png.png"),
    _Path("Assets/kristiansand_havn.png.png"),
]

def _find_first(paths) -> Optional[str]:
    for p in paths:
        if p.exists():
            return str(p)
    return None

CRANE_PATH = _find_first(CRANE_CANDIDATES)
HARBOR_CRANE_PATH = _find_first(HARBOR_CANDIDATES)

# ===========================
# Norske helligdager (egen beregning – ingen avhengighet til 'holidays'-pakken)
# ===========================
def _easter_sunday(year: int) -> dt.date:
    """Første påskedag via Meeus/Jones/Butcher-algoritmen."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    month = (h + L - 7 * m + 114) // 31
    day = ((h + L - 7 * m + 114) % 31) + 1
    return dt.date(year, month, day)

def norwegian_holidays(year: int) -> Dict[dt.date, str]:
    """Alle norske lov-/helligdager for et gitt år."""
    easter = _easter_sunday(year)
    return {
        dt.date(year, 1, 1): "Første nyttårsdag",
        easter - dt.timedelta(days=3): "Skjærtorsdag",
        easter - dt.timedelta(days=2): "Langfredag",
        easter: "Første påskedag",
        easter + dt.timedelta(days=1): "Andre påskedag",
        dt.date(year, 5, 1): "Arbeidernes dag",
        dt.date(year, 5, 17): "Grunnlovsdag",
        easter + dt.timedelta(days=39): "Kristi himmelfartsdag",
        easter + dt.timedelta(days=49): "Første pinsedag",
        easter + dt.timedelta(days=50): "Andre pinsedag",
        dt.date(year, 12, 25): "Første juledag",
        dt.date(year, 12, 26): "Andre juledag",
    }

_HOLIDAYS_CACHE: Dict[int, Dict[dt.date, str]] = {}

def holiday_name(d: dt.date) -> Optional[str]:
    if d.year not in _HOLIDAYS_CACHE:
        _HOLIDAYS_CACHE[d.year] = norwegian_holidays(d.year)
    return _HOLIDAYS_CACHE[d.year].get(d)

def is_holiday(d: dt.date) -> bool:
    return holiday_name(d) is not None

def is_weekend(d: dt.date) -> bool:
    return d.weekday() >= 5  # 5=lør, 6=søn

def day_type_label(d: Optional[dt.date]) -> str:
    if not isinstance(d, dt.date):
        return ""
    h = holiday_name(d)
    if h:
        return f"Helligdag: {h}"
    wd = d.weekday()
    if wd == 5:
        return "Lørdag"
    if wd == 6:
        return "Søndag"
    return ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"][wd]

# ===========================
# Regler
# ===========================
@dataclass(frozen=True)
class Rules:
    day_start: dt.time
    day_end: dt.time
    ot50_end: dt.time
    night_end: dt.time

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
            if len(s) == 4:
                hh, mm = int(s[:2]), int(s[2:])
            elif len(s) == 3:
                hh, mm = int(s[0]), int(s[1:])
            elif len(s) <= 2:
                hh, mm = int(s), 0
            else:
                return None
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                return dt.time(hh, mm)
        except Exception:
            return None

    return None

def _to_timedelta(x) -> dt.timedelta:
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
            if len(s) == 4:
                hh, mm = int(s[:2]), int(s[2:])
                return dt.timedelta(hours=hh, minutes=mm)
            if len(s) == 3:
                hh, mm = int(s[0]), int(s[1:])
                return dt.timedelta(hours=hh, minutes=mm)
            return dt.timedelta(minutes=int(s))
        except Exception:
            return dt.timedelta(0)

    return dt.timedelta(0)

def combine(d: dt.date, t: dt.time) -> dt.datetime:
    return dt.datetime.combine(d, t)

def hours(td: dt.timedelta) -> float:
    return round(td.total_seconds() / 3600.0, 2)

def fmt_kr(v: float) -> str:
    return f"kr {v:,.2f}".replace(",", "§").replace(".", ",").replace("§", " ")

def fmt_t(v: float) -> str:
    return f"{v:.2f} t".replace(".", ",")

def split_work_by_windows(start_dt: dt.datetime, end_dt: dt.datetime, rules: Rules, day: dt.date) -> Dict[str, dt.timedelta]:
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
        "Overtid 100% Helg": hours(buckets.get("weekend", dt.timedelta(0))),
        "Overtid 133% Helligdag": hours(buckets.get("holiday", dt.timedelta(0))),
        "Spisetid (t)": hours(meal),
        "Ventetid (t)": hours(wait),
        "Fakturerbar Krantid (t)": hours(billed_td),
    }

# ===========================
# Sidebar (innstillinger + satser)
# ===========================
with st.sidebar:
    if HARBOR_CRANE_PATH:
        st.image(HARBOR_CRANE_PATH, use_container_width=True)

    st.markdown("## ⚙️ Tidsvinduer")
    c1, c2 = st.columns(2)
    with c1:
        day_start = st.time_input("Ordinær start", DEFAULT_RULES.day_start, step=dt.timedelta(minutes=15))
        ot50_end = st.time_input("OT 50% slutt", DEFAULT_RULES.ot50_end, step=dt.timedelta(minutes=15))
    with c2:
        day_end = st.time_input("Ordinær slutt", DEFAULT_RULES.day_end, step=dt.timedelta(minutes=15))

    rules = Rules(day_start=day_start, day_end=day_end, ot50_end=ot50_end, night_end=DEFAULT_RULES.night_end)

    st.markdown("---")
    st.markdown("## 💰 Satser (valgfritt)")
    st.caption("Fyll inn kr/t for å regne ut fakturabeløp per rate.")

    sats_ord = st.number_input("Ordinær (kr/t)", min_value=0.0, value=0.0, step=50.0, format="%.2f")
    sats_ot50 = st.number_input("Overtid 50% (kr/t)", min_value=0.0, value=0.0, step=50.0, format="%.2f")
    sats_ot100 = st.number_input("Overtid 100% natt (kr/t)", min_value=0.0, value=0.0, step=50.0, format="%.2f")
    sats_helg = st.number_input("Overtid 100% helg (kr/t)", min_value=0.0, value=0.0, step=50.0, format="%.2f")
    sats_helligdag = st.number_input("Overtid 133% helligdag (kr/t)", min_value=0.0, value=0.0, step=50.0, format="%.2f")

    any_rate = any(v > 0 for v in [sats_ord, sats_ot50, sats_ot100, sats_helg, sats_helligdag])

    st.markdown("---")
    with st.expander("📌 Tips", expanded=False):
        st.markdown(
            "- Klokkeslett kan skrives som **0730**, **730**, **07:30** eller **7.30**.\n"
            "- Hvis slutt er tidligere enn start, tolkes det som **over midnatt**.\n"
            "- Helg → all tid blir **Overtid 100% Helg**.\n"
            "- Helligdag → all tid blir **Overtid 133% Helligdag**.\n"
            "- Fakturerbar = totalt − spisetid − ventetid."
        )
    with st.expander("📅 Norske helligdager i år", expanded=False):
        for d, name in sorted(norwegian_holidays(dt.date.today().year).items()):
            st.markdown(f"- **{d.strftime('%d.%m.%Y')}** ({['Man','Tir','Ons','Tor','Fre','Lør','Søn'][d.weekday()]}) – {name}")

# ===========================
# Header
# ===========================
top_left, top_right = st.columns([0.22, 0.78], vertical_alignment="center")
with top_left:
    if CRANE_PATH:
        st.image(CRANE_PATH, use_container_width=True)
with top_right:
    st.markdown(
        """
<div class="kh-hero">
  <h1>🏗️ KranKalkulator</h1>
  <p>Registrer økter og få automatisk fordeling på rate-kategorier – klart for fakturering.</p>
</div>
""",
        unsafe_allow_html=True,
    )

st.write("")

# ===========================
# SEKSJON 1: Registreringer
# ===========================
default = pd.DataFrame(
    [{
        "Dato": dt.date.today(),
        "Start": "0730",
        "Slutt": "1500",
        "Spisetid (HH:MM)": "0030",
        "Ventetid (HH:MM)": "0000",
        "Kommentar (valgfritt)": "",
    }]
)

st.markdown('<div class="kh-card">', unsafe_allow_html=True)
st.markdown('<div class="kh-section-title"><span>📝 Registrer økter</span></div>', unsafe_allow_html=True)
st.caption("Legg til én rad per økt. Trykk **+** nederst i tabellen for flere rader.")

edited = st.data_editor(
    default,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Dato": st.column_config.DateColumn(format="YYYY-MM-DD", help="Dato for økten"),
        "Start": st.column_config.TextColumn(help="F.eks 0730 / 07:30 / 7.30"),
        "Slutt": st.column_config.TextColumn(help="F.eks 1530 / 15:30 (kan være neste dag)"),
        "Spisetid (HH:MM)": st.column_config.TextColumn(help="F.eks 0030 / 00:30 / 30 (min)"),
        "Ventetid (HH:MM)": st.column_config.TextColumn(help="F.eks 0015 / 00:15 / 15 (min)"),
        "Kommentar (valgfritt)": st.column_config.TextColumn(help="Fri tekst (tas med i eksport)"),
    },
    key="editor",
)
st.markdown('<p class="small-muted">Slutt tidligere enn start tolkes som over midnatt.</p>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ===========================
# Beregn
# ===========================
rows: List[Dict[str, Any]] = []
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
        "Dagtype": day_type_label(_to_date(r.get("Dato"))),
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

# Periodedata + helligdager i perioden
valid_dates = [d for d in out_df.get("Dato", pd.Series(dtype="object")).tolist() if isinstance(d, dt.date)]
period_str = ""
holidays_in_period: List[Tuple[dt.date, str]] = []
if valid_dates:
    mn, mx = min(valid_dates), max(valid_dates)
    period_str = f"{mn.strftime('%d.%m.%Y')}" if mn == mx else f"{mn.strftime('%d.%m.%Y')} – {mx.strftime('%d.%m.%Y')}"
    for d in sorted(set(valid_dates)):
        name = holiday_name(d)
        if name:
            holidays_in_period.append((d, name))

# ===========================
# SEKSJON 2: Oversikt per dag
# ===========================
st.markdown('<div class="kh-card">', unsafe_allow_html=True)
chips_html = ""
if period_str:
    chips_html += f'<span class="kh-chip period">📅 {period_str}</span>'
for d, name in holidays_in_period:
    chips_html += f'<span class="kh-chip hellig">🎉 {d.strftime("%d.%m")} {name}</span>'
st.markdown(
    f'<div class="kh-section-title"><span>📊 Oversikt per dag</span><span class="kh-chips">{chips_html}</span></div>',
    unsafe_allow_html=True,
)

if errors:
    st.markdown(f'<div class="err">⚠️ {errors} rad(er) mangler dato/start/slutt og er utelatt fra oppsummeringen.</div>', unsafe_allow_html=True)

display_cols_map = {
    "Dato": "Dato",
    "Dagtype": "Dagtype",
    "Start": "Start",
    "Slutt": "Slutt",
    "Totalt timer": "Totalt",
    "Ordinær (07:30-15:00)": "Ordinær",
    "Overtid 50% (15:00-21:00)": "OT 50%",
    "Overtid 100% (21:00-07:30)": "OT 100% natt",
    "Overtid 100% Helg": "OT 100% helg",
    "Overtid 133% Helligdag": "OT 133% hellig",
    "Spisetid (t)": "Spise",
    "Ventetid (t)": "Vent",
    "Fakturerbar Krantid (t)": "Fakturerbar",
    "Kommentar": "Kommentar",
}
existing = [c for c in display_cols_map.keys() if c in out_df.columns]
display_df = out_df[existing].rename(columns=display_cols_map)

st.dataframe(display_df, use_container_width=True, hide_index=True, height=min(360, 60 + 38 * max(len(display_df), 1)))
st.markdown("</div>", unsafe_allow_html=True)

# ===========================
# SEKSJON 3: Fakturagrunnlag
# ===========================
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
existing_numeric = [c for c in numeric_cols if c in out_df.columns]
totals = out_df[existing_numeric].sum(numeric_only=True) if existing_numeric else pd.Series(dtype=float)

t_ord = float(totals.get("Ordinær (07:30-15:00)", 0) or 0)
t_ot50 = float(totals.get("Overtid 50% (15:00-21:00)", 0) or 0)
t_ot100 = float(totals.get("Overtid 100% (21:00-07:30)", 0) or 0)
t_helg = float(totals.get("Overtid 100% Helg", 0) or 0)
t_hellig = float(totals.get("Overtid 133% Helligdag", 0) or 0)
t_spise = float(totals.get("Spisetid (t)", 0) or 0)
t_vent = float(totals.get("Ventetid (t)", 0) or 0)
t_fakt = float(totals.get("Fakturerbar Krantid (t)", 0) or 0)
t_totalt = float(totals.get("Totalt timer", 0) or 0)

categories: List[Tuple[str, float, float]] = [
    ("Ordinær (07:30–15:00)", t_ord, sats_ord),
    ("Overtid 50% (15:00–21:00)", t_ot50, sats_ot50),
    ("Overtid 100% natt (21:00–07:30)", t_ot100, sats_ot100),
    ("Overtid 100% helg", t_helg, sats_helg),
    ("Overtid 133% helligdag", t_hellig, sats_helligdag),
]

sum_kategorier = sum(h for _, h, _ in categories)
sum_belop = sum(h * s for _, h, s in categories)

st.markdown('<div class="kh-card">', unsafe_allow_html=True)
chips_html = ""
if period_str:
    chips_html += f'<span class="kh-chip period">📅 {period_str}</span>'
for d, name in holidays_in_period:
    chips_html += f'<span class="kh-chip hellig">🎉 {d.strftime("%d.%m")} {name}</span>'
st.markdown(
    f'<div class="kh-section-title"><span>💰 Fakturagrunnlag</span><span class="kh-chips">{chips_html}</span></div>',
    unsafe_allow_html=True,
)

if any_rate:
    hero_html = f"""
<div class="kh-invoice-hero">
  <div class="block">
    <div class="label">Fakturerbar krantid</div>
    <div class="value">{t_fakt:.2f}<span class="unit">timer</span></div>
    <div class="sub">Totalt arbeidet: {t_totalt:.2f} t · Trekk: {(t_spise + t_vent):.2f} t</div>
  </div>
  <div class="divider"></div>
  <div class="block">
    <div class="label">Totalbeløp</div>
    <div class="value">{fmt_kr(sum_belop)}</div>
    <div class="sub">Basert på satser i sidebaren · {sum_kategorier:.2f} t fakturert</div>
  </div>
</div>
"""
else:
    hero_html = f"""
<div class="kh-invoice-hero">
  <div class="block">
    <div class="label">Fakturerbar krantid</div>
    <div class="value">{t_fakt:.2f}<span class="unit">timer</span></div>
    <div class="sub">Totalt arbeidet: {t_totalt:.2f} t · Trekk: {(t_spise + t_vent):.2f} t</div>
  </div>
  <div class="divider"></div>
  <div class="block">
    <div class="label">Totalt i kategorier</div>
    <div class="value">{sum_kategorier:.2f}<span class="unit">timer</span></div>
    <div class="sub">Fyll inn satser i sidebaren for å se fakturabeløp</div>
  </div>
</div>
"""
st.markdown(hero_html, unsafe_allow_html=True)

# Rate-tabell
header_cols = ['<div class="kh-rate-name">Kategori</div>',
               '<div class="kh-right">Timer</div>',
               '<div class="kh-right">Sats</div>',
               '<div class="kh-right">Beløp</div>']
rate_html = '<div class="kh-rate-table">'
rate_html += '<div class="kh-rate-row header">' + "".join(header_cols) + '</div>'

for name, h, s in categories:
    amount = h * s
    zero_cls = " zero" if h == 0 else ""
    sats_cell = fmt_kr(s) if s > 0 else '<span class="kh-muted-val">–</span>'
    amount_cell = fmt_kr(amount) if s > 0 else '<span class="kh-muted-val">–</span>'
    rate_html += (
        f'<div class="kh-rate-row{zero_cls}">'
        f'<div class="kh-rate-name">{name}</div>'
        f'<div class="kh-right">{fmt_t(h)}</div>'
        f'<div class="kh-right kh-muted-val">{sats_cell}</div>'
        f'<div class="kh-right">{amount_cell}</div>'
        f'</div>'
    )

total_amount_cell = fmt_kr(sum_belop) if any_rate else '<span class="kh-muted-val">–</span>'
rate_html += (
    f'<div class="kh-rate-row total">'
    f'<div>Sum kategorier</div>'
    f'<div class="kh-right">{fmt_t(sum_kategorier)}</div>'
    f'<div></div>'
    f'<div class="kh-right">{total_amount_cell}</div>'
    f'</div>'
)
rate_html += '</div>'
st.markdown(rate_html, unsafe_allow_html=True)

# Trekk
st.markdown(
    f"""
<div class="kh-deduct-row">
  <div class="kh-deduct-item">
    <div class="lbl">🍽️ Spisetid (ikke fakturert)</div>
    <div class="val">{fmt_t(t_spise)}</div>
  </div>
  <div class="kh-deduct-item">
    <div class="lbl">⏸️ Ventetid (ikke fakturert)</div>
    <div class="val">{fmt_t(t_vent)}</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Kopi-klar tekstblokk
with st.expander("📋 Kopi-klar oppsummering (til e-post/faktura)"):
    lines = []
    lines.append("FAKTURAGRUNNLAG – KRANKALKULATOR")
    lines.append("=" * 42)
    if period_str:
        lines.append(f"Periode:              {period_str}")
    lines.append(f"Fakturerbar krantid:  {t_fakt:>7.2f} t")
    if holidays_in_period:
        lines.append("")
        lines.append("Helligdager i perioden:")
        for d, name in holidays_in_period:
            lines.append(f"  {d.strftime('%d.%m.%Y')} – {name}")
    lines.append("")
    lines.append("Fordeling på rater:")
    lines.append(f"  Ordinær              {t_ord:>7.2f} t")
    lines.append(f"  Overtid 50%          {t_ot50:>7.2f} t")
    lines.append(f"  Overtid 100% natt    {t_ot100:>7.2f} t")
    lines.append(f"  Overtid 100% helg    {t_helg:>7.2f} t")
    lines.append(f"  Overtid 133% hellig  {t_hellig:>7.2f} t")
    lines.append(f"  {'─' * 32}")
    lines.append(f"  Sum kategorier       {sum_kategorier:>7.2f} t")
    lines.append("")
    lines.append("Trekk (ikke fakturert):")
    lines.append(f"  Spisetid             {t_spise:>7.2f} t")
    lines.append(f"  Ventetid             {t_vent:>7.2f} t")
    if any_rate:
        lines.append("")
        lines.append("Fakturabeløp per rate:")
        for name, h, s in categories:
            if s > 0:
                lines.append(f"  {name:<32} {h:>6.2f} t × {s:>8.2f} = {h*s:>12.2f} kr")
        lines.append(f"  {'─' * 60}")
        lines.append(f"  SUM:                                                     {sum_belop:>12.2f} kr")
    summary_text = "\n".join(lines)
    st.code(summary_text, language="text")

st.markdown("</div>", unsafe_allow_html=True)

# ===========================
# SEKSJON 4: Eksport
# ===========================
st.markdown('<div class="kh-card">', unsafe_allow_html=True)
st.markdown('<div class="kh-section-title"><span>📥 Eksport</span></div>', unsafe_allow_html=True)

e1, e2 = st.columns(2)
with e1:
    st.download_button(
        "⬇️ Last ned CSV",
        data=out_df.to_csv(index=False).encode("utf-8"),
        file_name=f"krankalkulator_{dt.date.today().isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with e2:
    try:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            out_df.to_excel(writer, sheet_name="Registreringer", index=False)

            summary_rows = [
                ("Periode", period_str or "–"),
                ("", ""),
                ("Fakturerbar krantid (t)", round(t_fakt, 2)),
                ("Totalt arbeidet (t)", round(t_totalt, 2)),
                ("", ""),
                ("Ordinær (07:30-15:00) (t)", round(t_ord, 2)),
                ("Overtid 50% (15:00-21:00) (t)", round(t_ot50, 2)),
                ("Overtid 100% natt (21:00-07:30) (t)", round(t_ot100, 2)),
                ("Overtid 100% helg (t)", round(t_helg, 2)),
                ("Overtid 133% helligdag (t)", round(t_hellig, 2)),
                ("", ""),
                ("Spisetid trukket fra (t)", round(t_spise, 2)),
                ("Ventetid trukket fra (t)", round(t_vent, 2)),
            ]

            if holidays_in_period:
                summary_rows.append(("", ""))
                summary_rows.append(("— Helligdager i perioden —", ""))
                for d, name in holidays_in_period:
                    summary_rows.append((d.strftime("%d.%m.%Y"), name))

            if any_rate:
                summary_rows.append(("", ""))
                summary_rows.append(("— Fakturabeløp —", ""))
                for name, h, s in categories:
                    if s > 0:
                        summary_rows.append((f"{name} (kr)", round(h * s, 2)))
                summary_rows.append(("Totalbeløp (kr)", round(sum_belop, 2)))

            pd.DataFrame(summary_rows, columns=["Post", "Verdi"]).to_excel(
                writer, sheet_name="Oppsummering", index=False
            )
        st.download_button(
            "⬇️ Last ned Excel",
            data=buf.getvalue(),
            file_name=f"krankalkulator_{dt.date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except ModuleNotFoundError:
        st.info("Installer `openpyxl` i requirements.txt for å aktivere Excel-eksport.")

st.markdown("</div>", unsafe_allow_html=True)

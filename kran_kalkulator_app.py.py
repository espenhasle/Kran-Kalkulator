import streamlit as st
import pandas as pd
import datetime as dt
import holidays
from dataclasses import dataclass
from typing import Optional, Dict, Any

# ---------------------------
# Sideoppsett + "havnefarger"
# ---------------------------
# ---------------------------
# Logo (legg bildet i repoet, f.eks. /assets/kristiansand_havn.png)
# ---------------------------
from pathlib import Path as _Path

LOGO_CANDIDATES = [
    _Path("assets/kristiansand_havn.png"),
    _Path("assets/kristiansand_havn.jpg"),
    _Path("kristiansand_havn.png"),
    _Path("kristiansand_havn.jpg"),
]

def _find_logo():
    for p in LOGO_CANDIDATES:
        if p.exists():
            return str(p)
    return None

LOGO_PATH = _find_logo()

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
# Helligdager (automatisk, fremtidssikkert)
# Bruker python-pakken "holidays" (Norge).
# ---------------------------
NO_HOLIDAYS = holidays.country_holidays("NO")

def is_holiday(d: dt.date) -> bool:
    # holidays støtter mange år, men bygger opp dynamisk ved behov
    return d in NO_HOLIDAYS

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
    """Aksepterer:
    - dt.time / dt.datetime
    - 'HH:MM'
    - 'HHMM' (f.eks. 0730)
    - 'HMM' (f.eks. 730)
    - 'H.MM' / 'HH.MM' / 'H,MM' / 'HH,MM' (f.eks. 7.30)
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

    # Normaliser separatorer
    s = s.replace(".", ":").replace(",", ":")

    # 1) HH:MM
    if ":" in s:
        try:
            hh, mm = s.split(":")
            return dt.time(int(hh), int(mm))
        except Exception:
            return None

    # 2) Bare tall: HHMM eller HMM
    if s.isdigit():
        try:
            if len(s) == 4:      # 0730
                hh, mm = int(s[:2]), int(s[2:])
            elif len(s) == 3:    # 730
                hh, mm = int(s[0]), int(s[1:])
            elif len(s) <= 2:    # 7 eller 07 -> tolkes som hel time
                hh, mm = int(s), 0
            else:
                return None
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                return dt.time(hh, mm)
        except Exception:
            return None

    return None

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

import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(page_title="KranKalkulator", layout="wide")

# Helligdager hentet fra Excel-arket (området Y55:Y92)
HOLIDAYS = set(['2025-01-01', '2025-04-13', '2025-04-17', '2025-04-18', '2025-04-20', '2025-04-21', '2025-05-01', '2025-05-17', '2025-05-29', '2025-06-08', '2025-06-09', '2025-12-25', '2025-12-26', '2026-01-01', '2026-03-29', '2026-04-02', '2026-04-03', '2026-04-05', '2026-04-06', '2026-05-01', '2026-05-14', '2026-05-17', '2026-05-24', '2026-05-25', '2026-12-25', '2026-12-26', '2027-01-01', '2027-03-21', '2027-03-25', '2027-03-26', '2027-03-28', '2027-03-29', '2027-05-01', '2027-05-06', '2027-05-16', '2027-05-17', '2027-12-25', '2027-12-26'])

def parse_time(val):
    """
    Accepts:
      - datetime.time
      - 'HH:MM' or 'HH:MM:SS'
      - pandas Timestamp/time-like
    Returns datetime.time or None
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, dt.time):
        return val
    if isinstance(val, dt.datetime):
        return val.time()
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return dt.datetime.strptime(s, fmt).time()
            except ValueError:
                pass
    return None

def parse_duration(val):
    """
    Accepts:
      - 'H:MM' / 'HH:MM' / 'HH:MM:SS'
      - float (hours)
      - datetime.timedelta
    Returns timedelta (>=0)
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return dt.timedelta(0)
    if isinstance(val, dt.timedelta):
        return max(val, dt.timedelta(0))
    if isinstance(val, (int, float)):
        # interpret as hours
        return dt.timedelta(hours=float(val))
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return dt.timedelta(0)
        parts = s.split(":")
        try:
            if len(parts) == 2:
                h, m = map(int, parts)
                return dt.timedelta(hours=h, minutes=m)
            if len(parts) == 3:
                h, m, sec = map(int, parts)
                return dt.timedelta(hours=h, minutes=m, seconds=sec)
        except ValueError:
            return dt.timedelta(0)
    return dt.timedelta(0)

def td_hours(td: dt.timedelta) -> float:
    return td.total_seconds() / 3600.0

def compute_row(date_val, start_t, end_t, meal_td, wait_td):
    # Basic validation
    if pd.isna(date_val) or start_t is None or end_t is None:
        return {}

    if isinstance(date_val, dt.datetime):
        d = date_val.date()
    elif isinstance(date_val, dt.date):
        d = date_val
    else:
        try:
            d = pd.to_datetime(date_val).date()
        except Exception:
            return {}

    start_dt = dt.datetime.combine(d, start_t)
    end_dt = dt.datetime.combine(d, end_t)
    if end_dt < start_dt:
        end_dt += dt.timedelta(days=1)

    total = end_dt - start_dt

    is_holiday = d.isoformat() in HOLIDAYS
    weekday = d.isoweekday()  # Mon=1..Sun=7
    is_weekend = weekday >= 6

    # Time windows (same day, but we will clip on timeline that may extend to next day)
    def clip(window_start: dt.time, window_end: dt.time):
        ws = dt.datetime.combine(d, window_start)
        we = dt.datetime.combine(d, window_end)
        if we <= ws:
            we += dt.timedelta(days=1)
        s = max(start_dt, ws)
        e = min(end_dt, we)
        return max(dt.timedelta(0), e - s)

    # Excel-logikken:
    # Ordinær: 07:30-15:00 kun hverdager og ikke helligdag
    # Overtid 50%: 15:00-21:00 kun hverdager
    # Overtid 100% natt: resten (total - ordinær - 50%) kun hverdager og ikke helligdag
    # Overtid 100% helg: hele totalen hvis helg og ikke helligdag
    # Overtid 133% helligdag: hele totalen hvis helligdag
    regular = dt.timedelta(0)
    ot50 = dt.timedelta(0)
    ot100_night = dt.timedelta(0)
    ot100_weekend = dt.timedelta(0)
    ot133_holiday = dt.timedelta(0)

    if is_holiday:
        ot133_holiday = total
    elif is_weekend:
        ot100_weekend = total
    else:
        regular = clip(dt.time(7,30), dt.time(15,0))
        ot50 = clip(dt.time(15,0), dt.time(21,0))
        # Remaining time = natt (21:00-07:30) + evt andre rester ved over-midnatt
        ot100_night = max(dt.timedelta(0), total - regular - ot50)

    billable = max(dt.timedelta(0), total - meal_td - wait_td)

    return {
        "Dag": d.strftime("%A"),
        "Totalt timer": td_hours(total),
        "Ordinær (07:30-15:00)": td_hours(regular),
        "Overtid 50% (15:00-21:00)": td_hours(ot50),
        "Overtid 100% (21:00-07:30)": td_hours(ot100_night),
        "Overtid 100% Helg": td_hours(ot100_weekend),
        "Overtid 133% Helligdag": td_hours(ot133_holiday),
        "Spisetid (t)": td_hours(meal_td),
        "Ventetid (t)": td_hours(wait_td),
        "Fakturerbar Krantid (t)": td_hours(billable),
        "Helligdag?": "Ja" if is_holiday else "Nei",
    }

st.title("KranKalkulator – app")

st.markdown(
    "Legg inn dato og tidsrom, så får du automatisk fordeling på ordinær/OT og fakturerbar krantid."
)

default = pd.DataFrame(
    [
        {
            "Dato": dt.date.today(),
            "Start": "07:30",
            "Slutt": "15:00",
            "Spisetid": "01:00",
            "Ventetid": "00:00",
        }
    ]
)

st.subheader("Registreringer")
edited = st.data_editor(
    default,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Dato": st.column_config.DateColumn(format="YYYY-MM-DD"),
        "Start": st.column_config.TextColumn(help="HH:MM (24t)"),
        "Slutt": st.column_config.TextColumn(help="HH:MM (24t)"),
        "Spisetid": st.column_config.TextColumn(help="Varighet, f.eks 01:00"),
        "Ventetid": st.column_config.TextColumn(help="Varighet, f.eks 00:30"),
    },
)

# Compute outputs
rows = []
for _, r in edited.iterrows():
    date_val = r.get("Dato")
    start_t = parse_time(r.get("Start"))
    end_t = parse_time(r.get("Slutt"))
    meal_td = parse_duration(r.get("Spisetid"))
    wait_td = parse_duration(r.get("Ventetid"))
    out = compute_row(date_val, start_t, end_t, meal_td, wait_td)
    if out:
        rows.append({
            "Dato": pd.to_datetime(date_val).date() if not pd.isna(date_val) else None,
            "Start": start_t.strftime("%H:%M") if start_t else None,
            "Slutt": end_t.strftime("%H:%M") if end_t else None,
            **out
        })
    else:
        rows.append({
            "Dato": date_val,
            "Start": r.get("Start"),
            "Slutt": r.get("Slutt"),
        })

out_df = pd.DataFrame(rows)

st.subheader("Beregning")
st.dataframe(out_df, use_container_width=True)

# Totals
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
totals = out_df[numeric_cols].sum(numeric_only=True).to_frame("Sum (t)").T
st.subheader("Summer")
st.dataframe(totals, use_container_width=True)

# Export
st.download_button(
    "Last ned som CSV",
    data=out_df.to_csv(index=False).encode("utf-8"),
    file_name="kran_kalkulator.csv",
    mime="text/csv",
)

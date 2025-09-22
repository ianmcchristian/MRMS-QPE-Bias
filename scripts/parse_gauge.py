#!/usr/bin/env python3
from pathlib import Path
import re
import pandas as pd

# Default file to use if none is provided by callers
FNAME = "/qvs-storage/VMRMS/2025/08/gauge/ALLSETS/GAUGE_1H_MRMS_QC.20250831.230000"


# Helper Functions
def infer_file_time_utc(fname: str) -> pd.Timestamp:
    """Parse ...YYYYMMDD.HH0000 from filename and return tz-aware UTC timestamp."""
    m = re.search(r'\.(\d{8})\.(\d{2})0000$', Path(fname).name)
    if not m:
        raise ValueError(f"Filename must end with .YYYYMMDD.HH0000: {fname}")
    ymd, hh = m.group(1), m.group(2)
    return pd.Timestamp(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:]), int(hh), 0, 0, tz='UTC')

def line_is_data(s: str) -> bool:
    """Keep only likely data lines."""
    if not s or s.startswith("#"):
        return False
    # toss obvious headers/explanations
    bad_keys = ("G_ID", "Lat", "Lon", "T_Shift", "G_Value", "QC_Flag", "Gauge station ID")
    return not any(k in s for k in bad_keys)

# Main Parsing Function
def parse_gauge_file_to_table1(fname: str, qc_keep=None) -> pd.DataFrame:
    """
    Return DataFrame with columns:
      Obs ID | Obs value | Lat. | Long. | Time | Q3Rad | 2m_temp | N
    """
    base = infer_file_time_utc(fname)

    recs = []
    with open(fname, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if not line_is_data(s):
                continue
            parts = s.split()
            if len(parts) < 6:
                continue  # skip malformed
            gid, lat, lon, tshift, gval, qc = parts[:6]
            try:
                recs.append({
                    "G_ID": gid,
                    "Lat": float(lat),
                    "Lon": float(lon),
                    "T_Shift": int(float(tshift)),
                    "G_Value": float(gval),
                    "QC_Flag": int(float(qc)),
                })
            except Exception:
                continue  # skip weird rows

    if not recs:
        raise ValueError(f"No valid rows parsed from {fname}")

    df = pd.DataFrame(recs)

    if qc_keep is not None:
        df = df[df["QC_Flag"].isin(set(qc_keep))]

    df["Time"] = base + pd.to_timedelta(df["T_Shift"], unit="m")

    # Table-1 schema
    out = pd.DataFrame({
        "Obs ID":    df["G_ID"].astype("string"),
        "Obs value": df["G_Value"].astype(float),
        "Lat.":      df["Lat"].astype(float),
        "Long.":     df["Lon"].astype(float),
        "Time":      df["Time"],          # tz-aware UTC
        "Q3Rad":     pd.NA,               # fill later from radar
        "2m_temp":   pd.NA,               # fill later from met data
        "N":         pd.NA,               # fill later (neighbors, etc.)
    }).reset_index(drop=True)

    return out

if __name__ == "__main__":
    df = parse_gauge_file_to_table1(FNAME, qc_keep=None)  # or qc_keep={0}
    print(f"Parsed rows: {len(df)}")

    # Filter out zero-precip rows
    nonzero = df[df["Obs value"] > 0]

    print("\nFirst 10 rows with non-zero Obs value:")
    if nonzero.empty:
        print("No non-zero observations found in this file.")
    else:
        print(nonzero.head(10).to_string(index=False))


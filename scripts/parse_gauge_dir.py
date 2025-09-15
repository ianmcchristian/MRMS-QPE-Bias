import pandas as pd

# path to a single gauge file (adjust the YYYYMMDD.HH0000 part)
fname = "/qvs-storage/VMRMS/2025/08/gauge/ALLSETS/GAUGE_1H_MRMS_QC.20250831.230000"

# columns we expect
cols = ["G_ID", "lat", "lon", "T_shift", "G_Value", "QC_Flag"]

df = pd.read_csv(
    fname,
    delim_whitespace=True,  # split on spaces/tabs
    comment="#",            # ignore header lines that start with #
    names=cols,
    usecols=cols
)

print(df.head())
print(df.dtypes)
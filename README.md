# MRMS-QPE-Bias

Build a tabular dataset pairing in situ gauge observations with MRMS outputs for bias/stat analysis.

## Goal
Create a new dataset enabling statistical analyses of MRMS biases. Each row pairs a gauge/in-situ observation with collocated MRMS outputs at the valid time/location.

### Prototype schema
| Obs ID | Obs value (mm) | Lat | Long | Time (UTC) | MRMS fields... |
|-------:|----------------:|----:|-----:|------------|----------------|
| G_ID   | G_Value         |LAT  | LON  | from file  | Q3Rad, 2m_temp, ... |

- **Obs ID**: station identifier (CoCoRaHS, MADIS/HADS, etc.)
- **Time**: use UTC/Zulu; convert CST = UTC−6, CDT = UTC−5

### Gauge data source (NSSL network)
`/qvs-storage/{YEAR}/{MONTH}/gauge/ALLSETS/`
files: `GAUGE_1H_MRMS_QC.YYYYMMDD.HH0000`

Columns of interest: `G_ID, LAT, LON, T_shift (min), G_Value (mm), QC_Flag`
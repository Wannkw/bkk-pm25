"""
Bangkok PM2.5: when is it actually bad, and when is it OK to go outside?

Reads the CSVs from fetch_data.py, prints the numbers I quote in the README
and saves the charts into charts/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).parent
CHARTS = ROOT / "charts"
CHARTS.mkdir(exist_ok=True)

TH_STANDARD = 37.5   # Thai 24h standard since June 2023 (was 50 before)
WHO_GUIDE = 15       # WHO 2021 24h guideline

plt.rcParams.update({
    "figure.dpi": 120,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 10,
})

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load(city):
    df = pd.read_csv(ROOT / "data" / f"{city}_hourly.csv", parse_dates=["time"])
    return df.set_index("time")["pm25"]


bkk = load("bangkok")
cnx = load("chiang_mai")

bkk_daily = bkk.resample("D").mean()
cnx_daily = cnx.resample("D").mean()


# dry season runs Nov -> Apr, so label each day with the season it belongs to
# e.g. Nov 2024 - Apr 2025 = "2024/25"
def season_label(ts):
    start = ts.year if ts.month >= 11 else ts.year - 1
    return f"{start}/{str(start + 1)[-2:]}"


is_dry = bkk_daily.index.month.isin([11, 12, 1, 2, 3, 4])
dry = bkk_daily[is_dry]
dry_seasons = dry.groupby(dry.index.map(season_label))

print("=== Bangkok, days above Thai standard (37.5) per dry season ===")
summary = pd.DataFrame({
    "days": dry_seasons.size(),
    "days_over_th": dry_seasons.apply(lambda s: (s > TH_STANDARD).sum()),
    "days_over_who": dry_seasons.apply(lambda s: (s > WHO_GUIDE).sum()),
    "worst_day": dry_seasons.max().round(1),
})
print(summary)
print("note: 2022/23 only has Jan-Apr 2023, so it's a partial season\n")


# --- 1. calendar heatmap: monthly mean, year x month ----------------------
monthly = bkk.resample("ME").mean()
grid = monthly.groupby([monthly.index.year, monthly.index.month]).first().unstack()

fig, ax = plt.subplots(figsize=(9, 3))
im = ax.imshow(grid.values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=60)
ax.set_xticks(range(12), MONTHS)
ax.set_yticks(range(len(grid)), grid.index)
ax.grid(False)
for (i, j), v in pd.DataFrame(grid.values).stack().items():
    if pd.isna(v):  # months that haven't happened yet
        continue
    ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8,
            color="white" if v > 40 else "black")
fig.colorbar(im, ax=ax, label="µg/m³")
ax.set_title("Bangkok monthly average PM2.5")
fig.tight_layout()
fig.savefig(CHARTS / "01_monthly_heatmap.png")
plt.close(fig)


# --- 2. hour of day, dry vs wet season ------------------------------------
hourly_dry = bkk[bkk.index.month.isin([11, 12, 1, 2, 3, 4])]
hourly_wet = bkk[~bkk.index.month.isin([11, 12, 1, 2, 3, 4])]
by_hour_dry = hourly_dry.groupby(hourly_dry.index.hour).median()
by_hour_wet = hourly_wet.groupby(hourly_wet.index.hour).median()

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(by_hour_dry.index, by_hour_dry.values, marker="o", ms=3, label="Dry season (Nov-Apr)", color="#c0392b")
ax.plot(by_hour_wet.index, by_hour_wet.values, marker="o", ms=3, label="Wet season (May-Oct)", color="#2e86c1")
ax.axhline(TH_STANDARD, ls="--", color="gray", lw=1)
ax.text(0, TH_STANDARD + 1, "Thai 24h standard", color="gray", fontsize=8)
ax.set_xticks(range(0, 24, 2))
ax.set_xlabel("Hour of day (Bangkok time)")
ax.set_ylabel("Median PM2.5 (µg/m³)")
ax.set_title("Bangkok PM2.5 by hour of day")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(CHARTS / "02_hour_of_day.png")
plt.close(fig)

print("=== Dry season, median PM2.5 by hour ===")
print(f"lowest  : {by_hour_dry.idxmin():02d}:00 -> {by_hour_dry.min():.1f}")
print(f"highest : {by_hour_dry.idxmax():02d}:00 -> {by_hour_dry.max():.1f}")
print(f"06:00 vs 18:00 : {by_hour_dry[6]:.1f} vs {by_hour_dry[18]:.1f}\n")


# --- 3. weekday vs weekend -------------------------------------------------
dry_days = bkk_daily[is_dry]
wd = dry_days.groupby(dry_days.index.dayofweek).median()
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.bar(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], wd.values,
       color=["#7f8c8d"] * 5 + ["#16a085"] * 2)
ax.set_ylabel("Median daily PM2.5 (µg/m³)")
ax.set_title("Dry season: does the weekend help?")
fig.tight_layout()
fig.savefig(CHARTS / "03_weekday.png")
plt.close(fig)

print("=== Dry season, median daily PM2.5 by weekday ===")
print(wd.round(1).rename(index=dict(enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))).to_string())
print()


# --- 4. Bangkok vs Chiang Mai ---------------------------------------------
m_bkk = bkk_daily.groupby(bkk_daily.index.month).mean()
m_cnx = cnx_daily.groupby(cnx_daily.index.month).mean()
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(MONTHS, m_bkk.values, marker="o", label="Bangkok", color="#c0392b")
ax.plot(MONTHS, m_cnx.values, marker="o", label="Chiang Mai", color="#8e44ad")
ax.set_ylabel("Average PM2.5 (µg/m³)")
ax.set_title("Different cities, different bad seasons")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(CHARTS / "04_bkk_vs_cnx.png")
plt.close(fig)

print("=== Peak month ===")
print(f"Bangkok   : {MONTHS[m_bkk.idxmax() - 1]} ({m_bkk.max():.1f})")
print(f"Chiang Mai: {MONTHS[m_cnx.idxmax() - 1]} ({m_cnx.max():.1f})")

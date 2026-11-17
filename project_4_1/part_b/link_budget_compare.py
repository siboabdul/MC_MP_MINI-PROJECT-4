#!/usr/bin/env python3
"""Mini Project 4.1 (Part B) - LPWAN link-budget and battery-life comparison.

Standard library only. Writes results/link_budget_results.json.
No plotting here - see make_figure.py.
"""
import json
import math
from pathlib import Path

TX_POWER_DBM      = {"NB-IoT": 23.0, "LTE-M (CE Mode B)": 23.0, "LoRaWAN SF12": 14.0}
RX_SENS_DBM       = {"NB-IoT": -129.0, "LTE-M (CE Mode B)": -125.0, "LoRaWAN SF12": -137.0}
TX_CURRENT_MA     = {"NB-IoT": 220.0, "LTE-M (CE Mode B)": 380.0, "LoRaWAN SF12": 44.0}
TX_TIME_S         = {"NB-IoT": 1.2, "LTE-M (CE Mode B)": 2.4, "LoRaWAN SF12": 1.5}
SLEEP_CURRENT_MA  = {"NB-IoT": 0.005, "LTE-M (CE Mode B)": 0.005, "LoRaWAN SF12": 0.0015}

D_KM, D0_KM, PL_D0_DB = 8.0, 1.0, 91.5
N_EXP = 3.5
BATTERY_MAH = 19000.0
TARGET_YEARS = 5.0
INTERVAL_S = 30 * 60


def path_loss(d_km: float) -> float:
    return PL_D0_DB + 10.0 * N_EXP * math.log10(d_km / D0_KM)


def mcl(tx_dbm: float, rx_dbm: float) -> float:
    return tx_dbm - rx_dbm


def battery_years(tx_ma: float, tx_s: float, sleep_ma: float) -> float:
    mah_tx    = tx_ma * (tx_s / 3600.0)
    mah_sleep = sleep_ma * ((INTERVAL_S - tx_s) / 3600.0)
    cycles_per_year = 365.25 * 24 * 3600 / INTERVAL_S
    return BATTERY_MAH / ((mah_tx + mah_sleep) * cycles_per_year)


def main() -> None:
    pl = path_loss(D_KM)
    rows = []
    for tech in TX_POWER_DBM:
        m = mcl(TX_POWER_DBM[tech], RX_SENS_DBM[tech])
        margin = m - pl
        years  = battery_years(TX_CURRENT_MA[tech], TX_TIME_S[tech], SLEEP_CURRENT_MA[tech])
        rows.append({
            "technology": tech,
            "tx_dbm": TX_POWER_DBM[tech],
            "rx_dbm": RX_SENS_DBM[tech],
            "mcl_db": round(m, 2),
            "path_loss_db": round(pl, 2),
            "margin_db": round(margin, 2),
            "coverage_ok": margin > 0,
            "battery_years": round(years, 2),
            "battery_ok": years >= TARGET_YEARS,
        })

    print(f"Scenario: {D_KM:g} km range, PL(d0)={PL_D0_DB} dB @ {D0_KM:g} km, n={N_EXP}")
    print(f"Path loss at {D_KM:g} km = {pl:.2f} dB\n")
    header = f"{'Technology':<22}{'MCL(dB)':>9}{'Margin(dB)':>12}{'Battery(yr)':>13}{'Cov':>6}{'Batt':>6}"
    print(header); print("-" * len(header))
    for r in rows:
        print(f"{r['technology']:<22}{r['mcl_db']:>9.1f}{r['margin_db']:>12.1f}"
              f"{r['battery_years']:>13.2f}"
              f"{'OK' if r['coverage_ok'] else 'X':>6}"
              f"{'OK' if r['battery_ok'] else 'X':>6}")

    out_dir = Path(__file__).resolve().parents[2] / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "link_budget_results.json").write_text(json.dumps({
        "scenario": {"distance_km": D_KM, "pl_d0_db": PL_D0_DB,
                     "path_loss_exponent": N_EXP, "battery_mah": BATTERY_MAH,
                     "target_years": TARGET_YEARS, "interval_s": INTERVAL_S},
        "path_loss_db": round(pl, 2),
        "rows": rows,
    }, indent=2))
    print(f"\nResults written to {out_dir/'link_budget_results.json'}")
    print(f"Now run:  python make_figure.py")


if __name__ == "__main__":
    main()
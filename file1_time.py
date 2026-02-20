# ----------------------------------------------------------
# FIRE MODEL ENGINE
# Gasoline Pool Fire – Seat of Fire (R = 0)
# Returns DataFrame + Key Outputs
# ----------------------------------------------------------

import numpy as np
import pandas as pd
import math


def run_pool_fire_model(fuel, m_fuel, D, burning_rate=0.055, lhv_mj=43.7, combustion_efficiency=0.98):

    # ==========================================================
    # FUEL PROPERTIES
    # ==========================================================
    m_dot_area = burning_rate      # kg/m²·s
    LHV = lhv_mj * 1e6             # Convert MJ/kg to J/kg
    eta = combustion_efficiency    # Combustion efficiency

    # Seat of fire
    R = 0.0

    # ==========================================================
    # PIECEWISE CORRELATIONS
    # ==========================================================

    def chi_r(D):
        if D <= 5:
            return 0.25
        elif D < 30:
            return 0.25 - 0.20 * (D - 5) / 25
        else:
            return 0.05

    def kappa_f(D):
        if D <= 5:
            return 0.04
        elif D < 30:
            return 0.04 + 0.08 * (D - 5) / 25
        else:
            return 0.12

    def tau_f(D):
        return math.exp(-kappa_f(D) * (2 * D))

    def H_min(D):
        if D <= 5:
            return 0.25 * D
        elif D < 30:
            return 0.25 * D + 0.25 * (D - 5)
        else:
            return 0.5 * D

    def kappa_atm(R):
        if R == 0:
            return 0.0
        elif R <= 10:
            return 0.04
        elif R < 50:
            return 0.04 + 0.002 * (R - 10)
        else:
            return 0.12

    def tau_atm(R):
        return math.exp(-kappa_atm(R) * R)

    # ==========================================================
    # CORE CALCULATIONS
    # ==========================================================

    A_pool = math.pi * D**2 / 4.0
    t_burn = m_fuel / (m_dot_area * A_pool)
    time = np.linspace(0, t_burn, 300)

    rows = []

    for t in time:

        f = 4 * (t / t_burn) * (1 - t / t_burn)
        f = max(0.0, f)

        HRR = m_dot_area * A_pool * LHV * eta * f
        HRR_kW = HRR / 1000.0

        H_corr = 0.235 * HRR_kW**0.4 - 1.02 * D
        H = max(H_corr, H_min(D))

        A_proj = D * H
        E_surface = (chi_r(D) * HRR / A_proj) * tau_f(D)

        denom = 4 * math.pi * (R**2 + (H / 2)**2)
        F_geom = A_proj / denom if denom > 0 else 0.0
        F_geom = min(F_geom, 1.0)

        tau_atm_val = tau_atm(R)

        q_rad = E_surface * F_geom * tau_atm_val
        q_conv = (1 - chi_r(D)) * HRR / A_proj
        q_total = q_rad + q_conv

        rows.append([
            t, HRR, H, q_rad, q_conv, q_total
        ])

    df = pd.DataFrame(rows, columns=[
        "Time_s",
        "HRR_W",
        "Flame_Height_m",
        "Radiative_Flux_W_m2",
        "Convective_Flux_W_m2",
        "Total_Flux_W_m2"
    ])

    idx_peak = df["Total_Flux_W_m2"].idxmax()

    q_peak = df.loc[idx_peak, "Total_Flux_W_m2"]
    t_peak = df.loc[idx_peak, "Time_s"]

    return {
        "fuel": fuel,
        "burn_duration_s": t_burn,
        "q_peak_W_m2": q_peak,
        "t_peak_s": t_peak,
        "df_flux": df
    }

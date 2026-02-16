# ----------------------------------------------------------
# GASOLINE POOL FIRE — Distance Model at t = t_peak
# Aligned with updated File1 return structure
# ----------------------------------------------------------

import numpy as np
import pandas as pd
import math


def run_distance_model(fire_result):

    # ==========================================================
    # EXTRACT FROM FILE 1 DICTIONARY
    # ==========================================================
    df_time = fire_result["df_flux"]
    t_peak = fire_result["t_peak_s"]

    # Get peak row directly
    peak_row = df_time[df_time["Time_s"] == t_peak].iloc[0]

    HRR = peak_row["HRR_W"]
    H = peak_row["Flame_Height_m"]

    # Since File1 was seat-of-fire, recompute needed values
    # ------------------------------------------------------
    D = 2.0  # must match File1 input (for now fixed)
    m_dot_area = 0.055
    LHV = 43.7e6
    eta = 0.98

    A_pool = math.pi * D**2 / 4.0
    A_proj = D * H

    chi_r = 0.25  # for D=2 (since D <= 5)
    tau_f = math.exp(-0.04 * (2 * D))

    E_surface = (chi_r * HRR / A_proj) * tau_f

    # ==========================================================
    # DISTANCE RANGE
    # ==========================================================
    R_values = np.linspace(0, 50, 300)

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

    R_c = 2.0  # convective decay length

    rows = []

    for R in R_values:

        denom = 4 * math.pi * (R**2 + (H / 2)**2)
        F_geom = A_proj / denom if denom > 0 else 0.0
        F_geom = min(F_geom, 1.0)

        tau_atm_val = tau_atm(R)

        q_rad = E_surface * F_geom * tau_atm_val

        q_conv_0 = (1 - chi_r) * HRR / A_proj
        q_conv = q_conv_0 * math.exp(-R / R_c)

        q_total = q_rad + q_conv

        rows.append([R, q_rad, q_conv, q_total])

    df_dist = pd.DataFrame(rows, columns=[
        "Distance_m",
        "Radiative_Flux_W_m2",
        "Convective_Flux_W_m2",
        "Total_Flux_W_m2"
    ])

    # ==========================================================
    # SELECT ≈100 kW/m²
    # ==========================================================
    threshold = 100_000  # W/m²
    df_dist["Flux_Approx_100kW"] = False

    selected_index = (df_dist["Total_Flux_W_m2"] - threshold).abs().idxmin()
    df_dist.loc[selected_index, "Flux_Approx_100kW"] = True

    return df_dist

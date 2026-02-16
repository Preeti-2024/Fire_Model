# file3_ppe.py
import numpy as np
import pandas as pd

def run_ppe_model(df_distance, layers, t_peak, exposure_time=600.0):
    """
    PPE heat transfer model over time at a selected distance.

    Parameters:
    - df_distance : DataFrame from distance model (must have Flux_Approx_100kW)
    - layers      : list of dicts with PPE layer properties
    - t_peak      : peak fire time from File1 (s)
    - exposure_time : total simulation time (s)

    Returns:
    - df_ppe      : DataFrame with temperatures, heat flux, safety status
    - pain_time   : first time wearer feels pain (s)
    """

    # -------------------------------------------------
    # SELECT DISTANCE ROW (~100 kW/m²)
    # -------------------------------------------------
    row = df_distance[df_distance["Flux_Approx_100kW"] == True].iloc[0]
    distance_m = row["Distance_m"]
    q_rad_ref = row["Radiative_Flux_W_m2"]
    q_conv_ref = row["Convective_Flux_W_m2"]

    # -------------------------------------------------
    # FIXED CONSTANTS
    # -------------------------------------------------
    sigma = 5.67e-8
    T_amb = 300.0
    h_skin = 10.0
    dt = 0.1

    air_gap_thickness = 0.001
    k_air = 0.026
    eps_air_1 = 0.8
    eps_air_2 = 0.8

    # -------------------------------------------------
    # TIME SETTINGS
    # -------------------------------------------------
    time = np.arange(0, exposure_time + dt, dt)
    n_layers = len(layers)

    # -------------------------------------------------
    # INITIAL TEMPERATURES
    # -------------------------------------------------
    T = np.ones(n_layers) * T_amb

    # -------------------------------------------------
    # STORAGE ARRAYS
    # -------------------------------------------------
    T_hist = np.zeros((len(time), n_layers))
    q_layer = np.zeros((len(time), n_layers))
    q_skin = np.zeros(len(time))
    safety_status = []

    q_rad_t = np.zeros(len(time))
    q_conv_t = np.zeros(len(time))
    q_total_t = np.zeros(len(time))

    pain_time = None

    # -------------------------------------------------
    # AIR GAP FUNCTION
    # -------------------------------------------------
    def h_air_gap(T1, T2):
        Tm = 0.5 * (T1 + T2)
        h_rad = 4 * sigma * Tm**3 / (1/eps_air_1 + 1/eps_air_2 - 1)
        h_cond = k_air / air_gap_thickness
        return h_cond + h_rad

    # -------------------------------------------------
    # FIRE TIME FUNCTION
    # -------------------------------------------------
    def fire_time_function(t, tp):
        if t <= 0:
            return 0.0
        return (t / tp) * np.exp(1 - t / tp)

    # -------------------------------------------------
    # TIME LOOP
    # -------------------------------------------------
    for n, t in enumerate(time):

        fire_factor = fire_time_function(t, t_peak)

        q_rad_inc = q_rad_ref * fire_factor
        q_conv_inc = q_conv_ref * fire_factor
        q_total_inc = q_rad_inc + q_conv_inc

        q_rad_t[n] = q_rad_inc
        q_conv_t[n] = q_conv_inc
        q_total_t[n] = q_total_inc

        q_rad_abs = layers[0]["eps"] * q_rad_inc
        q_in = q_rad_abs + q_conv_inc

        T_new = T.copy()

        for i, layer in enumerate(layers):
            mcp = layer["rho"] * layer["cp"] * layer["d"]

            # Left boundary
            if i == 0:
                q_left = q_in
            else:
                h_gap = h_air_gap(T[i-1], T[i])
                q_left = h_gap * (T[i-1] - T[i])

            # Right boundary
            if i < n_layers - 1:
                h_gap = h_air_gap(T[i], T[i+1])
                q_right = h_gap * (T[i] - T[i+1])
            else:
                q_right = h_skin * (T[i] - T_amb)
                q_skin[n] = q_right

            T_new[i] += (q_left - q_right) / mcp * dt
            q_layer[n, i] = q_left

        T = T_new
        T_hist[n, :] = T

        # Safety classification
        if q_skin[n] < 2000:
            safety_status.append("SAFE")
        elif q_skin[n] < 4000:
            safety_status.append("PAIN")
            if pain_time is None:
                pain_time = t
        elif q_skin[n] < 6000:
            safety_status.append("BURN_RISK")
        else:
            safety_status.append("NOT_SAFE")

    # -------------------------------------------------
    # OUTPUT DATAFRAME
    # -------------------------------------------------
    data = {
        "Time_s": time,
        "Distance_m": distance_m,
        "Radiative_Flux_Incident_W_m2": q_rad_t,
        "Convective_Flux_Incident_W_m2": q_conv_t,
        "Total_Flux_Incident_W_m2": q_total_t,
        "q_skin_W_m2": q_skin,
        "Exposure_Safety_Status": safety_status
    }

    for i, layer in enumerate(layers):
        data[f"T_{layer['name']}_K"] = T_hist[:, i]
        data[f"q_into_{layer['name']}_W_m2"] = q_layer[:, i]

    df_ppe = pd.DataFrame(data)

    return df_ppe, pain_time

# main.py
from file1_time import run_pool_fire_model
from file2_distance import run_distance_model
from file3_ppe import run_ppe_model
from fuel_data import get_fuel_properties, get_all_fuel_names

# -------------------------------------------------
# TEST INPUT
# -------------------------------------------------
fuel = "Gasoline"
m_fuel = 14.8
D = 2.0

# Get fuel properties from database
fuel_props = get_fuel_properties(fuel)

# -------------------------------------------------
# RUN FILE 1: Pool Fire Model
# -------------------------------------------------
fire_result = run_pool_fire_model(
    fuel, 
    m_fuel, 
    D,
    burning_rate=fuel_props['burning_rate'],
    lhv_mj=fuel_props['lhv'],
    combustion_efficiency=fuel_props['combustion_efficiency']
)

print("===== POOL FIRE RESULTS =====")
print("Burn Duration (s):", round(fire_result["burn_duration_s"], 2))
print("Peak Flux at R=0 (kW/m²):", round(fire_result["q_peak_W_m2"]/1000, 2))
print("Time at Peak (s):", round(fire_result["t_peak_s"], 2))

# -------------------------------------------------
# RUN FILE 2: Distance Model
# -------------------------------------------------
df_distance = run_distance_model(fire_result)

selected_row = df_distance[df_distance["Flux_Approx_100kW"] == True]

print("\n===== DISTANCE SELECTION =====")
if not selected_row.empty:
    R_selected = selected_row["Distance_m"].values[0]
    flux_selected = selected_row["Total_Flux_W_m2"].values[0] / 1000
    print("Selected Distance (m):", round(R_selected, 3))
    print("Heat Flux at that Distance (kW/m²):", round(flux_selected, 2))
else:
    print("No suitable distance found")

# -------------------------------------------------
# PPE Layer Properties
# -------------------------------------------------
layers = [
    {"name": "Outer Shell",      "d": 0.0007, "k": 0.25, "rho": 450, "cp": 1400, "eps": 0.8},
    {"name": "Moisture Barrier", "d": 0.0005, "k": 0.20, "rho": 900, "cp": 1300, "eps": 0.7},
    {"name": "Thermal Liner",    "d": 0.0030, "k": 0.05, "rho": 120, "cp": 1400, "eps": 0.9},
    {"name": "Inner Liner",      "d": 0.0005, "k": 0.10, "rho": 300, "cp": 1300, "eps": 0.9},
]

# -------------------------------------------------
# RUN FILE 3: PPE Model
# -------------------------------------------------
df_ppe, pain_time = run_ppe_model(
    df_distance,
    layers,
    t_peak=fire_result["t_peak_s"],
    exposure_time=600.0
)

# -------------------------------------------------
# PPE SAFETY OUTPUT
# -------------------------------------------------
print("\n===== PPE SAFETY SUMMARY =====")
if pain_time:
    print(f"The wearer starts feeling PAIN at t = {round(pain_time,2)} s")
else:
    print("The wearer is SAFE for the entire exposure duration.")

statuses = ["SAFE", "PAIN", "BURN_RISK", "NOT_SAFE"]
for status in statuses:
    rows = df_ppe[df_ppe["Exposure_Safety_Status"] == status]
    if not rows.empty:
        t_first = rows["Time_s"].iloc[0]
        print(f"First time status '{status}' is reached: t = {round(t_first,2)} s")

final_status = df_ppe["Exposure_Safety_Status"].iloc[-1]
print(f"\nFinal Status at end of exposure ({df_ppe['Time_s'].iloc[-1]} s): {final_status}")

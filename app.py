import streamlit as st
import pandas as pd
from file1_time import run_pool_fire_model
from file2_distance import run_distance_model
from file3_ppe import run_ppe_model

st.set_page_config(page_title="Gasoline Pool Fire + PPE Safety Simulator", layout="wide")
st.title("🔥 Gasoline Pool Fire + PPE Safety Simulator")

# -----------------------------
# USER INPUTS
# -----------------------------
st.header("1️⃣ Fire and PPE Inputs")

# Fuel type
fuel = st.selectbox("Select Fuel Type", ["Gasoline"])  # Only Gasoline supported

# Mass and pool diameter
m_fuel = st.number_input("Mass of Fuel (kg)", min_value=0.1, step=0.1)
D = st.number_input("Pool Diameter (m)", min_value=0.1, step=0.1)

st.markdown("### PPE Layer Properties (All 4 Layers Required)")
layers = []
for layer_name in ["Outer Shell", "Moisture Barrier", "Thermal Liner", "Inner Liner"]:
    st.write(f"#### {layer_name}")
    d = st.number_input(f"Thickness d (m) for {layer_name}", min_value=0.0001, step=0.0001, format="%.4f")
    k = st.number_input(f"Thermal Conductivity k (W/m·K) for {layer_name}", min_value=0.001, step=0.01)
    rho = st.number_input(f"Density rho (kg/m³) for {layer_name}", min_value=1, step=1)
    cp = st.number_input(f"Specific Heat cp (J/kg·K) for {layer_name}", min_value=1, step=1)
    eps = st.number_input(f"Emissivity eps (0-1) for {layer_name}", min_value=0.0, max_value=1.0, step=0.01)
    layers.append({"name": layer_name, "d": d, "k": k, "rho": rho, "cp": cp, "eps": eps})

# Run button
run_sim = st.button("Run Simulation")

# -----------------------------
# SIMULATION
# -----------------------------
if run_sim:

    if m_fuel <= 0 or D <= 0:
        st.error("Please enter valid values for mass and pool diameter.")
    else:
        st.header("2️⃣ Simulation Results")

        # ---- File 1: Pool Fire Model ----
        fire_result = run_pool_fire_model(fuel, m_fuel, D)
        st.subheader("🔥 Pool Fire Model (R=0)")
        st.write(f"**Burn Duration:** {fire_result['burn_duration_s']:.2f} s")
        st.write(f"**Peak Heat Flux:** {fire_result['q_peak_W_m2']/1000:.2f} kW/m²")
        st.write(f"**Time at Peak:** {fire_result['t_peak_s']:.2f} s")

        # ---- File 2: Distance Model ----
        df_distance = run_distance_model(fire_result)
        row_selected = df_distance[df_distance["Flux_Approx_100kW"] == True].iloc[0]
        R_selected = row_selected["Distance_m"]
        flux_selected = row_selected["Total_Flux_W_m2"]/1000

        st.subheader("📏 Distance Model")
        st.write(f"**Distance at ~100 kW/m²:** {R_selected:.2f} m")
        st.write(f"**Heat Flux at this Distance:** {flux_selected:.2f} kW/m²")

        # ---- File 3: PPE Model ----
        df_ppe, pain_time = run_ppe_model(df_distance, layers, fire_result['t_peak_s'], exposure_time=600.0)

        st.subheader("🛡️ PPE Safety Analysis")

        # Pain time
        if pain_time is None:
            st.success("✅ The wearer is SAFE for the entire exposure duration at this distance.")
        else:
            st.warning(f"⚠️ Pain threshold reached at t = {pain_time:.2f} s")

        # Final status
        final_status = df_ppe["Exposure_Safety_Status"].iloc[-1]
        st.write(f"**Final Safety Status after 600 s:** {final_status}")

        # Layer temperatures at pain time
        if pain_time is not None:
            closest_idx = (df_ppe["Time_s"] - pain_time).abs().idxmin()
            st.write("**Temperatures of PPE Layers at Pain Threshold:**")
            for layer in layers:
                temp = df_ppe.loc[closest_idx, f"T_{layer['name']}_K"]
                st.write(f"- {layer['name']}: {temp:.2f} K")
        
        # Sample of skin heat flux over time
        st.write("**Sample Skin Heat Flux (W/m²) over Time:**")
        st.line_chart(df_ppe[["Time_s", "q_skin_W_m2"]].set_index("Time_s"))

        # Conclusion
        st.subheader("✅ Safety Conclusion")
        st.markdown(f"""
        - Maximum flux at R=0: **{fire_result['q_peak_W_m2']/1000:.2f} kW/m²**  
        - Time at peak flux: **{fire_result['t_peak_s']:.2f} s**  
        - At distance **{R_selected:.2f} m**, flux ≈ 100 kW/m²  
        - PPE wearer will feel **pain** at t = **{pain_time:.2f} s** (if reached)  
        - **Final Safety Status** after 600 s: **{final_status}**
        """)

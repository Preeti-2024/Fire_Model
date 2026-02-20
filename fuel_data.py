# ----------------------------------------------------------
# FUEL PROPERTIES DATABASE
# Database of fuel types with their combustion characteristics
# ----------------------------------------------------------

FUEL_DATABASE = {
    "Gasoline": {
        "burning_rate": 0.055,           # ṁ'' (kg/m²·s)
        "lhv": 43.7,                     # LHV (MJ/kg)
        "combustion_efficiency": 0.98,   # η (dimensionless)
        "density": 740.0,                # density (kg/m³) — approximate
    },
    "Diesel": {
        "burning_rate": 0.040,
        "lhv": 43.0,
        "combustion_efficiency": 0.92,
        "density": 918.0,
    },
    "Jet A-1 / ATF": {
        "burning_rate": 0.045,
        "lhv": 43.1,
        "combustion_efficiency": 0.98,
        "density": 800.0,
    },
    "LPG (Propane basis)": {
        "burning_rate": 0.100,
        "lhv": 46.0,
        "combustion_efficiency": 0.99,
        "density": 510.0,
    },
    "Methanol": {
        "burning_rate": 0.030,
        "lhv": 19.9,
        "combustion_efficiency": 0.90,
        "density": 796.0,
    },
    "Ethanol": {
        "burning_rate": 0.035,
        "lhv": 26.8,
        "combustion_efficiency": 0.95,
        "density": 794.0,
    },
    "Hydrogen (liquid)": {
        "burning_rate": 0.150,
        "lhv": 120.0,
        "combustion_efficiency": 0.99,
        "density": 71.0,
    },
    "n-Heptane (Reference Fuel)": {
        "burning_rate": 0.050,
        "lhv": 44.6,
        "combustion_efficiency": 0.99,
        "density": 675.0,
    },
}


def get_fuel_properties(fuel_name):
    """
    Retrieve fuel properties from the database.
    
    Args:
        fuel_name (str): Name of the fuel
        
    Returns:
        dict: Dictionary containing fuel properties
        
    Raises:
        ValueError: If fuel not found in database
    """
    if fuel_name not in FUEL_DATABASE:
        raise ValueError(f"Fuel '{fuel_name}' not found in database. Available fuels: {list(FUEL_DATABASE.keys())}")
    
    return FUEL_DATABASE[fuel_name].copy()


def get_all_fuel_names():
    """Return list of all available fuel names."""
    return list(FUEL_DATABASE.keys())

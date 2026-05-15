import tkinter as tk
from tkinter import ttk, messagebox

PRESET_RUNWAYS = {
        "Custom": {
            "latitude": "",
            "longitude": "",
            "rw_heading": "",
            "rw_height": "",
            "rw_width": ""
        },
        "KSEA (Seattle) - Runway 34R": {
            "latitude": "47.4311723",
            "longitude": "-122.3080382",
            "rw_heading": "0.0", # [deg]
            "rw_height": "355.0", # [ft]
            "rw_width": "150.0" # [ft]
        }
}

PRESET_CONDITIONS = {
    "height": 524.0, # [ft]
    "velocity": 80.0, # [kts]
    "distance": 10000.0, # [ft]
    "glide": -3.0, # [deg]
    "heading": 0.0 # [deg]
}

def get_jsbsim_config(preset_runway=None):
    """
    Terminal version (Docker-ready). 
    Uses input() in the console instead of windows.
    """
    runway_data = {}
    initial_conditions = {}

    if preset_runway is not None:
        runway_key = preset_runway
    else:
        print("\n" + "="*30)
        print(" CONFIGURATION (Terminal Mode)")
        print("="*30)
        
        runway_keys = list(PRESET_RUNWAYS.keys())
        for i, name in enumerate(runway_keys):
            print(f" [{i}] {name}")
        
        try:
            choice = input("\nPick a runway (default 0): ")
            idx = int(choice) if choice.strip() != "" else 0
            runway_key = runway_keys[idx]
        except (ValueError, IndexError):
            print("Invalid choice, setting default.")
            runway_key = runway_keys[0]

    preset = PRESET_RUNWAYS[runway_key]
    
    if runway_key == "Custom":
        print("\n--- Custom Runway: Please enter the details ---")
        runway_data["lat"] = float(input("Latitude [deg]: ") or 0)
        runway_data["lon"] = float(input("Longitude [deg]: ") or 0)
        runway_data["heading"] = float(input("Runway heading [deg]: ") or 0)
        runway_data["elevation"] = float(input("Elevation [ft]: ") or 0)
        runway_data["width"] = float(input("Runway width [ft]: ") or 0)
    else:
        runway_data["lat"] = float(preset["latitude"])
        runway_data["lon"] = float(preset["longitude"])
        runway_data["heading"] = float(preset["rw_heading"])
        runway_data["elevation"] = float(preset["rw_height"])
        runway_data["width"] = float(preset["rw_width"])

    initial_conditions["h_agl"] = float(PRESET_CONDITIONS["height"])
    initial_conditions["vc_kts"] = float(PRESET_CONDITIONS["velocity"])
    initial_conditions["dist_ft"] = float(PRESET_CONDITIONS["distance"])
    initial_conditions["gamma_deg"] = float(PRESET_CONDITIONS["glide"])
    initial_conditions["psi_true_deg"] = runway_data["heading"]

    print(f"\nStarting simulation for: {runway_key}")
    return runway_data, initial_conditions
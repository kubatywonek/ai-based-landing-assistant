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
    Displays a GUI for the user to input runway parameters and initial conditions for the flight simulation.
    :param preset_runway: If provided, returns the preset configuration. If None, manual input is required.
    Returns:
    - runway_data: dict with keys 'lat', 'lon', 'heading', 'elevation', 'width'
    - initial_conditions: dict with keys 'h_agl', 'vc_kts', 'dist_ft', 'gamma_deg', 'psi_true_deg'
    """
    runway_data = {}
    initial_conditions = {}
    if(preset_runway is not None):
        runway_data["lat"] = float(PRESET_RUNWAYS[preset_runway]["latitude"])
        runway_data["lon"] = float(PRESET_RUNWAYS[preset_runway]["longitude"])
        runway_data["heading"] = float(PRESET_RUNWAYS[preset_runway]["rw_heading"])
        runway_data["elevation"] = float(PRESET_RUNWAYS[preset_runway]["rw_height"])
        runway_data["width"] = float(PRESET_RUNWAYS[preset_runway]["rw_width"])
        
        initial_conditions["h_agl"] = float(PRESET_CONDITIONS["height"])
        initial_conditions["vc_kts"] = float(PRESET_CONDITIONS["velocity"])
        initial_conditions["dist_ft"] = float(PRESET_CONDITIONS["distance"])
        initial_conditions["gamma_deg"] = float(PRESET_CONDITIONS["glide"])
        initial_conditions["psi_true_deg"] = float(PRESET_RUNWAYS[preset_runway]["rw_heading"]) # Same as runway heading
        return runway_data, initial_conditions
    
    window = tk.Tk()
    window.title("Configuration")
    data = {
        "latitude": tk.StringVar(value="PRESET_RUNWAY['Custom']['latitude']"),
        "longitude": tk.StringVar(value="PRESET_RUNWAY['Custom']['longitude']"),
        "rw_heading": tk.StringVar(value="PRESET_RUNWAY['Custom']['rw_heading']"),
        "rw_height": tk.StringVar(value="PRESET_RUNWAY['Custom']['rw_height']"),
        "rw_width": tk.StringVar(value="PRESET_RUNWAY['Custom']['rw_width']"),

        "height": tk.StringVar(value=PRESET_CONDITIONS['height']),      # Height above the runway [ft]
        "velocity": tk.StringVar(value=PRESET_CONDITIONS['velocity']),  # Velocity [kts]
        "distance": tk.StringVar(value=PRESET_CONDITIONS['distance']),  # Distance from threshold [ft]
        "glide": tk.StringVar(value=PRESET_CONDITIONS['glide']),        # Glide path angle [deg]
        "heading": tk.StringVar(value=PRESET_CONDITIONS['heading']),    # Initial heading [deg]
    }

    def on_start():
        try:
            runway_data["lat"] = float(data["latitude"].get())
            runway_data["lon"] = float(data["longitude"].get())
            runway_data["heading"] = float(data["rw_heading"].get())
            runway_data["elevation"] = float(data["rw_height"].get())
            runway_data["width"] = float(data["rw_width"].get())

            initial_conditions["h_agl"] = float(data["height"].get())
            initial_conditions["vc_kts"] = float(data["velocity"].get())
            initial_conditions["dist_ft"] = float(data["distance"].get())
            initial_conditions["gamma_deg"] = float(data["glide"].get())
            initial_conditions["psi_true_deg"] = float(data["heading"].get())
            
            window.destroy()
        except ValueError:
            messagebox.showerror("Data error", "All fields must be numeric values (use a dot, not a comma).")

    def on_preset_selected(event):
        selected = preset_combo.get()
        if selected in PRESET_RUNWAYS:
            preset = PRESET_RUNWAYS[selected]
            data["latitude"].set(preset["latitude"])
            data["longitude"].set(preset["longitude"])
            data["rw_heading"].set(preset["rw_heading"])
            data["rw_height"].set(preset["rw_height"])
            data["rw_width"].set(preset["rw_width"])
            data["heading"].set(preset["rw_heading"]) # Initial heading same as runway heading

    # ------------------------------ LAYOUT -----------------------------------------------

    frame = ttk.Frame(window, padding="15")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    ttk.Label(frame, text="Runway parameters", font=('-weight', 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))

    ttk.Label(frame, text="Quick Select:", font=('-weight', 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
    preset_combo = ttk.Combobox(frame, values=list(PRESET_RUNWAYS.keys()), state="readonly", width=35)
    preset_combo.grid(row=1, column=1, pady=(0, 5))
    preset_combo.bind("<<ComboboxSelected>>", on_preset_selected)

    ttk.Label(frame, text="Latitude [deg]:").grid(row=2, column=0, sticky=tk.W)
    ttk.Entry(frame, textvariable=data["latitude"]).grid(row=2, column=1)
    ttk.Label(frame, text="Longitude [deg]:").grid(row=3, column=0, sticky=tk.W)
    ttk.Entry(frame, textvariable=data["longitude"]).grid(row=3, column=1)
    ttk.Label(frame, text="Runway heading [deg]:").grid(row=4, column=0, sticky=tk.W)
    ttk.Entry(frame, textvariable=data["rw_heading"]).grid(row=4, column=1)
    ttk.Label(frame, text="Elevation [ft]:").grid(row=5, column=0, sticky=tk.W)
    ttk.Entry(frame, textvariable=data["rw_height"]).grid(row=5, column=1)
    ttk.Label(frame, text="Runway width [ft]:").grid(row=6, column=0, sticky=tk.W)
    ttk.Entry(frame, textvariable=data["rw_width"]).grid(row=6, column=1)

    ttk.Label(frame, text="Initial Aircraft Position", font=('-weight', 'bold')).grid(row=7, column=0, columnspan=2, pady=(15, 10))
    ttk.Label(frame, text="Height above runway [ft]:").grid(row=8, column=0, sticky=tk.W)
    ttk.Entry(frame, textvariable=data["height"]).grid(row=8, column=1)
    ttk.Label(frame, text="Distance from threshold [ft]:").grid(row=9, column=0, sticky=tk.W)
    ttk.Entry(frame, textvariable=data["distance"]).grid(row=9, column=1)
    ttk.Label(frame, text="Velocity [kts]:").grid(row=10, column=0, sticky=tk.W)
    ttk.Entry(frame, textvariable=data["velocity"]).grid(row=10, column=1)
    ttk.Label(frame, text="Glide path angle [deg]:").grid(row=11, column=0, sticky=tk.W)
    ttk.Entry(frame, textvariable=data["glide"]).grid(row=11, column=1)
    ttk.Label(frame, text="Initial heading [deg]:").grid(row=12, column=0, sticky=tk.W)
    ttk.Entry(frame, textvariable=data["heading"]).grid(row=12, column=1)

    ttk.Button(frame, text="Confirm and Start", command=on_start).grid(row=13, column=0, columnspan=2, pady=(20, 0))

    # -------------------------------------------------------------------------------------
    preset_combo.current(0)
    on_preset_selected(None)
    window.mainloop()
    # If the user closes the window without confirming
    if not runway_data:
        return None, None

    return runway_data, initial_conditions
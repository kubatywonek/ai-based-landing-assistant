import jsbsim
import os
import numpy as np
import math

"""
API for JSBSim with custom flight simulation capabilities.

Available aircraft models in JSBSim (as of version 1.0.0):
737			c172p			f22			    minisgs			Short_S23
787-8		c172r			F450			mk82			Shuttle
A320		c172x			F4N			    OV10			Submarine_Scout
A4			c182			F80C			p51d			T37
ah1s		c310			fokker100		pa28			T38
aircraft_template.xml	    Camel			fokker50		paraglider		t6texan2
B17			Concorde		global5000		pc7			    weather-balloon
B747		DHC6			J246			pogo-jsbsim		wrightFlyer1903
ball		dr1			    J3Cub			Pterosaur		X15
blank		f104			L17			    SGS			    x24b
Boeing314	f15			    L410			sgs126			XB-70
C130		f16			    MD11			sgs233			ZLT-NT
"""
LATTITUDE_TO_FT_COEF = 364173.0  # Approximate conversion factor from degrees of latitude to feet (varies with latitude)

class FlightSimulator:

    """
    :thows Raises an Error if created without runway data or initial conditions!!
    :param aircraft: plane model (default: Cessna 172)
    :param runway_data: Dictionary with runway information
        {
            "lat": float,       # latitude of runway threshold [deg]
            "lon": float,       # longitude of runway threshold [deg]
            "heading": float,   # runway heading (True Heading) [deg]
            "elevation": float, # runway elevation [ft]
            "width": float      # runway width [ft]
        }
    :param initial_conditions: Dictionary with initial aircraft conditions (default: stable approach path)
        {
            "h_agl": float,         # height above ground level [ft]
            "vc_kts": float,        # velocity (IAS) [kts]
            "dist_ft": float,       # distance from runway threshold [ft]
            "gamma_deg": float,     # glide path angle [deg]
            "psi_true_deg": float   # initial heading [deg]
        }
    """
    def __init__(self, aircraft="c172p", runway_data=None, initial_conditions=None):
        self.jsbsim_path = os.path.dirname(jsbsim.__file__)
        self.fdm = jsbsim.FGFDMExec(self.jsbsim_path)
        self.fdm.set_debug_level(0) # 0 = no debug, 1 = warnings, 2 = info, 3 = debug
        self.fdm.set_aircraft_path(os.path.join(self.jsbsim_path, 'aircraft'))
        self.fdm.set_engine_path(os.path.join(self.jsbsim_path, 'engine'))
        if aircraft == "c172p":
            # Distance from the center of gravity to the main landing gear (in feet), used for touchdown detection
            self.cg_offset = 4.44
        else:
            self.cg_offset = 0.0
        
        if not self.fdm.load_model(aircraft):
            raise RuntimeError(f"Could not load model: {aircraft}")

        if runway_data is None or initial_conditions is None:
            raise RuntimeError("Simulation configuration was not provided.")
        
        self.rw_data = runway_data
        self.init_data = initial_conditions
        
        self.reset()

    def reset(self):
        """
        Resets the simulation and returns the initial state and sets up the environment
        based on the provided runway and initial conditions.
        """
        # Starting parameters
        self.fdm['position/terrain-elevation-asl-ft'] = self.rw_data["elevation"]     # Runway elevation above mean sea level
        self.fdm['ic/h-sl-ft'] = self.rw_data["elevation"] + self.init_data["h_agl"]  # Starting height above the runway
        self.fdm['ic/vc-kts'] = self.init_data["vc_kts"]                              # Speed
        self.fdm['ic/gamma-deg'] = self.init_data["gamma_deg"]                        # Descent angle
        self.fdm['ic/psi-true-deg'] = self.rw_data["heading"]                         # Nose heading
        dist_start_ft = self.init_data["dist_ft"]                                     # Distance from runway threshold

        # Starting position calculated based on runway data and desired starting distance
        rw_rad = math.radians(self.rw_data["heading"])
        lat_offset = (dist_start_ft * math.cos(rw_rad)) / LATTITUDE_TO_FT_COEF
        lon_offset = (dist_start_ft * math.sin(rw_rad)) / (LATTITUDE_TO_FT_COEF * math.cos(math.radians(self.rw_data["lat"])))
        
        self.fdm['ic/lat-geod-deg'] = self.rw_data["lat"] - lat_offset                # Starting latitude
        self.fdm['ic/long-gc-deg'] = self.rw_data["lon"] - lon_offset                 # Starting longitude
        
        # Simulation initialization (run initial conditions)
        self.fdm.run_ic()
        
        # Engine startup
        self.fdm['propulsion/engine[0]/set-running'] = 1
        self.fdm['fcs/throttle-cmd-norm'] = 0.5  # Half throttle as default
        self.fdm['fcs/mixture-cmd-norm'] = 1.0   # Rich mixture (required for c172)
        
        # Stabilization of physics (performing a few "empty" steps to remove sudden force jumps)
        for _ in range(10):
            self.fdm.run()
            
        self.touchdown = False
        return self.get_state()

    def get_runway_relative_pos(self):
        """
        Calculates the position of the aircraft relative to the runway threshold and centerline.
        Math used: Vector projection onto the local runway coordinate system.
        """
        # Current position of the aircraft [degrees]
        ac_lat = self.fdm['position/lat-geod-deg']
        ac_lon = self.fdm['position/long-gc-deg']
        
        # Conversion of degrees to feet
        d_lat = (ac_lat - self.rw_data["lat"]) * LATTITUDE_TO_FT_COEF
        d_lon = (ac_lon - self.rw_data["lon"]) * LATTITUDE_TO_FT_COEF * math.cos(math.radians(self.rw_data["lat"]))
        
        # Runway heading in radians
        rw_rad = math.radians(self.rw_data["heading"])
        
        # long_dist = longitudinal distance to threshold (positive if past the threshold, negative if before)
        # lat_error = lateral deviation from runway centerline (positive if right of centerline, negative if left)
        long_dist = d_lat * math.cos(rw_rad) + d_lon * math.sin(rw_rad)
        lat_error = -d_lat * math.sin(rw_rad) + d_lon * math.cos(rw_rad)
        
        return long_dist, lat_error

    def get_heading_error(self):
        """
        Calculates the heading error relative to the runway heading. Normalizes value between [-pi, pi].
        Positive means the nose is pointing to the right of the runway heading, negative means left.
        """

        plane_heading = self.fdm['ic/psi-true-rad']
        runway_heading = math.radians(self.rw_data["heading"])
        heading_error = (plane_heading - runway_heading + math.pi) % (2 * math.pi) - math.pi

        return heading_error

    def get_state(self):
        """
        Returns the current state of the aircraft.
        Input Vector (8-dimensional):
        0: Height above the runway (ft)
        1: Vertical speed (ft/s) - positive means climbing, negative means descending
        2: Horizontal speed (ft/s)
        3: Pitch angle (rad) - positive means nose up, negative means nose down
        4: Roll angle (rad) - positive means right wing down, negative means left wing down
        5: Distance to runway threshold (ft) - negative means we are before the threshold
        6: Lateral deviation from runway centerline (ft) - negative means to the left, positive to the right
        7: Heading error (rad) - error relative to runway heading, negative means to the left and positive means to the right
        """
        long_dist, lat_error = self.get_runway_relative_pos()
        heading_error = self.get_heading_error()
        
        state = [
            self.fdm['position/h-agl-ft'] - self.cg_offset,           # Height above runway - center of gravity offset
            self.fdm['velocities/v-down-fps'] * -1,                   # Vertical speed
            self.fdm['velocities/u-fps'],                             # Horizontal speed
            self.fdm['attitude/pitch-rad'],                           # Pitch
            self.fdm['attitude/roll-rad'],                            # Roll
            long_dist,                                                # Dist to threshold
            lat_error,                                                # Lateral deviation
            heading_error                                             # Heading error
        ]
        return np.array(state, dtype=np.float32)

    def step(self, actions):
        """
        Performs a simulation step given the control inputs and returns the new state and done flag.
        :param actions: [aileron, elevator, throttle] in range [-1, 1]
        Aileron: -1 (full left) to 1 (full right)
        Elevator: -1 (full down - nose up) to 1 (full up - nose down)
        Throttle: -1 (idle) to 1 (full throttle)
        """
        self.fdm['fcs/aileron-cmd-norm'] = float(actions[0])
        self.fdm['fcs/elevator-cmd-norm'] = float(actions[1])
        self.fdm['fcs/throttle-cmd-norm'] = (float(actions[2]) + 1.0) / 2.0
        
        # 5 steps to let the physics react to the control inputs
        for _ in range(5):
            self.fdm.run()
            
        state = self.get_state()
        done, info = self._check_if_done(state)
        
        return state, done, info
    
    def _check_if_done(self, state):
        """
        Ending conditions:
        - Touchdown (landing) detected by wheel contact
        - Exceeding limits (5000 ft from threshold or 2000 ft lateral deviation from the centerline)
        """
        v_speed = state[1]
        roll = state[4]
        dist = state[5]
        lat_err = state[6]
        
        # State value is NaN - consider it a crash
        if not state.any(): 
            return True, {"status": "ERROR", "reason": "NaN value (physics error)"}
            
        nose_wheel_touch = self.fdm['gear/unit[0]/WOW']
        left_wheel_touch = self.fdm['gear/unit[1]/WOW']
        right_wheel_touch = self.fdm['gear/unit[2]/WOW']
        
        if nose_wheel_touch > 0 or left_wheel_touch > 0 or right_wheel_touch > 0:
            if not self.touchdown:
                self.touchdown = True
                print("TOUCHDOWN DETECTED")

            if v_speed < -10.0:
                return True, {"status": "CRASH", "reason": f"Hard Landing (V-Speed: {v_speed:.1f} fps)"}
            
            # Wing strike - roll angle too high at touchdown 
            if abs(roll) > 0.26:
                return True, {"status": "CRASH", "reason": "Wing Strike (Too much roll)"}
                
            # Out of runway landing - the plane is too far from the centerline at touchdown
            if abs(lat_err) > self.rw_data["width"] / 2.0:
                return True, {"status": "CRASH", "reason": "Landed off runway (Grass)"}
            
            # Short or long landing - the plane touched down too early or too late
            if dist < -100.0 or dist > 8000.0:
                 return True, {"status": "CRASH", "reason": "Landed short or overran runway"}

            # Landing accepted - the plane touched down with acceptable parameters
            return True, {"status": "LANDED", "reason": "Perfect Touchdown!"}
            
        # Out of bounds - the plane flew too far from the runway or is too high above it
        if dist > 10000.0 or abs(lat_err) > 3000.0 or state[0] > 3000.0:
            return True, {"status": "OUT_OF_BOUNDS", "reason": "Flew too far from approach path"}
            
        # Normal flying - the plane is still in the air and within acceptable parameters
        return False, {"status": "FLYING", "reason": ""}
    
    def enable_flightgear(self, host='127.0.0.1', port=5550, rate=60):
        """
        Creates an output directive for FlightGear to receive the aircraft state via UDP.
        :param host: IP address to send the data to (default is localhost)
        :param port: UDP port to send the data to (default is 5550)
        :param rate: Rate in Hz at which to send the data (default is 60)
        """
        output_xml = f"""<?xml version="1.0"?>
        <output name="{host}" type="FLIGHTGEAR" port="{port}" protocol="UDP" rate="{rate}">
        </output>
        """
        abs_path = os.path.abspath("fg_conf/fg_out.xml")

        with open(abs_path, "w") as f:
            f.write(output_xml)
            
        if not self.fdm.set_output_directive(abs_path):
            print("Warning: Failed to initialize FlightGear directive.")
        else:
            print(f"UDP visualization enabled on {host}:{port}")
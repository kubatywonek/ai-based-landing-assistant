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

lattitude_to_ft_coef = 364173.0  # Approximate conversion factor from degrees of latitude to feet (varies with latitude)

class FlightSimulator:

    """
    :param aircraft: plane model (default: Cessna 172)
    :param runway_data: Dictionary with runway information (default: Seattle-Tacoma Intl, RWY 34L)
        {
            "lat": float,      # latitude of runway threshold [deg]
            "lon": float,      # longitude of runway threshold [deg]
            "heading": float,  # runway heading (True Heading) [deg]
            "elevation": float # runway elevation [ft]
        }
    """
    def __init__(self, aircraft="c172x", runway_data=None):
        self.jsbsim_path = os.path.dirname(jsbsim.__file__)
        self.fdm = jsbsim.FGFDMExec(self.jsbsim_path)
        self.fdm.set_aircraft_path(os.path.join(self.jsbsim_path, 'aircraft'))
        self.fdm.set_engine_path(os.path.join(self.jsbsim_path, 'engine'))
        
        if not self.fdm.load_model(aircraft):
            raise RuntimeError(f"Could not load model: {aircraft}")

        self.rw_data = runway_data or {
            "lat": 47.43, 
            "lon": -122.31, 
            "heading": 340.0, 
            "elevation": 433.0
        }
        
        self.reset()

    def reset(self):
        """
        Resets the simulation and returns the initial state.
        FOR NOW: Sets the plane on a stable approach path 3 miles from the runway, 
        at 1500 ft AGL, 85 knots, and a 3 degree glide slope.
        """

        # Starting parameter (for testing purposes)
        self.fdm['ic/h-sl-ft'] = self.rw_data["elevation"] + 1500.0  # 1500 ft over runway elevation
        self.fdm['ic/vc-kts'] = 85.0                                 # IAS (85 knots - ideal for Cessna)
        self.fdm['ic/gamma-deg'] = -3.0                              # Descent angle (3 degrees down)
        self.fdm['ic/psi-true-deg'] = self.rw_data["heading"]        # Nose pointed along the runway centerline
        dist_start_ft = 18228.0                                      # 3 miles from the runway threshold

        # Starting position calculated based on runway data and desired starting distance
        rw_rad = math.radians(self.rw_data["heading"])
        lat_offset = (dist_start_ft * math.cos(rw_rad)) / lattitude_to_ft_coef
        lon_offset = (dist_start_ft * math.sin(rw_rad)) / (lattitude_to_ft_coef * math.cos(math.radians(self.rw_data["lat"])))
        self.fdm['ic/lat-gc-deg'] = self.rw_data["lat"] - lat_offset
        self.fdm['ic/long-gc-deg'] = self.rw_data["lon"] - lon_offset
        
        # Simulation initialization (run initial conditions)
        self.fdm.run_ic()
        
        # Engine startup
        self.fdm['propulsion/engine[0]/set-running'] = 1
        self.fdm['fcs/throttle-cmd-norm'] = 0.5  # Half throttle as default
        self.fdm['fcs/mixture-cmd-norm'] = 1.0   # Rich mixture (required for c172)
        
        # Stabilization of physics (performing a few "empty" steps to remove sudden force jumps)
        for _ in range(10):
            self.fdm.run()
            
        return self.get_state()

    def _get_runway_relative_pos(self):
        """
        Calculates the position of the aircraft relative to the runway threshold and centerline.
        Math used: Vector projection onto the local runway coordinate system.
        """
        # Current position of the aircraft [degrees]
        ac_lat = self.fdm['position/lat-gc-deg']
        ac_lon = self.fdm['position/long-gc-deg']
        
        # Conversion of degrees to feet
        d_lat = (ac_lat - self.rw_data["lat"]) * lattitude_to_ft_coef
        d_lon = (ac_lon - self.rw_data["lon"]) * lattitude_to_ft_coef * math.cos(math.radians(self.rw_data["lat"]))
        
        # Runway heading in radians
        rw_rad = math.radians(self.rw_data["heading"])
        
        # long_dist = longitudinal distance to threshold (positive if past the threshold, negative if before)
        # lat_error = lateral deviation from runway centerline (positive if right of centerline, negative if left)
        long_dist = d_lat * math.cos(rw_rad) + d_lon * math.sin(rw_rad)
        lat_error = -d_lat * math.sin(rw_rad) + d_lon * math.cos(rw_rad)
        
        return long_dist, lat_error

    def get_state(self):
        """
        Returns the current state of the aircraft.
        Input Vector (7-dimensional):
        0: Height above the runway (ft)
        1: Vertical speed (ft/s) - positive means climbing, negative means descending
        2: Horizontal speed (ft/s)
        3: Pitch angle (rad) - positive means nose up, negative means nose down
        4: Roll angle (rad) - positive means right wing down, negative means left wing down
        5: Distance to runway threshold (ft) - negative means we are before the threshold
        6: Lateral deviation from runway centerline (ft) - negative means to the left, positive to the right
        """
        long_dist, lat_error = self._get_runway_relative_pos()
        
        state = [
            self.fdm['position/h-sl-ft'] - self.rw_data["elevation"], # Height above runway
            self.fdm['velocities/v-down-fps'] * -1,                   # Vertical speed
            self.fdm['velocities/u-fps'],                             # Horizontal speed
            self.fdm['attitude/pitch-rad'],                           # Pitch
            self.fdm['attitude/roll-rad'],                            # Roll
            long_dist,                                                # Dist to threshold
            lat_error                                                 # Lateral deviation
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
        done = self._check_if_done(state)
        
        # NaN protection: if any state value is NaN, return a zero state and mark as done (crash)
        if np.isnan(state).any():
            return np.zeros(7, dtype=np.float32)

        return state, done
    
    def _check_if_done(self, state):
        """
        Ending conditions:
        - Height < 1 foot (Landing/Crash)
        - Exceeding limits (5000 ft from threshold or 2000 ft lateral deviation from the centerline)
        """
        h_agl = state[0]
        dist = state[5]
        lat_err = state[6]
        
        # If any state value is NaN - consider it a crash (done)
        if not state.any(): 
            return True
            
        # Finishing conditions
        if h_agl < 1.0 or dist > 5000 or abs(lat_err) > 2000:
            return True
        return False
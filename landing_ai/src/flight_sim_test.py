from sim_env.jsbsim_wrapper import FlightSimulator
from sim_env.preflight_config import get_jsbsim_config
import time

def test_flight_sim(action=[0.0, 0.0, 0.0], steps=50, Hz=10, enable_flightgear=False, default_runway=None):
    """
    Simple test function to validate the FlightSimulator API.
    :param action: Control input for the plane [aileron (-1.0 to 1.0), elevator (-1.0 to 1.0), throttle (-1.0 to 1.0)]
    :param steps: Number of simulation steps to run
    :param Hz: Simulation delay (1 / Hz seconds per step) to simulate real-time
    :param enable_flightgear: Whether to enable FlightGear visualization (optional)
    :param default_runway: Preset runway to use for the simulation (e.g., "KSEA (Seattle) - Runway 34R")
    """
    print("--- API test for JSBSim ---")
    runway, ic = get_jsbsim_config(preset_runway=default_runway)
    if runway is None or ic is None:
        print("Configuration error: No runway or initial conditions provided.")
        return
    env = FlightSimulator(runway_data=runway, initial_conditions=ic)
    rate = 1.0 / Hz
    try:
        if env is None:
            print("No environment provided")
            return
        if enable_flightgear:
            env.enable_flightgear() # Optional
        plane_state = env.reset()
        print(f"Environment initialized!")
        print(f"Initial state:")
        debug_flight_state(plane_state)

        for i in range(steps):
            plane_state, done, info = env.step(action)
            if i % 10 == 0:
                print(f"Step {i} -> Finished: {done}\n")
                debug_flight_state(plane_state)
                if enable_flightgear:
                    time.sleep(rate)  # Sleep to simulate real-time
            if done:
                print("Simulation finished. Status: ", info["status"], ". Reason: ", info["reason"])
                break
                
        print("\n--- TEST FINISHED ---")
        
    except Exception as e:
        print(f"✗ Error: {e}")

def debug_flight_state(state):
    """
    0: Height above the runway (ft)
    1: Vertical speed (ft/s)
    2: Horizontal speed (ft/s)
    3: Pitch angle (rad)
    4: Roll angle (rad)
    5: Distance to runway threshold (ft) - negative means we are before the threshold
    6: Lateral deviation from runway centerline (ft) - 0 means ideal centering
    7: Heading error (rad) - error relative to runway heading, negative means to the left
    """
    print(f"------------- Flight State -------------")
    print(f"Height above runway: {state[0]:.2f} ft")
    print(f"Vertical speed: {state[1]:.2f} ft/s   or   {state[1]*0.5925:.2f} knots")
    print(f"Horizontal speed: {state[2]:.2f} ft/s   or   {state[2]*0.5925:.2f} knots")
    print(f"Pitch angle: {state[3]:.2f} rad   or   {state[3]*57.2957795:.2f} deg")
    print(f"Roll angle: {state[4]:.2f} rad   or   {state[4]*57.2957795:.2f} deg")
    print(f"Distance to threshold: {state[5]:.2f} ft")
    print(f"Lateral deviation: {state[6]:.2f} ft")
    print(f"Heading error: {state[7]:.2f} rad   or   {state[7]*57.2957795:.2f} deg")
    print(f"----------------------------------------\n")
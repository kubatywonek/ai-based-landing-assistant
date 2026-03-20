def test_flight_sim(env=None, action=[0.0, 0.0, 0.0], steps=50):
    """
    Simple test function to validate the FlightSimulator API.
    :param env: FlightSimulator instance
    :param action: Control input for the plane [aileron (-1.0 to 1.0), elevator (-1.0 to 1.0), throttle (-1.0 to 1.0)]
    :param steps: Number of simulation steps to run
    """
    print("--- API test for JSBSim ---")
    try:
        if env is None:
            print("No environment provided")
            return
        plane_state = env.reset()
        print(f"✓ Environment initialized!")
        print(f"✓ Initial state:")
        debug_flight_state(plane_state)

        for i in range(steps):
            plane_state, done = env.step(action)
            if i % 10 == 0:
                print(f"Step {i} -> Finished: {done}\n")
                debug_flight_state(plane_state)
                
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
    """
    print(f"------------- Flight State -------------")
    print(f"Height above runway: {state[0]:.2f} ft")
    print(f"Vertical speed: {state[1]:.2f} ft/s   or   {state[1]*0.5925:.2f} knots")
    print(f"Horizontal speed: {state[2]:.2f} ft/s   or   {state[2]*0.5925:.2f} knots")
    print(f"Pitch angle: {state[3]:.2f} rad   or   {state[3]*57.2957795:.2f} deg")
    print(f"Roll angle: {state[4]:.2f} rad   or   {state[4]*57.2957795:.2f} deg")
    print(f"Distance to threshold: {state[5]:.2f} ft")
    print(f"Lateral deviation: {state[6]:.2f} ft")
    print(f"----------------------------------------\n")
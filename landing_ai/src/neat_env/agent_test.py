from sim_env.jsbsim_wrapper import FlightSimulator
from sim_env.preflight_config import get_jsbsim_config
import time
import neat
import pickle

def test_agent(agent_path, steps=1000, Hz=10, enable_flightgear=False):
    """
    Simple test function to validate the FlightSimulator API.
    :param agent_path: Path to the trained agent file
    :param steps: Number of simulation steps to run
    :param Hz: Simulation delay (1 / Hz seconds per step) to simulate real-time
    :param enable_flightgear: Whether to enable FlightGear visualization (optional)
    """
    print("--- Agent test flight ---")

    # --- AGENT SETUP ---
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         'config-neat.txt')
                         
    with open(agent_path, 'rb') as f:
        agent_genome = pickle.load(f)
    if agent_genome is None:
        print("Error: No genome found in the specified file.")
        return

    net = neat.nn.FeedForwardNetwork.create(agent_genome, config)

    # --- SIMULATION SETUP ---
    runway, ic = get_jsbsim_config()
    if runway is None or ic is None:
        print("Configuration error: No runway or initial conditions provided.")
        return
    env = FlightSimulator(runway_data=runway, initial_conditions=ic)
    rate = 1.0 / Hz
    if env is None:
        print("No environment provided")
        return

    # --- SIMULATION LOOP ---
    try:
        if enable_flightgear:
            env.enable_flightgear() # Optional
        plane_state = env.reset()

        for i in range(steps):
            action = net.activate(plane_state)
            plane_state, done, info = env.step(action)
            if i % 10 == 0:
                print(f"Step {i}\n")
                debug_agent(plane_state)
                if enable_flightgear:
                    time.sleep(rate)  # Sleep to simulate real-time
            if done:
                print("Simulation finished. Status: ", info["status"], ". Reason: ", info["reason"])
                break
        
    except Exception as e:
        print(f"✗ Error: {e}")

def debug_agent(state):
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
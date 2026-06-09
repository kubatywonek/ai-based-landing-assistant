from sim_env.jsbsim_wrapper import FlightSimulator
from sim_env.preflight_config import get_jsbsim_config
import sim_env.telemetry as log
import time
import neat
import os
import math
import pickle

def test_agent(agent_path, steps=10000, Hz=5, enable_flightgear=False):
    """
    Simple test function to validate the FlightSimulator API.
    :param agent_path: Path to the trained agent file
    :param steps: Number of simulation steps to run
    :param Hz: Simulation delay (1 / Hz seconds per step) to simulate real-time
    :param enable_flightgear: Whether to enable FlightGear visualization (optional)
    """
    print("--- Agent test flight ---")

    # --- AGENT SETUP ---
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-neat.txt')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
                         
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
    logger = log.Telemetry()
    if env is None:
        print("No environment provided")
        return

    # --- SIMULATION LOOP ---
    try:
        if enable_flightgear:
            env.enable_flightgear() # Optional
        plane_state = env.reset()
        prev_action = [0.0, 0.0, 0.1] # Initial action to get the plane moving

        for i in range(steps):
            action = net.activate(list(plane_state))
            logger.log({
                'step': i,
                'alt': plane_state[0],
                'aileron': action[0],
                'elevator': action[1],
                'throttle': action[2],
                'pitch': math.degrees(plane_state[3]),
                'roll': math.degrees(plane_state[4])
            })
            plane_state, done, info = env.step(action)
            if i % 10 == 0:
                print(f"Step {i}\n")
                debug_agent(plane_state)
                if enable_flightgear:
                    time.sleep(rate)  # Sleep to simulate real-time
            if done:
                print("Simulation finished. Status: ", info["status"], ". Reason: ", info["reason"])
                break
        logger.save()
        print("Flight data saved. Generating report...")
        logger.plot()
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
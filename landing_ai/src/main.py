from flight_sim_test import test_flight_sim
from neat_env.assistant import run_evolution
from neat_env.agent_test import test_agent
import os

def test():
    test_flight_sim(action=[0.0, 0.0, 0.0], steps=1500, Hz=10, enable_flightgear=False, default_runway="KSEA (Seattle) - Runway 34R")

def main():
    local_dir = os.path.dirname(__file__)
    base_agent = os.path.join(local_dir, 'neat_env', 'models', 'v1_landing_agent.pkl')
    run_evolution(learn_runway="KSEA (Seattle) - Runway 34R", generations=50, from_seed=base_agent)

def test_agent_result(filename=None):
    if filename != None:
        local_dir = os.path.dirname(__file__)
        model_path = os.path.join(local_dir, 'neat_env', 'models', filename)
        test_agent(agent_path=model_path, enable_flightgear=True)

if __name__ == "__main__":
    main()
    #test_agent_result(filename='')
from flight_sim_test import test_flight_sim
from neat_env.assistant import run_evolution
from neat_env.agent_test import test_agent
import os

def test():
    test_flight_sim(action=[0.0, 0.0, 1.0], steps=2500, Hz=1, enable_flightgear=True, default_runway="KSEA (Seattle) - Runway 34R")

def e_from_seed():
    local_dir = os.path.dirname(__file__)
    base_agent = os.path.join(local_dir, 'neat_env', 'models', 'new_teachings_2.pkl')
    run_evolution(learn_runway="KSEA (Seattle) - Runway 34R", generations=100, from_seed=base_agent)

def e_from_gen0():
    run_evolution(learn_runway="KSEA (Seattle) - Runway 34R", generations=100)

def test_agent_result(filename=None):
    if filename != None:
        local_dir = os.path.dirname(__file__)
        model_path = os.path.join(local_dir, 'neat_env', 'models', filename)
        test_agent(agent_path=model_path, enable_flightgear=True, Hz=10, steps=7000)

if __name__ == "__main__":
    #test()
    #e_from_seed()
    #e_from_gen0()
    test_agent_result(filename='2026-05-22_13-48-00_best_agent.pkl')
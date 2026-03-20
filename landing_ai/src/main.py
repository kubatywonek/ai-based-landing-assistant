from jsbsim_wrapper import FlightSimulator
from flight_sim_analysis import test_flight_sim


if __name__ == "__main__":
    env = FlightSimulator()
    test_flight_sim(env, [0.0, 0.0, 0.0], 100)
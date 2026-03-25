from jsbsim_wrapper import FlightSimulator
from flight_sim_analysis import test_flight_sim


if __name__ == "__main__":
    test_flight_sim(action=[0.0, 0.1, 1.0], steps=1000, Hz=10, enable_flightgear=True)
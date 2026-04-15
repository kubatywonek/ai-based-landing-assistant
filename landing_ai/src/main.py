from flight_sim_test import test_flight_sim

def main():
    test_flight_sim(action=[0.0, 0.0, 0.0], steps=1500, Hz=10, enable_flightgear=False, default_runway="KSEA (Seattle) - Runway 34R")

if __name__ == "__main__":
    main()
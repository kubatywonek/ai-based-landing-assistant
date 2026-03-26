from flight_sim_analysis import test_flight_sim

def main():
    test_flight_sim(action=[0.0, 0.1, 1.0], steps=500, Hz=10, enable_flightgear=True)

if __name__ == "__main__":
    main()
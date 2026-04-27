from sim_env.preflight_config import get_jsbsim_config
from sim_env.jsbsim_wrapper import FlightSimulator
import os
import neat
import pickle
import random
from datetime import datetime
import math
import glob

MAX_STEPS = 2500 # Maximum steps per try to prevent infinite loops
HEIGHT_RAND_RANGE = 100  # Maximum randomization coeff for initial height (in feet)
HEADNG_RAND_RANGE = 10  # Maximum randomization coeff for initial heading (in degrees)
GLIDE_RAND_RANGE = 0.75  # Maximum randomization coeff for angle of glide slope (in degrees)
DISTANCE_RAND_RANGE = 300  # Maximum randomization coeff for initial distance from threshold (in feet)
DISTANCE_COEFF = math.tan(math.radians(3))  # Coefficient for ideal altitude based on distance to threshold (3 degrees glide slope)

def run_evolution(from_seed=None, resume=False, learn_runway=None, generations=100, randomize_level=0):
    """
    Runs the NEAT evolutionary algorithm to train a landing assistant for the specified runway.
    :param from_seed: Path to a seed genome file to initialize the population. If None, starts with a random population.
    :param resume: If True, population will be restored from the latest checkpoint in the "neat-checkpoints" directory.
    :param learn_runway: Preset runway to use for training, config panel opens if None.
    :param generations: Number of generations to run the evolution for.
    :param randomize_level: Level of randomization for each generation.
    """

    runway, ic = get_jsbsim_config(preset_runway=learn_runway)
    if runway is None or ic is None:
        print("Configuration error: No runway or initial conditions provided.")
        return

    print("--- Running Evolution ---")
    print("| Runway coordinates: ", runway["lat"], " ", runway["lon"])
    print("| Initial height: ", ic["h_agl"], " ft")
    print("| Initial distance from threshold: ", ic["dist_ft"], " ft")
    print("| Neat initialization...")

    # NEAT CONFIGURATION
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-neat.txt')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                        neat.DefaultSpeciesSet, neat.DefaultStagnation,
                        config_path)
    os.makedirs("neat-checkpoints", exist_ok=True)
    if resume:
        print("| Resuming population from latest checkpoint")
        list_of_files = glob.glob(os.path.join(local_dir, 'neat-checkpoints', 'checkpoint-*'))
        if not list_of_files:
            print("| No checkpoints found, starting with a new population")
            new_population = neat.Population(config)
        else:
            latest_checkpoint = max(list_of_files, key=os.path.getctime)
            print(f"| Resuming population from: {latest_checkpoint}")
            new_population = neat.Checkpointer.restore_checkpoint(latest_checkpoint)
    elif from_seed is not None:
        print("| Reinitializing population from seed")
        new_population = neat.Population(config)
        with open(from_seed, 'rb') as f:
            champion_genome = pickle.load(f)
        for genome_id, genome in new_population.population.items():
            genome.nodes = champion_genome.nodes.copy()
            genome.connections = champion_genome.connections.copy()
            genome.mutate(config.genome_config)
    else: 
        new_population = neat.Population(config)

    new_population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    new_population.add_reporter(stats)
    new_population.add_reporter(neat.Checkpointer(15, filename_prefix="neat-checkpoints/checkpoint-"))

    print("| Neat initialization completed")
    print("| Running evolution...")

    best_agent = new_population.run(lambda genomes, config: evaluate(genomes, config, (runway, ic), randomize_level), n=generations)

    print("\nBest genome:\n{!s}".format(best_agent))
    models_dir = os.path.join(local_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    save_path = os.path.join(models_dir, datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_best_agent.pkl")
    with open(save_path, "wb") as file:
        pickle.dump(best_agent, file)
    return



def evaluate(genomes, config, env_config, randomize):
    """
    Evaluating function that evaluates each genome by scoring the landing performance.
    :param genomes: List of genomes to evaluate.
    :param config: NEAT configuration object.
    :param env_config: Tuple containing runway and initial conditions.
    """
    for genome_id, genome in genomes:
        
        # Randomization
        runway, ic = env_config
        if(randomize != 0):
            if(randomize > 10):
                randomize = 10
            elif(randomize < 0):
                randomize = 0
            ic["h_agl"] += random.uniform(-HEIGHT_RAND_RANGE*randomize, HEIGHT_RAND_RANGE*randomize)
            ic["heading"] += random.uniform(-HEADNG_RAND_RANGE*randomize, HEADNG_RAND_RANGE*randomize)
            ic["glide_slope"] += random.uniform(-GLIDE_RAND_RANGE*randomize, GLIDE_RAND_RANGE*randomize)
            ic["dist_ft"] += random.uniform(-DISTANCE_RAND_RANGE*randomize, DISTANCE_RAND_RANGE*randomize)
        env = FlightSimulator(runway_data=runway, initial_conditions=ic)
        if env is None:
            print("jsbsim error: No environment")
            return

        genome.fitness = 0.0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        state = env.reset()
        done = False
        steps_left = MAX_STEPS

        while not done and steps_left > 0:
            action = net.activate(state)
            state, done, info = env.step(action)
            genome.fitness += calculate_fitness(state, done, info)
            steps_left -= 1
            if done:
                print(f"Agent died after {MAX_STEPS - steps_left} steps. Reason: {info['reason']}")



def calculate_fitness(state, done, info):
    """
    Custom fitness calculation function. NOTE: fitness_treshold = 100 000
    :param state: Current state of the plane.
    :param done: Whether the episode is finished.
    :param info: Additional info from the environment.
    :return: Fitness score for the current step.
    """
    fitness = 0.0
    alt = state[0]
    v_speed = state[1]
    h_speed = state[2]
    pitch = math.degrees(state[3])
    roll = state[4]
    distance = state[5]
    lat_error = state[6]
    heading_error = state[7]

    if done: # Finished
        if info["status"] == "LANDED":
            fitness += 20000                                                     # Great reward for landing
            fitness += max(0, 2000 - abs(lat_error) * 20)                        # Reward for being close to centerline
            fitness += max(0, 2000 - abs(math.degrees(heading_error)) * 150)    # Reward for correct heading
            fitness += max(0, 3000 - abs(v_speed + 3.0) * 300)                   # Reward for smooth vertical speed
            if 0.0 < pitch < 7.0:
                fitness += 1000                                                  # Bonus for proper flare at landing
            elif pitch < 0.0:
                fitness -= 2000                                                  # Penalty for nose-down landing

        elif info["status"] == "OUT_OF_BOUNDS":
            fitness -= 2000
        elif info["status"] == "CRASH":
            fitness -= 5000
        elif info["status"] == "ERROR":
            fitness -= 1000
        else:
            raise ValueError(f"Unknown status: {info['status']}")
    else: #Still flying
        fitness += 0.1                                          # Small reward for surviving each step
        ideal_alt = max(0, -distance * DISTANCE_COEFF)          # Ideal altitude

        fitness -= abs(alt - ideal_alt) / 500.0                 # Penalty for altitude deviation
        fitness -= abs(lat_error) * 0.01                        # Penalty for lateral deviation
        fitness -= abs(heading_error) * 10                      # Penalty for heading deviation
        fitness -= abs(h_speed - 143.00) * 0.02                 # Penalty for horizontal speed deviation
        fitness -= abs(roll) * 5.0                              # Penalty for roll angle

    if math.isnan(fitness) or math.isinf(fitness):
            return -5000.0
    
    return fitness
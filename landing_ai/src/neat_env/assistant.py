from numpy import copy
from sim_env.preflight_config import get_jsbsim_config
from sim_env.jsbsim_wrapper import FlightSimulator
import os
import neat
import pickle
import random
from datetime import datetime
import math
import glob

MAX_STEPS = 4000 # Maximum steps per try to prevent infinite loops
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
    runway, ic = env_config
    for genome_id, genome in genomes:
        
        # Randomization
        if(randomize != 0):
            if(randomize > 10):
                randomize = 10
            elif(randomize < 0):
                randomize = 0
            genome_ic = copy.deepcopy(ic)
            genome_ic["h_agl"] += random.uniform(-HEIGHT_RAND_RANGE*randomize, HEIGHT_RAND_RANGE*randomize)
            genome_ic["heading"] += random.uniform(-HEADNG_RAND_RANGE*randomize, HEADNG_RAND_RANGE*randomize)
            genome_ic["glide_slope"] += random.uniform(-GLIDE_RAND_RANGE*randomize, GLIDE_RAND_RANGE*randomize)
            genome_ic["dist_ft"] += random.uniform(-DISTANCE_RAND_RANGE*randomize, DISTANCE_RAND_RANGE*randomize)
            env = FlightSimulator(runway_data=runway, initial_conditions=genome_ic)
        else:
            env = FlightSimulator(runway_data=runway, initial_conditions=ic)

        if env is None:
            print("jsbsim error: No environment")
            return

        genome.fitness = 0.0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        state = env.reset()
        done = False
        prev_action = action = [0.0, 0.0, -1.0] # Start with no aileron or elevator deflection and no throttle
        steps_left = MAX_STEPS

        while not done and steps_left > 0:
            action = net.activate(state)
            state, done, info = env.step(action)
            genome.fitness += calculate_fitness(state, done, info, action, prev_action, ic["dist_ft"], steps_left)
            prev_action = action
            steps_left -= 1
            if done:
                print(f"Agent finished after {MAX_STEPS - steps_left} steps. Reason: {info['reason']}")



def calculate_fitness(state, done, info, action, prev_action, dist_ft, steps_left):
    """
    Custom fitness calculation function. NOTE: fitness_treshold = 100 000
    :param state: Current state of the plane.
    :param done: Whether the episode is finished.
    :param info: Additional info from the environment.
    :param action: Action taken by the agent.
    :param prev_action: Previous action taken by the agent.
    :param dist_ft: Initial distance from the runway threshold (in feet).
    :param steps_left: Number of steps left in the episode.
    :return: Fitness score for the current step.
    """
    fitness = 0.0
    alt = state[0]
    v_speed = state[1]
    h_speed = state[2]
    pitch = math.degrees(state[3])
    roll = math.degrees(state[4])
    distance = state[5]
    lat_error = state[6]
    heading_error = state[7]

    if done: # Finished
        if info["status"] == "LANDED":
            fitness += 20000                                                     # Great reward for landing
            fitness += max(0, 2000 - abs(lat_error) * 20)                        # Reward for being close to centerline
            fitness += max(0, 2000 - abs(math.degrees(heading_error)) * 150)     # Reward for correct heading
            fitness += max(0, 3000 - abs(v_speed + 1.5) * 300)                   # Reward for smooth vertical speed
            if 0.0 < pitch < 7.0:
                fitness += 1000                                                  # Bonus for proper flare at landing
            elif pitch < 0.0:
                fitness -= 2000                                                  # Penalty for nose-down landing

        elif info["status"] == "OUT_OF_BOUNDS":
            fitness -= 5000
            fitness += max(0, dist_ft - abs(distance))
        elif info["status"] == "CRASH":
            fitness -= 10000 * steps_left / MAX_STEPS
            fitness += max(0, dist_ft - abs(distance))
        elif info["status"] == "ERROR":
            fitness -= 1000
        else:
            raise ValueError(f"Unknown status: {info['status']}")
    else: #Still flying
        fitness += max(0.0, (dist_ft - abs(distance)) / dist_ft) * 3            # Small reward for surviving towards the runway
        fitness -= 0.05 * (MAX_STEPS - steps_left) / MAX_STEPS                  # Small penalty for taking more time to land
        fitness += 1.0
        
        ideal_alt = max(0, -distance * DISTANCE_COEFF)                          # Ideal altitude
        ideal_vspeed = -h_speed * DISTANCE_COEFF                                # Ideal vertical speed based on horizontal speed to maintain glide slope
        if alt < 20:
            ideal_vspeed = -1.5
        
        fitness -= math.sqrt(abs(v_speed - ideal_vspeed)) * 0.5                  # Penalty for vertical speed deviation from ideal glide slope descent rate
        fitness -= min(0.15, abs(alt - ideal_alt) / 1000.0)                     # Penalty for altitude deviation
        fitness -= min(0.50, abs(lat_error) * 0.05)                                        # Penalty for lateral deviation
        fitness -= min(0.25, abs(heading_error) * 3.0)                                     # Penalty for heading deviation
        fitness -= min(0.15, abs(h_speed - 140.00) * 0.006)                                 # Penalty for horizontal speed deviation
        fitness -= min(0.15, abs(roll) * 0.02)                                             # Penalty for roll angle
        fitness -= min(0.15, abs(pitch) * 0.01)                                            # Penalty for pitch angle
        fitness -= min(0.30, (abs(action[0])**2 + abs(action[1])**2) * 0.3)      # Penalty for excessive control inputs                                                 

        if abs(alt - ideal_alt) < 50 and v_speed > -1.0 and -distance > 100:    # Punish for floating and not descending
            fitness -= 4.0
        
        delta_aileron = abs(action[0] - prev_action[0])
        delta_elevator = abs(action[1] - prev_action[1])
        
        fitness -= min(0.3, (delta_aileron ** 2) * 1.0)
        fitness -= min(0.3, (delta_elevator ** 2) * 0.3)

        if abs(heading_error) > math.radians(30):
            fitness -= 5.0                         # Anti-farming penalty for large heading errors
        if distance > 300:
            fitness -= 5.0                         # Anti-farming penalty for being too far from the runway
        if abs(roll) > 40.0:
            fitness -= 10.0                        # Anti-farming penalty for excessive roll
        if abs(pitch) > 15.0:
            fitness -= 10.0                        # Anti-farming penalty for excessive pitch
        if alt > ideal_alt + 1000:
            fitness -= 10.0                        # Anti-farming penalty for being too high above the glide path
        if v_speed < -40.0:
            fitness -= 50.0                        # Anti-farming penalty for rapid descent
        

    if math.isnan(fitness) or math.isinf(fitness):
            return -5000.0
    
    return fitness
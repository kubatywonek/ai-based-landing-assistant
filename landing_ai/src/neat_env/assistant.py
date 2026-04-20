from sim_env.preflight_config import get_jsbsim_config as config
from sim_env.jsbsim_wrapper import FlightSimulator
import os
import neat
import pickle
import datetime

def run_evolution(learn_runway=None, generations=100):
    """
    Runs the NEAT evolutionary algorithm to train a landing assistant for the specified runway.
    :param learn_runway: Preset runway to use for training, config panel opens if None.
    :param generations: Number of generations to run the evolution for.
    """

    runway, ic = config(preset_runway=learn_runway)
    if runway is None or ic is None:
        print("Configuration error: No runway or initial conditions provided.")
        return
    env = FlightSimulator(runway_data=runway, initial_conditions=ic)
    if env is None:
        print("jsbsim error: No environment")
        return

    print("--- Running Evolution ---")
    print("| Runway coordinates: ", runway["lat"], " ", runway["lon"])
    print("| Initial height: ", ic["h_agl"], " ft")
    print("| Initial distance from threshold: ", ic["dist_ft"], " ft")
    print("| Neat initialization...")

    # NEAT CONFIGURATION
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                        neat.DefaultSpeciesSet, neat.DefaultStagnation,
                        config_path)
    os.makedirs("models", exist_ok=True)
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    os.makedirs("neat-checkpoints", exist_ok=True)
    population.add_reporter(neat.Checkpointer(15, filename_prefix="neat-checkpoints/checkpoint-"))

    print("| Neat initialization completed")
    print("| Running evolution...")

    best_agent = population.run(lambda genomes, config: fitness(genomes, config, (runway, ic), env), n=generations)

    print("\nBest genome:\n{!s}".format(best_agent))
    save_path = os.path.join(local_dir, "models", datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_best_agent.pkl")
    with open(save_path, "wb") as file:
        pickle.dump(best_agent, file)
    return



def fitness(genomes, config, env_config, env):
    """
    Fitness function that evaluates each genome by scoring the landing performance.
    :param genomes: List of genomes to evaluate.
    :param config: NEAT configuration object.
    :param env_config: Tuple containing runway and initial conditions.
    :param env: FlightSimulator instance to use for evaluation.
    """
    runway, ic = env_config
    for genome_id, genome in genomes:
        genome.fitness = 0.0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        state = env.reset()
        done = False
        max_steps = 2500

        while not done and max_steps > 0:
            action = net.activate(state)
            state, done, info = env.step(action)
            genome.fitness += calculate_fitness(state, done, info)
            max_steps -= 1



def calculate_fitness(state, done, info):   #TODO fitness function
    """
    Custom fitness calculation function. NOTE: (fitness_treshold = 100 000)
    :param state: Current state of the plane.
    :param done: Whether the episode is finished.
    :param info: Additional info from the environment.
    :return: Fitness score for the current step.
    """
    fitness = 0.0
    if done: # Finished
        if info["status"] == "LANDED":
            fitness = 0
        elif info["status"] == "OUT_OF_BOUNDS":
            fitness = 0
        elif info["status"] == "CRASH":
            fitness = 0
        elif info["status"] == "ERROR":
            fitness = 0
        else:
            raise ValueError(f"Unknown status: {info['status']}")
    else: #Still flying
        fitness += 0.1 # Small reward for surviving each step
    return fitness
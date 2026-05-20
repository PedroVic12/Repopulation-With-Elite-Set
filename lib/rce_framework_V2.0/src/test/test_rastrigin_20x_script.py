"""
Test script to run the genetic algorithm with the rastrigin function 5 times.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))


from ..AlgEvolutivoRCE.Setup import Setup
from ..AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from ..utils.functions_fitness.functions_benchmarking import rastrigin


def load_params():
    """Load parameters from params.json"""
    params_path = os.path.join(os.path.dirname(__file__), "params.json")
    with open(params_path, "r") as f:
        return json.load(f)


def load_params(params_file="params.json"):
    """Load parameters from JSON file"""
    import json

    # Build the absolute path to the params.json file relative to this script
    script_dir = os.path.dirname(__file__)
    params_path = os.path.join(script_dir, "..", params_file)  # Go up one level to src/
    with open(params_path, "r") as f:
        return json.load(f)


def run_rastrigin_test(run_num, params=None):
    """Run a single test with the rastrigin function"""
    print(f"\n{'='*80}")
    print(f"RUN {run_num + 1}/5 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")

    # Load default parameters if none provided
    if params is None:
        params = load_params()

    # Set up configuration for rastrigin using params from JSON
    params["funcao_objetivo"] = "rastrigin"
    params["decision_variables"] = params.get("IND_SIZE", 5)  # Use IND_SIZE from params
    params["lower_bound"] = -5.12  # Rastrigin's recommended bounds
    params["upper_bound"] = 5.12  # Rastrigin's recommended bounds

    # Create output directory for this run
    output_dir = os.path.join("output", "rastrigin_tests", f"run_{run_num + 1}")
    os.makedirs(output_dir, exist_ok=True)

    # Get bounds from params
    lower_bound = params.get("LIMITE_VAR", [0])[0]  # First value in LIMITE_VAR array
    upper_bound = (
        params.get("LIMITE_VAR", [30])[1]
        if len(params.get("LIMITE_VAR", [])) > 1
        else 30
    )  # Second value in LIMITE_VAR array or 30

    # Create a wrapper function that handles the rastrigin evaluation
    def rastrigin_wrapper(individual, setup=None):
        try:
            # Ensure individual is a list of numbers
            if not isinstance(individual, (list, tuple)):
                individual = [individual]

            # Convert to float and scale from [lower_bound, upper_bound] to [-5.12, 5.12]
            scaled_individual = []
            for x in individual:
                try:
                    x_float = float(x)
                    # Scale from [lower_bound, upper_bound] to [-5.12, 5.12]
                    scaled_x = (
                        (x_float - lower_bound) / (upper_bound - lower_bound)
                    ) * (5.12 * 2) - 5.12
                    scaled_individual.append(scaled_x)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Could not scale value {x} (Error: {e}), using 0")
                    scaled_individual.append(0.0)

            # Calculate fitness
            fitness = rastrigin(scaled_individual)
            print(
                f"Evaluating individual: {individual} -> {scaled_individual} -> {fitness}"
            )  # Debug print

            # Ensure we return a tuple with a single float
            return (
                (float(fitness),)
                if not isinstance(fitness, tuple)
                else tuple(float(f) for f in fitness)
            )

        except Exception as e:
            print(f"Error in rastrigin_wrapper: {e}")
            import traceback

            traceback.print_exc()
            return (float("inf"),)  # Return worst possible fitness on error

    # Set up algorithm parameters from params.json
    params.update(
        {
            "MUTATION_RATE": params.get("MUTACAO", 0.1),
            "CROSSOVER_RATE": params.get("CROSSOVER", 0.8),
            "POP_SIZE": params.get("POP_SIZE", 50),
            "NUM_GENERATIONS": params.get("NUM_GENERATIONS", 100),
            "RCE_REPOPULATION_GENERATIONS": params.get(
                "RCE_REPOPULATION_GENERATIONS", 50
            ),
            "funcao_objetivo": "rastrigin",
            "decision_variables": params.get("IND_SIZE", 5),
            "lower_bound": -5.12,
            "upper_bound": 5.12,
        }
    )

    print(f"\nRunning with parameters:")
    print(f"- Population size: {params['POP_SIZE']}")
    print(f"- Generations: {params['NUM_GENERATIONS']}")
    print(f"- Mutation rate: {params['MUTATION_RATE']}")
    print(f"- Crossover rate: {params['CROSSOVER_RATE']}")
    print(f"- Variable bounds: {params.get('LIMITE_VAR', [0, 30])}")

    # Create Setup instance with parameters
    # tamanho_hash is used for some internal calculations, defaulting to 0 for the rastrigin test
    setup = Setup(params, fitness_function=rastrigin_wrapper, tamanho_hash=0)

    # Create and run the genetic algorithm
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=True)

    # Run the algorithm with progress tracking
    start_time = time.time()
    best_individual, logbook, best_variables = alg.run()
    elapsed_time = time.time() - start_time

    # Print results with robust fitness value handling
    print("\n" + "=" * 50)
    print(f"RUN {run_num + 1} COMPLETED")
    print(f"Best solution: {best_variables}")
    print(f"Fitness values: {best_individual.fitness.values}")
    print(f"Fitness valid: {best_individual.fitness.valid}")
    print(f"Fitness weights: {best_individual.fitness.weights}")

    # Safely get the best fitness value
    if hasattr(best_individual.fitness, "values") and best_individual.fitness.values:
        best_fitness = (
            best_individual.fitness.values[0]
            if len(best_individual.fitness.values) > 0
            else float("inf")
        )
    else:
        best_fitness = float("inf")

    print(f"Best fitness: {best_fitness}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print("=" * 50 + "\n")

    # Safely get the best fitness value for the return dictionary
    try:
        if (
            best_individual
            and hasattr(best_individual, "fitness")
            and best_individual.fitness.valid
        ):
            if (
                hasattr(best_individual.fitness, "values")
                and best_individual.fitness.values
            ):
                best_fitness = float(best_individual.fitness.values[0])
            else:
                # If values is empty but fitness is valid, try to evaluate again
                fitness = setup.toolbox.evaluate(best_individual)
                best_fitness = (
                    float(fitness[0])
                    if isinstance(fitness, (list, tuple))
                    else float(fitness)
                )
        else:
            # If no valid fitness, find best from population
            valid_fitness = [
                ind.fitness.values[0]
                for ind in alg.POPULATION
                if hasattr(ind.fitness, "values")
                and ind.fitness.values
                and ind.fitness.valid
            ]
            best_fitness = min(valid_fitness) if valid_fitness else float("inf")
    except Exception as e:
        print(f"Error getting best fitness: {e}")
        best_fitness = float("inf")

    return {
        "run": run_num + 1,
        "best_solution": best_variables,
        "best_fitness": best_fitness,
        "fitness_values": getattr(best_individual.fitness, "values", None),
        "fitness_valid": getattr(best_individual.fitness, "valid", False),
        "elapsed_time": elapsed_time,
        "logbook": logbook,
    }


def main():
    # Load parameters
    params = load_params()

    # Create main output directory
    os.makedirs(os.path.join("output", "rastrigin_tests"), exist_ok=True)

    # Run 5 tests
    num_executions = input("Digite a quantidade de vezes que voce quer simular :  ")
    results = []
    print(
        f"Voce escolheu realizar a simulação da função RASTRIGIN {num_executions} vezes!"
    )
    for i in range(num_executions):
        result = run_rastrigin_test(i, params.copy())
        results.append(result)

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for i, result in enumerate(results):
        print(
            f"Run {i+1}: Fitness = {result['best_fitness']:.6f}, "
            f"Time = {result['elapsed_time']:.2f}s, "
            f"Solution = {result['best_solution']}"
        )

    avg_fitness = sum(r["best_fitness"] for r in results) / len(results)
    avg_time = sum(r["elapsed_time"] for r in results) / len(results)

    print("\n" + "-" * 40)
    print(f"Average fitness: {avg_fitness:.6f}")
    print(f"Average time: {avg_time:.2f} seconds")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

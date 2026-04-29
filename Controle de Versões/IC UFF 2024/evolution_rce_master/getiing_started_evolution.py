from src.models.getting_started import Setup, DataExploration, Algorithm
import json

from pathlib import Path


def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params


def main():
    params = load_params("evolution_rce_master/src/db/parameters.json")
    print(params)

    setup = Setup(params)
    alg = Algorithm(setup)
    data_visual = DataExploration()

    pop, logbook, hof = alg.run()

    data_visual.visualize(logbook, pop, repopulation=True)


if __name__ == "__main__":
    main()

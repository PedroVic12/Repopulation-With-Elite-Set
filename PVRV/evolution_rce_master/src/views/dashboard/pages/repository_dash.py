import json


class Repository:
    def __init__(self) -> None:
        pass

    def buscar_json_evolutivos(self, path):
        with open(path, "r") as file:
            params = json.load(file)
        return params

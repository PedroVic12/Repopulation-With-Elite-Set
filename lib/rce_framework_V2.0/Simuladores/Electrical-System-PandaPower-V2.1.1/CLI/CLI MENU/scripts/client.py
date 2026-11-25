class ClientModel:
    def __init__(self, data=None):
        self.data = data or {}

    def save(self):
        print(f"Salvando dados de Client...")

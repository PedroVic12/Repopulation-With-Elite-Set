
from .....tools.database_controller import DatabaseController
from .....global_settings import SRC_DIR

class ConfigManager:
    """Model - Gerencia o acesso aos arquivos de configuração JSON."""

    def __init__(self):
        self.db_controller = DatabaseController(SRC_DIR)

    def get_params(self):
        return self.db_controller.get_params()

    def get_options(self):
        return self.db_controller.get_options()

    def save_params(self, params):
        return self.db_controller.save_params(params)

    def save_options(self, options):
        return self.db_controller.save_options(options)

    def consolidate_results(self):
        self.db_controller.consolidate_results()
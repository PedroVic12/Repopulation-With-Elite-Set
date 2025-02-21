from rich.console import Console
from rich.theme import Theme
from rich.traceback import install

install()

class Logger:
    def __init__(self):
        self.console = Console(theme=Theme({
            "success": "bold green",
            "warning": "yellow",
            "error": "bold red",
            "info": "white"  # Added "info" level for default blue color
        }))

    def log(self, message, level="info"):  # Changed default level to "info"
        """Logs a message with the specified level and color."""
        if level == "success":
            self.console.print(f"[success]{message}[/]")
        elif level == "warning":
            self.console.print(f"[warning]{message}[/]")
        elif level == "error":
            self.console.print(f"[error]{message}[/]")
        else:
            self.console.print(f"[info]{message}[/]") # Changed to "info" to use blue color


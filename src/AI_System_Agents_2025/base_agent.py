from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import asyncio
import logging

class Agent(ABC):
    """Classe base abstrata para todos os agentes do sistema"""
    
    def __init__(
        self,
        agent_id: int,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        api_key: str,
        model: str = "gemini-2.0-pro"
    ):
        self.id = agent_id
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.api_key = api_key
        self.model = model
        self.memory = {}  # Memória simples do agente
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def process(self, task_description: str, context: Dict[str, Any] = None) -> str:
        """
        Processa uma tarefa e retorna o resultado
        
        Args:
            task_description: Descrição da tarefa a ser realizada
            context: Contexto adicional para a tarefa (opcional)
            
        Returns:
            Resultado do processamento da tarefa (geralmente em markdown)
        """
        pass
    
    def generate_system_prompt(self) -> str:
        """Gera o prompt do sistema para o agente"""
        return f"""Você é {self.name}, um {self.role}.

Seu objetivo é: {self.goal}

Backstory: {self.backstory}

Responda sempre de acordo com seu papel, mantendo sua personalidade.
Seu resultado deve ser formatado em markdown conforme esperado no 'expected_output'.
"""
    
    def update_memory(self, key: str, value: Any) -> None:
        """Atualiza a memória do agente"""
        self.memory[key] = value
    
    def get_memory(self, key: str) -> Any:
        """Recupera um valor da memória do agente"""
        return self.memory.get(key)
    
    def clear_memory(self) -> None:
        """Limpa a memória do agente"""
        self.memory = {}
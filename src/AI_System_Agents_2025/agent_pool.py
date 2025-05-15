from typing import Dict, List, Optional, Type, Any
import logging

from agemts; import pesquisador_agent

from config import settings

logger = logging.getLogger("agent_pool")

class AgentPool:
    """
    Pool de agentes que gerencia a criação, acesso e ciclo de vida dos agentes
    """
    
    def __init__(self):
        self.agents: Dict[int, Agent] = {}
        self.agent_types = {
            "researcher": ResearcherAgent,
            "writer": WriterAgent,
            "programmer": ProgrammerAgent,
            "marketing": MarketingAgent
        }
    
    def register_agent(
        self,
        agent_id: int,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        agent_type: str = None
    ) -> Agent:
        """
        Registra um novo agente no pool
        
        Args:
            agent_id: ID único do agente
            name: Nome do agente
            role: Função/papel do agente
            goal: Objetivo do agente
            backstory: História de fundo do agente
            agent_type: Tipo específico do agente (opcional)
            
        Returns:
            Instância do agente criado
        """
        # Determinar o tipo de agente com base no nome ou função
        if not agent_type:
            if "pesquis" in name.lower() or "research" in role.lower():
                agent_type = "researcher"
            elif "redator" in name.lower() or "writer" in role.lower():
                agent_type = "writer"
            elif "program" in name.lower() or "develop" in role.lower():
                agent_type = "programmer"
            elif "market" in name.lower() or "SEO" in role:
                agent_type = "marketing"
            else:
                agent_type = "researcher"  # Tipo padrão
        
        # Obter a classe apropriada
        agent_class = self.agent_types.get(agent_type.lower(), ResearcherAgent)
        
        # Criar a instância do agente
        agent = agent_class(
            agent_id=agent_id,
            name=name,
            role=role,
            goal=goal,
            backstory=backstory,
            api_key=settings.GEMINI_API_KEY
        )
        
        # Armazenar no pool
        self.agents[agent_id] = agent
        logger.info(f"Agente {name} (ID: {agent_id}, Tipo: {agent_type}) registrado no pool")
        
        return agent
    
    def get_agent(self, agent_id: int) -> Optional[Agent]:
        """Obtém um agente do pool pelo ID"""
        return self.agents.get(agent_id)
    
    def remove_agent(self, agent_id: int) -> bool:
        """Remove um agente do pool"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agente ID {agent_id} removido do pool")
            return True
        return False
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """Lista todos os agentes no pool"""
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "goal": agent.goal,
                "backstory": agent.backstory
            }
            for agent in self.agents.values()
        ]
    
    def clear(self) -> None:
        """Limpa o pool de agentes"""
        self.agents = {}
        logger.info("Pool de agentes limpo")
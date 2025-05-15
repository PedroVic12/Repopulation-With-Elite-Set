import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from agents.base_agent import Agent
from orchestrator.agent_pool import AgentPool
from utils.memory import SharedMemory

logger = logging.getLogger("task_manager")

class TaskManager:
    """
    Gerenciador de tarefas responsável por orquestrar a execução de tarefas
    pelos agentes no sistema.
    """
    
    def __init__(self, agent_pool: AgentPool):
        self.agent_pool = agent_pool
        self.shared_memory = SharedMemory()
        self.task_history = []
        
    async def execute_tasks(self, tema: str, tasks: List[Dict[str, Any]]) -> Dict[int, str]:
        """
        Executa uma série de tarefas utilizando os agentes apropriados
        
        Args:
            tema: Tema ou assunto principal das tarefas
            tasks: Lista de tarefas a serem executadas
            
        Returns:
            Dicionário com os resultados das tarefas, mapeado pelo ID do agente
        """
        logger.info(f"Iniciando execução de {len(tasks)} tarefas sobre: {tema}")
        
        # Armazenar o tema na memória compartilhada
        self.shared_memory.set("tema", tema)
        
        # Resultados das tarefas
        results = {}
        
        # Executar tarefas sequencialmente (pode ser alterado para paralelo conforme necessário)
        for task in sorted(tasks, key=lambda t: t["agentId"]):
            agent_id = task["agentId"]
            description = task["description"]
            expected_output = task["expected_output"]
            attempts = task.get("attempts", 1)
            
            # Obter o agente do pool
            agent = self.agent_pool.get_agent(agent_id)
            if not agent:
                logger.error(f"Agente ID {agent_id} não encontrado no pool")
                continue
                
            # Preparar contexto para o agente
            context = {
                "tema": tema,
                "expected_output": expected_output,
                "shared_memory": self.shared_memory.get_all(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Executar a tarefa com até N tentativas
            result = None
            errors = []
            
            for attempt in range(1, attempts + 1):
                try:
                    logger.info(f"Executando tarefa para o agente {agent.name} (tentativa {attempt}/{attempts})")
                    result = await agent.process(description, context)
                    logger.info(f"Tarefa concluída para o agente {agent.name}")
                    
                    # Armazenar resultado na memória compartilhada
                    memory_key = f"result_{agent_id}"
                    self.shared_memory.set(memory_key, result)
                    
                    # Registrar no histórico de tarefas
                    self.task_history.append({
                        "agent_id": agent_id,
                        "agent_name": agent.name,
                        "description": description,
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    })
                    
                    # Armazenar resultado
                    results[agent_id] = result
                    break
                    
                except Exception as e:
                    error_msg = f"Erro na execução da tarefa (tentativa {attempt}): {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    
                    # Esperar antes de tentar novamente
                    if attempt < attempts:
                        await asyncio.sleep(2)
            
            # Se todas as tentativas falharam
            if agent_id not in results:
                error_message = "\n".join(errors)
                results[agent_id] = f"**ERRO**: Não foi possível completar a tarefa após {attempts} tentativas.\n\n```\n{error_message}\n```"
                
                # Registrar falha no histórico
                self.task_history.append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "description": description,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": error_message
                })
        
        logger.info(f"Todas as tarefas concluídas para o tema: {tema}")
        return results
    
    def get_task_history(self) -> List[Dict[str, Any]]:
        """Retorna o histórico de tarefas executadas"""
        return self.task_history
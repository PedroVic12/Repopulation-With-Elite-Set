import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from config import settings
from agents.base_agent import Agent
from orchestrator.task_manager import TaskManager
from orchestrator.agent_pool import AgentPool

# Criar a aplicação FastAPI
app = FastAPI(title="Sistema de Agentes IA", description="API para o sistema de agentes IA")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substituir por origens específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar o gerenciador de tarefas e pool de agentes
agent_pool = AgentPool()
task_manager = TaskManager(agent_pool)

# Modelos de dados
class AgentConfig(BaseModel):
    id: int
    name: str
    role: str
    goal: str
    backstory: str
    expected_output: str

class Task(BaseModel):
    description: str
    agentId: int
    expected_output: str
    attempts: int = 2

class TaskRequest(BaseModel):
    tema: str
    agents: List[AgentConfig]
    tasks: List[Task]

# Conexões WebSocket ativas
active_connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Receber mensagem do cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "start_tasks":
                # Iniciar tarefas assíncronas
                task_data = TaskRequest(**message["data"])
                asyncio.create_task(process_tasks(task_data, websocket))
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"Erro no WebSocket: {str(e)}")
        if websocket in active_connections:
            active_connections.remove(websocket)

async def process_tasks(task_request: TaskRequest, websocket: WebSocket):
    """Processa as tarefas solicitadas pelo cliente"""
    try:
        # Configurar os agentes no pool
        for agent_config in task_request.agents:
            agent_pool.register_agent(
                agent_id=agent_config.id,
                name=agent_config.name,
                role=agent_config.role,
                goal=agent_config.goal,
                backstory=agent_config.backstory
            )
        
        # Iniciar o processamento das tarefas
        results = await task_manager.execute_tasks(
            task_request.tema,
            task_request.tasks
        )
        
        # Combinar os resultados em um único markdown
        markdown_result = combine_results(results, task_request.agents)
        
        # Enviar resultado para o cliente
        await websocket.send_json({
            "type": "task_results",
            "status": "success",
            "markdown_result": markdown_result
        })
        
    except Exception as e:
        print(f"Erro ao processar tarefas: {str(e)}")
        await websocket.send_json({
            "type": "task_results",
            "status": "error",
            "message": str(e)
        })

def combine_results(results: Dict[int, str], agents: List[AgentConfig]) -> str:
    """Combina os resultados de todos os agentes em um único markdown"""
    combined = f"# Relatório: {task_request.tema}\n\n"
    
    for agent in sorted(agents, key=lambda a: a.id):
        if agent.id in results:
            combined += f"## {agent.name} ({agent.role})\n\n"
            combined += results[agent.id]
            combined += "\n\n---\n\n"
    
    return combined

@app.get("/")
def read_root():
    return {"message": "Sistema de Agentes IA"}

@app.get("/agents")
def list_agents():
    return agent_pool.list_agents()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9400, reload=True)
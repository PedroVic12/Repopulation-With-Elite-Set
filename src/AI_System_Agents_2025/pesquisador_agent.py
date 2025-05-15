"""
researcher.py - Implementação do agente pesquisador
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
import json

from google import genai
from agents.base_agent import Agent
from utils.tools import search_web, extract_relevant_information

class ResearcherAgent(Agent):
    """
    Agente especializado em pesquisar informações na web e organizar
    conhecimento relevante sobre um tópico.
    """
    
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
        super().__init__(agent_id, name, role, goal, backstory, api_key, model)
        # Inicializar o cliente Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.logger = logging.getLogger(f"agent.researcher.{name}")
    
    async def process(self, task_description: str, context: Dict[str, Any] = None) -> str:
        """
        Processa uma tarefa de pesquisa
        
        Args:
            task_description: Descrição da tarefa de pesquisa
            context: Contexto adicional para a tarefa
            
        Returns:
            Relatório de pesquisa em formato markdown
        """
        self.logger.info(f"Iniciando pesquisa sobre: {task_description}")
        
        context = context or {}
        tema = context.get("tema", "")
        expected_output = context.get("expected_output", "")
        
        # Etapa 1: Planejar a pesquisa
        search_plan = await self._create_search_plan(tema, task_description)
        self.logger.debug(f"Plano de pesquisa: {search_plan}")
        
        # Etapa 2: Realizar buscas na web (simulado por enquanto)
        search_results = []
        for query in search_plan["search_queries"]:
            self.logger.debug(f"Executando busca: {query}")
            results = await search_web(query)
            search_results.append({
                "query": query,
                "results": results
            })
        
        # Etapa 3: Extrair e organizar informações relevantes
        organized_info = await extract_relevant_information(search_results, tema)
        self.logger.debug("Informações organizadas obtidas")
        
        # Etapa 4: Gerar o relatório final
        report = await self._generate_report(
            tema=tema,
            task_description=task_description,
            search_results=search_results,
            organized_info=organized_info,
            expected_output=expected_output
        )
        
        self.logger.info("Pesquisa concluída e relatório gerado")
        return report
    
    async def _create_search_plan(self, tema: str, task_description: str) -> Dict[str, Any]:
        """Cria um plano de pesquisa com consultas específicas"""
        prompt = f"""
        Você é um especialista em planejamento de pesquisa. 
        Crie um plano de pesquisa para o seguinte tema:
        
        Tema: {tema}
        Tarefa: {task_description}
        
        Seu plano deve incluir:
        1. Subtópicos principais para investigação
        2. 5 consultas de pesquisa específicas e bem formuladas
        3. Aspectos prioritários a serem investigados
        
        Retorne o plano como um JSON estruturado com as chaves 'subtopics', 'search_queries' e 'priorities'.
        """
        
        response = await self.model.generate_content_async(prompt)
        response_text = response.text
        
        # Extrair o JSON da resposta
        try:
            # Buscar texto entre ``` se existir
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text.strip()
                
            return json.loads(json_text)
        except Exception as e:
            self.logger.error(f"Erro ao extrair JSON do plano de pesquisa: {str(e)}")
            # Retornar um plano básico em caso de erro
            return {
                "subtopics": ["Visão geral", "Aplicações", "Tendências atuais"],
                "search_queries": [
                    f"{tema} visão geral",
                    f"{tema} aplicações práticas",
                    f"{tema} tendências recentes",
                    f"{tema} melhores práticas",
                    f"{tema} pesquisas acadêmicas"
                ],
                "priorities": ["Informações atualizadas", "Exemplos práticos", "Dados estatísticos"]
            }
    
    async def _generate_report(
        self,
        tema: str,
        task_description: str,
        search_results: List[Dict[str, Any]],
        organized_info: Dict[str, Any],
        expected_output: str
    ) -> str:
        """Gera o relatório final com base nas informações coletadas"""
        
        # Formatar os resultados da pesquisa para incluir no prompt
        formatted_info = json.dumps(organized_info, indent=2, ensure_ascii=False)
        
        prompt = f"""
        {self.generate_system_prompt()}
        
        # Tarefa
        {task_description}
        
        # Tema Principal
        {tema}
        
        # Informações Coletadas
        {formatted_info}
        
        # Formato Esperado de Saída
        {expected_output}
        
        Crie um relatório completo em markdown seguindo o formato esperado de saída.
        O relatório deve ser bem estruturado, com seções claras, introdução, desenvolvimento e conclusão.
        Utilize os dados coletados de forma eficiente e informativa.
        """
        
        response = await self.model.generate_content_async(prompt)
        return response.text
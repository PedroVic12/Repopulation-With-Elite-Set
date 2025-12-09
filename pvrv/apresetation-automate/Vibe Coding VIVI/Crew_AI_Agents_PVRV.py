# pip install google-generativeai dotenv rich 

# https://aistudio.google.com/app/apikey


import google.generativeai as genai
from dotenv import load_dotenv
import os
from rich.console import Console
from rich import print


console = Console()

load_dotenv()

GOOGLE_API_KEY = "AIzaSyBBA5Xy4pGZhEpU5QOueka3Cj1SqUfqBcg"

APIKEY = "AIzaSyBBA5Xy4pGZhEpU5QOueka3Cj1SqUfqBcg"

if not APIKEY:
    raise ValueError("API key nao encontrada!")


genai.configure(api_key=APIKEY)

modelo = genai.GenerativeModel("gemini-2.5-flash")


class Agent:
    def __init__(self,role, goal, backstory):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        console.print(f"[b blue] AGENTE CRIADO [b blue] Agente [green] {self.role} [/green]")
    

    def execute(self, task, tentativas, tema):

        console.print(f"\n[b yellow]EXECUTANDO TAREFA [b yellow] Agente [green] {self.role} [/green]")
        
        results = []

        for i in range(tentativas):
            prompt = f""" Role: {self.role} \n Goal: {self.goal} \n Backstory: {self.backstory} \n Task: {task} \n Tema: {tema} \n """

            console.print(f"[b grey] Tentativa {i+1}- {tentativas} [/b grey]")

            response = modelo.generate_content(prompt)

            results.append(response.text)

            print(f"Resposta da tentativa {i+1}: {response.text}")


        # juntar as respostas
        print("CONSOLIDANDO OS RESULTADOS")
        consolidated_prompt = f""" Baseado nas tentativas {tentativas}, me de uma resposta consolidada a partir dos resultados {results}"""
        final_response = modelo.generate_content(consolidated_prompt)
        console.print(f"[b green] RESPOSTA FINAL [b green] Agente [green] {self.role} [/green]")


        return final_response.text
    

    def responde(self, tema):
        console.print(f"[b blue] RESPONDENDO [b blue] Agente [green] sobre o tema {tema} [/green]")
        response = modelo.generate_content(tema)
        console.print(f"[b green] RESPOSTA {response.text} [/green]")


    def gerar_markdown(self,content):
        formatted_content = content.replace("\\n", "\n\n")

        try:
            # save to a markdown file in the current directory
            with open("./documento.md", "w") as file:
                file.write(formatted_content)
                
            console.print("[b green] RELATORIO GERADO: documento.md [/b green]")
        except Exception as e:
            print("ERRO AO CRIAR O ARQUIVO",e)
        

class Task:
    def __init__(self,description, agent, expected_output, tentativas):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
        self.tentativas = tentativas
        

    
class Crew:
    def __init__(self,agents, tasks):
        self.agents = agents
        self.tasks = tasks
        print("EQUIPE CRIADA")
        
        for agent in self.agents:
            console.print(f"[b green] {agent.role} [/b green]")
        console.print("[b yellow] TAREFAS A SEREM EXECUTADAS DA EQUIPE [/b yellow]")
            
        for task in self.tasks:
            console.print(f"[b green] {task.description} - Agente: {task.agent.role} [/b green]")

    # MÉTODO EXECUTE_TASKS MODIFICADO
    def execute_tasks(self, inputs):
        print("\nINICIANDO AS TAREFAS DA EQUIPE:")
        task_outputs = {}
        context = inputs["tema"] # O contexto inicial é o tema

        for i, task in enumerate(self.tasks):
            console.print(f"[b cyan] INICIANDO A TAREFA {i+1}: {task.description} [/b cyan] - AGENTE: {task.agent.role}")
            
            # O contexto agora inclui o tema original e os resultados das tarefas anteriores
            full_context = f"Contexto atual: {context}\n\nTarefa: {task.description}"
            
            resultado = task.agent.execute(full_context, task.tentativas, inputs["tema"])
            
            # Armazena o resultado da tarefa atual
            task_outputs[task.agent.role] = resultado
            
            # Atualiza o contexto para a proxima tarefa com o resultado da tarefa atual
            context += f"\n\nResultado da tarefa '{task.description}' pelo agente {task.agent.role}:\n{resultado}"
            
            console.print(f"[b cyan] TAREFA {i+1} CONCLUIDA [/b cyan] - AGENTE: {task.agent.role}")

        # Retorna o resultado da última tarefa, que é o produto final consolidado.
        return list(task_outputs.values())


tema ={
    "Espiritimsmo":"Como posso saber sobre espiritismo, astronomia e engenharia eletrica e onde cada assunto é interligado. Me mostre respostas baseado na literatura e em artigos cientificos",

     "Ciencias":"",

     "TDAH": " Como ser uma pessoa melhor"
}


# --- LÓGICA PRINCIPAL COM A ORDEM CORRETA ---

# Instancias dos agentes e tarefas (sem alterações)
buscador = Agent(
    role="Pesquisador",
    goal="Pesquisar usando fontes relevantes sobre o assunto, encontrar informações detalhadas e recursos confiáveis para guiar alguém",
    backstory="Você é um pesquisador apaixondo pela Vivi, experiente e está sempre em busca de informações novas e relevantes.faça um relatório estruturado contendo seções de cada pesquisa com o link disponivel"
)

redator = Agent(
    role="Redator",
    goal="Escrever um guia prático e didático em formato Markdown sobre como se especializar sobre o assunto,com foco em fornecer um caminho de aprendizado claro e recursos úteis para iniciantes",
    backstory="Você é um redator técnico experiente com paixão por ensinar e compartilhar conhecimento. Você tem a habilidade de transformar informações complexas em explicações simples e acionáveis, mantendo um tom encorajador e motivador para novos desenvolvedores. Você se preocupa com a clareza, a organização e a praticidade do conteúdo"
)

chefe = Agent(
    role="Coordenador de Conteúdo",
    goal="Integrar os resultados da pesquisa e da redação em um guia final em portugues do brasil coeso, organizado e bem referenciado.",
    backstory="Você é um coordenador experiente com um histórico comprovado de gerenciamento de projetos de conteúdo. Você tem a capacidade de analisar informações de diversas fontes, identificar os pontos chave e garantir que o produto final seja bem estruturado, preciso e atenda aos objetivos definidos."
)

pesquisa = Task(
    description=f"Pesquisar sobre {tema} com as fontes mais recentes e confiáveis",
    agent=buscador,
    expected_output="Um arquivo markdown bem escrito e objetivo, com uma estrutura clara (títulos e subtítulos), explicações didáticas.",
    tentativas=2
)

escrita = Task(
    description=f"Com base no tema e na pesquisa já realizada, escrever um artigo em formato markdown sobre {tema}",
    agent=redator,
    expected_output="Arquivo markdown bem escrito e objetivo de forma clara e didática com parágrafos contendo Introdução, Desenvolvimento, links para recursos relevantes e uma conclusão inspiradora",
    tentativas=2
)



integracao = Task(
    description=f"Analisar o relatório de pesquisa fornecido pelo 'buscador' e o artigo escrito pelo 'redator'. Integrar os links de recursos encontrados na pesquisa ao longo do artigo, garantindo que o guia final seja completo, bem referenciado e atenda ao objetivo de ajudar alguém a se especializar nas tecnologias especificadas.",
    agent=chefe,
    expected_output= "Um artigo final em formato Markdown e na escrito em portugues do brasil  que incorpora os resultados da pesquisa (incluindo links) de forma fluida e organizada, apresentando um guia completo e bem referenciado sobre o tema usando Objetivo, Introdução, Desenvolvimento e Conclusão",
    tentativas=1 # Apenas uma tentativa para a consolidação final
)

# CORRIGINDO A ORDEM DAS TAREFAS
equipe = Crew(
    agents=[buscador, redator, chefe],
    tasks=[pesquisa, escrita, integracao] # Ordem lógica: Pesquisar -> Escrever -> Integrar
)

prompt = """
Organizar meu dia de segunda, quarta e sexta organizar meu dia para escrever relatorio e terça e quinta organizar para focar na planilha de gestão
"""

entrada = {"tema": prompt}

resultados = equipe.execute_tasks(inputs=entrada)

console.print("\n[b green] RESULTADOS FINAIS DAS TAREFAS [/b green]")
for i, result in enumerate(resultados):
    console.print(f"[b] Resultado da Tarefa {i+1}:[/b]")
    print(result)
    print("="*30)

# O resultado final é o último da lista, gerado pelo agente 'chefe'
resultado_final = resultados[-1]

# Gerar o markdown com o resultado final e consolidado
chefe.gerar_markdown(resultado_final)
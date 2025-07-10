#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 10 12:07:58 2025

@author: pedrov12
"""


#! TUTORIAL DAG - AIRFLOW PARA ENGENHARIA DE DADOS

from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
import pandas as pd
import requests
import json

def captura_dados():
    url = ""
    response = requests.get(url)
    df = pd.DataFrame(json.load(response.content))
    quantidade = len(df.index)
    return quantidade

def isValidate():
    if (qtd > 1000):
        return "valida"
    return "nao_valida"

def init_dag():
    with DAG("tutorial_dag", start_date = datetime(2025,07,10), schedule_interval = "30 * * * *", catchup = False) as dag:
        
        captura_dados(
            task_id = "caputra_dados",
            python_callable = captura_dados
            )
        
        operacao_valida = BranchPythonOperator(
            task_id = "e_valido"
            python_callable = isValidate
            )
        
        valido = BashOperator(
            task_id = "valido"
            bash_command = "echo 'Testando airflow.... quantidade ok'"
            )
        
        nao_valido = BashOperator(
            task_id = "valido"
            bash_command = "echo 'operação invalida!'"
            )
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
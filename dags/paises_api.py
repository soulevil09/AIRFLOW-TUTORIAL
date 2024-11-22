from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import pandas as pd


def extract():
    """
    Extrai dados da API REST Countries.
    """
    url = "https://restcountries.com/v3.1/all"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Falha na extração de dados")


def transform(ti):
    """
    Transforma os dados extraídos:
    - Converte para DataFrame.
    - Seleciona apenas países com população maior que 50 milhões.
    - Calcula densidade populacional.
    """
    data = ti.xcom_pull(task_ids="extract")

    if data:
        # Criar um DataFrame com os dados extraídos
        df = pd.DataFrame(data)

        # Selecionar colunas relevantes e calcular densidade populacional
        df = df[["name", "population", "area", "region"]].dropna()
        df["nome_comum"] = df["name"].apply(lambda x: x["common"])
        df["densidade_populacional"] = df["population"] / df["area"]

        # Filtrar países com mais de 50 milhões de habitantes
        df = df[df["population"] > 50000000]

        # Selecionar apenas colunas relevantes
        df = df[["nome_comum", "population", "area", "region", "densidade_populacional"]]

        # Retornar como JSON
        return df.to_json(orient="records")
    else:
        raise Exception("Nenhum dado recebido para transformação")


with DAG(dag_id="countries_pipeline", start_date=datetime(2024, 11, 21), schedule_interval="@daily") as dag:

    # Tarefa de extração
    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform,
        provide_context=True,
    )

    # Tarefa de carregamento (print dos dados)
    print_task = BashOperator(
        task_id="print",
        bash_command="echo {{ ti.xcom_pull(task_ids='transform') }}"
    )

    # Definição da ordem das tarefas
    extract_task >> transform_task >> print_task
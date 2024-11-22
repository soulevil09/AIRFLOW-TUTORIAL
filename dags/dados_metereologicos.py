from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import json
import pandas as pd

API_KEY = "b33d441495fcf2b08be7b4dc0dffa890"
CITY = "São Paulo"
BASE_URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}"


def extract():
    """
    Extrai dados da API OpenWeatherMap para uma cidade específica.
    """
    response = requests.get(BASE_URL)

    if response.status_code == 200:
        return json.loads(response.content)
    else:
        raise Exception("Falha na extração de dados")


def transform(ti):
    """
    Transforma os dados extraídos:
    - Converte para DataFrame.
    - Calcula nova coluna: temperatura em Celsius.
    - Seleciona apenas as colunas relevantes.
    """
    data = ti.xcom_pull(task_ids="extract")
    
    if data:

        df = pd.DataFrame([{
            "cidade": data["name"],
            "temperatura_kelvin": data["main"]["temp"],
            "umidade": data["main"]["humidity"],
            "vento_velocidade": data["wind"]["speed"],
            "condicao": data["weather"][0]["description"]
        }])


        df["temperatura_celsius"] = df["temperatura_kelvin"] - 273.15

        df = df[["cidade", "temperatura_celsius", "umidade", "vento_velocidade", "condicao"]]

        return df.to_json(orient="records")
    else:
        raise Exception("Nenhum dado recebido para transformação")


with DAG(dag_id="dados_metereologicos", start_date=datetime(2024, 11, 12), schedule_interval="@daily") as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform,
        provide_context=True,
    )

    print_task = BashOperator(
        task_id="print",
        bash_command="echo {{ ti.xcom_pull(task_ids='transform') }}"
    )

    extract_task >> transform_task >> print_task

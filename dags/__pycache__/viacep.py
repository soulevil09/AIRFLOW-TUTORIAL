from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import json
import pandas as pd


def extract():
    url = "https://viacep.com.br/ws/11700-100/json/"

    response = requests.get(url)

    if response.status_code == 200:
        return json.loads(response.content)


def transform(ti):
    data = ti.xcom_pull(task_ids="extract")

    if data != None:

        df = pd.DataFrame([data])

        df = df[["cep", "logradouro", "complemento", "bairro", "localidade", "estado","uf"]]

        return df.to_json(orient="records")


with DAG(dag_id="viacep", start_date=datetime(2024, 11, 11), schedule_interval="@daily") as dag:

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
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(dag_id='hello', start_date=datetime(2024, 11, 18), schedule_interval='@daily') as dag:
    t1 = BashOperator(task_id='hello', bash_command='echo hello')
    t1
    
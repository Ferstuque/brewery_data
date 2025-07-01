import sys
sys.path.append("airflow_pipeline")

from airflow.models import DAG
from datetime import datetime, timedelta
from operators.brewery_operator import BreweryOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from os.path import join
from airflow.utils.dates import days_ago
from pathlib import Path

# Retries
default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "email_on_failure": False  # Optional
}

# Define DAG configuration
with DAG(dag_id = "BreweryDAG",             # Unique ID for the DAG
         default_args=default_args,         # Retry & alert
         start_date=datetime.now(),         # Start the DAG now
         schedule_interval="@daily"         # DAG runs daily
         ) as dag:
    
    # Base path for data lake organized by stage and partition
    BASE_FOLDER = join(
       str(Path("~/Desktop").expanduser()),
       "Apache Airflow/datalake/{stage}/brewery_data/{partition}",
   )
    
    # Partition format using the current execution date
    # PARTITION_FOLDER_EXTRACT = "extract_date={{ data_interval_start.strftime('%Y-%m-%d') }}"
    PARTITION_FOLDER_EXTRACT = "extract_date={{ data_interval_end.strftime('%Y-%m-%d') }}"

    # Task 1: Extract raw brewery data (Bronze Layer)
    brewery_operator = BreweryOperator(file_path=join(BASE_FOLDER.format(stage="Bronze", partition=PARTITION_FOLDER_EXTRACT),
                                        "brewerydata_{{ ds_nodash }}.json"),
                                        task_id="task_brewery")
    
    # Task 2: Run Spark job to transform raw JSON into structured Parquet (Silver Layer)
    brewery_transform = SparkSubmitOperator(task_id="brewery_transform",
                                           application="/home/enduser/Desktop/Apache Airflow/src/scripts/spark/transformation.py",
                                           name="brewery_transformation",
                                           application_args=["--src", BASE_FOLDER.format(stage="Bronze", partition=PARTITION_FOLDER_EXTRACT),
                                                             "--dest", BASE_FOLDER.format(stage="Silver", partition=""),
                                                             "--process-date", "{{ ds }}"])
    
    # Task 3: Aggregate transformed data to gold layer using Spark
    brewery_aggregate = SparkSubmitOperator(task_id="brewery_aggregate",
                                           application="/home/enduser/Desktop/Apache Airflow/src/scripts/spark/aggregation.py",
                                           name="brewery_aggregation",
                                           application_args=["--src", join(BASE_FOLDER.format(stage="Silver", partition=""), "brewery_data_main"),
                                                             "--dest", BASE_FOLDER.format(stage="Gold", partition=""),
                                                             "--process-date", "{{ ds }}"])
    
# Define task dependencies: extract → transform → aggregate
brewery_operator >> brewery_transform >> brewery_aggregate
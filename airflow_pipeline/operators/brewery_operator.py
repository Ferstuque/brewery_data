import sys
sys.path.append("airflow_pipeline")

from airflow.models import BaseOperator, DAG, TaskInstance
from hook.brewery_hook import BreweryHook
import json
from datetime import datetime
from os.path import join
from pathlib import Path

class BreweryOperator(BaseOperator):

    template_fields = ["file_path"]

    def __init__(self,file_path, **kwargs):
        self.file_path = file_path
        super().__init__(**kwargs)

    def create_parent_folder(self):
        """
        Ensure the destination folder exists before writing the file.
        """
        (Path(self.file_path).parent).mkdir(parents=True, exist_ok=True)
    
    def execute(self, context):
        """
        Main method executed by Airflow during the DAG run.
        Calls the BreweryHook and writes the output to a JSON file line by line.
        """
        self.create_parent_folder()

        with open(self.file_path, "w") as output_file:
            for pg in BreweryHook().run():
                json.dump(pg, output_file, ensure_ascii=False)
                output_file.write("\n")

# Local testing block (bypasses Airflow runtime)
if __name__ == "__main__":

    with DAG(dag_id = "BreweryTest", start_date=datetime.now()) as dag:
        bd = BreweryOperator(file_path=join("datalake/brewery_data",
                                            f"extract_date={datetime.now().date()}",
                                            f"brewerydata_{datetime.now().date().strftime('%Y%m%d')}.json"),
                                            task_id="test_run")
        ti = TaskInstance(task=bd)
        bd.execute(ti.task_id)

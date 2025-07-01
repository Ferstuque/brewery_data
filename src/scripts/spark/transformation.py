from pyspark.sql import functions as f
from os.path import join
from pyspark.sql import SparkSession
import argparse

# Validates the presence of required columns in the input DataFrame
def validate_schema(df):
    expected_columns = {
        "address_1",
        "address_2",
        "address_3",
        "brewery_type",
        "city",
        "country",
        "id",
        "latitude",
        "longitude",
        "name",
        "phone",
        "postal_code",
        "state",
        "state_province",
        "street",
        "website_url"
    }

    actual_columns = set(df.columns)

    missing = expected_columns - actual_columns
    if missing:
        raise ValueError(f"[ERROR] Missing columns in input data: {missing}")
    else:
        print("[INFO] Schema validation passed.")

# Writes the given DataFrame as a single-file Parquet to the specified path
def export_parquet(df, path):
    df.coalesce(1).write.mode('overwrite').parquet(path)

# Main transformation function: reads raw JSON data and writes it to the silver layer in Parquet format
def brewery_transformation(spark, src, dest, process_date):
    df = spark.read.json(src)

    # Validate schema before proceeding
    validate_schema(df)

    table_dest = join(dest, '{table_name}', f'process_date={process_date}')
    export_parquet(df, table_dest.format(table_name='brewery_data_main'))

# Entry point: parses CLI arguments and runs the transformation pipeline
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Spark Brewery Transformation Silver"
    )
    parser.add_argument("--src", required=True)
    parser.add_argument("--dest", required=True)
    parser.add_argument("--process-date", required=True)

    args = parser.parse_args()

    # Initialize Spark session
    spark = SparkSession\
        .builder\
        .appName("brewery_transformation")\
        .getOrCreate()
    
    # Execute the transformation pipeline
    brewery_transformation(spark, args.src, args.dest, args.process_date)

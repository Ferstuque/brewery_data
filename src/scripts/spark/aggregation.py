from pyspark.sql import functions as f
from os.path import join
from pyspark.sql import SparkSession
import argparse

# Validates that required columns are present before aggregation
def validate_aggregation_schema(df):
    required_columns = {"brewery_type", "country", "process_date"}
    actual_columns = set(df.columns)

    missing = required_columns - actual_columns
    if missing:
        raise ValueError(f"[ERROR] Missing required columns for aggregation: {missing}")
    else:
        print("[INFO] Aggregation schema validation passed.")

# Filters the input DataFrame to keep only records with the latest 'process_date'
def filter_by_latest_extract_date(df, spark):
    try:
        latest_date_row = df.agg(f.max('process_date').alias('latest_date')).collect()
        
        if latest_date_row and latest_date_row[0]['latest_date'] is not None:
            latest_date = latest_date_row[0]['latest_date']
            print(f"Filtering data for latest extraction date: {latest_date}")
            
            df_filtered = df.filter(f.col('process_date') == latest_date)
            return df_filtered
        else:
            print("Warning: DataFrame is empty or 'process_date' column is missing. Returning empty DataFrame.")
            return spark.createDataFrame([], schema=df.schema)
            
    except Exception as e:
        print(f"Error while filtering by latest extraction date: {e}")
        return spark.createDataFrame([], schema=df.schema)

# Aggregates the data by brewery type and country, and returns only required columns
def get_aggregate(df):
    df_agg = df.groupBy('brewery_type', 'country')\
        .count()\
        .orderBy('country', ascending=False)
    return df_agg

# Exports the final DataFrame to a single-partition Parquet file
def export_parquet(df, path):
    df.coalesce(1).write.mode('overwrite').parquet(path)

def aggregated_layer(spark, src, dest, process_date):
    df_silver = spark.read.parquet(src)

    # Validate schema before proceeding
    validate_aggregation_schema(df_silver)

    df_silver_latest = filter_by_latest_extract_date(df_silver, spark)
    df_gold = get_aggregate(df_silver_latest)
    export_parquet(df_gold, join(dest, 'brewery_data_main', f'process_date={process_date}'))

# Entry point: parse CLI arguments and run pipeline
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Spark Brewery Transformation Gold"
    )
    parser.add_argument("--src", required=True)
    parser.add_argument("--dest", required=True)
    parser.add_argument("--process-date", required=True)

    args = parser.parse_args()

    # Spark Session
    spark = SparkSession\
        .builder\
        .appName("brewery_aggregation")\
        .getOrCreate()

    # Execute the aggregation pipeline
    aggregated_layer(spark, args.src, args.dest, args.process_date)
import pytest
from pyspark.sql import SparkSession
import sys
import os

# Make sure we can import aggregation.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aggregation import validate_aggregation_schema

# Creates a Spark session fixture
@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder \
        .master("local[1]") \
        .appName("test_aggregation_schema") \
        .getOrCreate()

# Test: should pass when all required columns are present
def test_validate_schema_success(spark):
    data = [
        ("brewpub", "United States", "2025-07-01"),
        ("micro", "Canada", "2025-07-01")
    ]
    columns = ["brewery_type", "country", "process_date"]

    df = spark.createDataFrame(data, columns)

    # Should not raise any exception
    validate_aggregation_schema(df)

# Test: should fail when a required column is missing
def test_validate_schema_missing_column(spark):
    data = [
        ("brewpub", "United States"),
        ("micro", "Canada")
    ]
    columns = ["brewery_type", "country"]  # process_date is missing

    df = spark.createDataFrame(data, columns)

    with pytest.raises(ValueError) as excinfo:
        validate_aggregation_schema(df)

    assert "Missing required columns" in str(excinfo.value)

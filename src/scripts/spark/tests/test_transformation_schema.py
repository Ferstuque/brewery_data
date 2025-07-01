import pytest
import datetime
import sys
import os

# Ensure the path to transformation.py is in PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyspark.sql import SparkSession
from pyspark.sql.types import *

from transformation import validate_schema

# Creates a Spark session fixture
@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder \
        .master("local[1]") \
        .appName("test_transformation_schema") \
        .getOrCreate()

# Test: should pass when all required columns are present
def test_validate_full_schema_success(spark):
    data = [
        (
            "80 Earhart Dr", None, None, "brewpub", "Williamsville", "United States",
            "uuid-123", 42.1, -78.7, "12 Gates Brewing", "7160000000",
            "14221", "New York", "New York", "80 Earhart Dr",
            "http://example.com", datetime.date(2025, 7, 1)
        )
    ]

    schema = StructType([
        StructField("address_1", StringType(), True),
        StructField("address_2", StringType(), True),
        StructField("address_3", StringType(), True),
        StructField("brewery_type", StringType(), True),
        StructField("city", StringType(), True),
        StructField("country", StringType(), True),
        StructField("id", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("name", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("postal_code", StringType(), True),
        StructField("state", StringType(), True),
        StructField("state_province", StringType(), True),
        StructField("street", StringType(), True),
        StructField("website_url", StringType(), True),
        StructField("extract_date", DateType(), True)
    ])

    df = spark.createDataFrame(data, schema=schema)

    # Should not raise any exception
    validate_schema(df)

# Test: should raise an error if required columns are missing
def test_validate_full_schema_missing_column(spark):
    data = [
        ("brewpub", "United States", "uuid-123")
    ]
    columns = ["brewery_type", "country", "id"]  # Missing many required fields

    df = spark.createDataFrame(data, columns)

    with pytest.raises(ValueError) as excinfo:
        validate_schema(df)

    assert "Missing columns" in str(excinfo.value)

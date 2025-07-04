# 🍺 Brewery Data Pipeline - Full Documentation

[English (EN-US) 🇺🇸](#english-en-us-) | [Português (PT-BR) 🇧🇷](#português-pt-br-)

---

## <a name="english-en-us-"></a>English (EN-US) 🇺🇸

### Table of Contents

- [Project Overview](#1-project-overview)
- [Data Lake Architecture: Medallion Layers](#2-data-lake-architecture-medallion-layers)
- [Project Structure](#3-project-structure)
- [Getting Started: Local Setup Guide](#4-getting-started-local-setup-guide)
  - [Prerequisites](#prerequisites)
  - [Python Environment Setup](#python-environment-setup)
  - [Java Installation](#java-installation)
  - [Apache Spark Installation](#apache-spark-installation)
  - [Apache Airflow Installation & Configuration](#apache-airflow-installation--configuration)
  - [Airflow Connections Setup](#airflow-connections-setup)
  - [Running the Pipeline](#running-the-pipeline)
- [Scripts Deep Dive: Understanding the Flow](#5-scripts-deep-dive-understanding-the-flow)
  - [`dags/brewery_dag.py`](#dagsbrewery_dagpy)
  - [`plugins/operators/brewery_operator.py`](#pluginsoperatorsbrewery_operatorpy)
  - [`hook/brewery_hook.py`](#hookbrewery_hookpy)
  - [`scripts/spark/api_extraction.py`](#scriptssparkapi_extractionpy)
  - [`scripts/spark/transformation.py`](#scriptssparktransformationpy)
  - [`scripts/spark/aggregation.py`](#scriptssparkaggregationpy)
- [Testing Your Pipeline with Pytest](#6-testing-your-pipeline-with-pytest)
  - [How to Run Tests](#how-to-run-tests)
  - [`scripts/tests/test_transformation_schema.py`](#scriptsteststest_transformation_schemapy)
  - [`scripts/tests/test_aggregation_schema.py`](#scriptsteststest_aggregation_schemapy)
- [Design Choices & Best Practices](#7-design-choices--best-practices)
  - [Data Ingestion & Partitioning](#data-ingestion--partitioning-)
  - [Testing & Validation](#testing--validation-)
  - [Architecture & Error Handling](#architecture--error-handling-)
  - [Version Control & Documentation](#version-control--documentation-)
- [Future Enhancements](#8-future-enhancements)
- [Contact](#9-contact)

### 1. Project Overview

This project implements a robust and scalable data pipeline designed to extract, transform, and persist brewery data from the Open Brewery DB API. The solution leverages Apache Airflow for orchestration and Apache Spark (PySpark) for distributed data processing, adhering strictly to the Medallion Architecture for data lake management.

The primary objective of this project is to showcase practical skills in:

- **API Consumption:** Efficiently fetching data from external web services, including pagination.
- **Data Transformation:** Processing raw data into structured, curated, and aggregated formats using PySpark.
- **Data Lake Management:** Implementing a multi-layered data lake for data quality, governance, and optimized querying.
- **Workflow Orchestration:** Building scheduled, fault-tolerant data pipelines with Apache Airflow, including retries and error handling.
- **Code Quality & Best Practices:** Applying principles of modularity, testability (Pytest), version control (Git), and comprehensive documentation.

### 2. Data Lake Architecture: Medallion Layers

The data lake in this project is structured following the Medallion Architecture, a widely adopted design pattern that organizes data into progressively refined layers. This approach enhances data governance, improves data quality, and provides a clear, traceable path for data transformation from raw sources to analytical insights.

#### Bronze Layer (Raw Data) 🥉
- **Purpose:** This is the landing zone for raw, immutable data directly ingested from the source API. Its primary goal is to preserve the original state of the data, acting as a historical archive. No transformations or data quality checks are performed at this stage, beyond ensuring successful ingestion.
- **Format:** JSON (native API format).
- **Partitioning:** Data is partitioned by `extract_date` (e.g., `extract_date=YYYY-MM-DD`). This allows for efficient incremental loads and easy querying of specific historical data snapshots. The `extract_date` reflects the actual date of the data extraction task execution.
- **Process:** The `BreweryOperator` extracts data from the Open Brewery DB API and lands it directly into this layer.

#### Silver Layer (Curated Data) 🥈
- **Purpose:** This layer contains cleaned, structured, and validated data. Data from the Bronze layer undergoes initial transformations to improve its quality, consistency, and usability. It's optimized for downstream consumption and serves as a reliable source for analytical processes.
- **Format:** Parquet (columnar storage) for optimized read performance, compression, and schema evolution.
- **Partitioning:** Data is partitioned by `process_date` (e.g., `process_date=YYYY-MM-DD`), which corresponds to the Airflow DAG's execution date. This facilitates efficient querying, incremental updates, and data versioning based on processing cycles.
- **Transformations:** Basic transformations include schema validation, data type conversions, and adding processing metadata (like the `extract_date` column, derived from the `process_date` argument).
- **Process:** The `transformation.py` script reads raw JSON data from the Bronze layer, performs these transformations, and writes the curated data to this layer.

#### Gold Layer (Aggregated/Analytical Data) 🥇
- **Purpose:** This is the final layer, housing highly aggregated and refined data, specifically designed for business intelligence (BI), reporting, and advanced analytical applications. Data here is optimized for specific use cases and business questions.
- **Format:** Parquet (columnar storage).
- **Partitioning:** Data is also partitioned by `process_date` to align with reporting cycles and enable efficient querying of aggregated views over time.
- **Transformations:** Complex aggregations and business logic are applied to data from the Silver layer. In this project, it includes an aggregated view of the quantity of breweries per type and location, ensuring only the latest available data is used for aggregation.
- **Process:** The `aggregation.py` script reads curated data from the Silver layer, performs the aggregations, and writes the results to this layer.

### 3. Project Structure

The project adheres to a modular and organized file structure for clarity, maintainability, and adherence to common data engineering practices.

```
Apache Airflow/  # This is your project root and Git repository root
├── .git/                      # Git version control metadata (hidden)
├── .gitignore                 # Specifies intentionally untracked files to ignore
├── .pytest_cache/             # Pytest cache directory (ignored by Git)
├── airflow_pipeline/          # Airflow Home directory (created by 'airflow standalone')
│   ├── dags/                  # Symlink to ../dags (or actual DAG files)
│   │   └── brewery_dag.py     # Airflow DAG definition
│   ├── logs/                  # Airflow logs (ignored by Git)
│   ├── plugins/               # Symlink to ../plugins (or actual plugin files)
│   │   ├── hook/
│   │   │   └── brewery_hook.py # Custom Airflow Hook for API interaction
│   │   └── operators/
│   │       └── brewery_operator.py # Custom Airflow Operator for API extraction
│   ├── airflow.cfg            # Airflow configuration file
│   ├── airflow.db             # Airflow SQLite metadata database (ignored by Git)
│   ├── standalone_admin_password.txt # Airflow admin password (ignored by Git)
│   └── webserver_config.py    # Airflow Webserver configuration (ignored by Git if local)
├── data/                      # Data Lake storage (ignored by Git)
│   ├── Bronze/                # Raw data layer
│   │   └── brewery_data/
│   │       └── extract_date=YYYY-MM-DD/ # Partitioned data
│   │           └── brewerydata_YYYYMMDD.json
│   ├── Silver/                # Curated data layer
│   │   └── brewery_data/
│   │       └── brewery_data_main/
│   │           └── process_date=YYYY-MM-DD/ # Partitioned data
│   │               └── *.parquet
│   └── Gold/                  # Aggregated/Analytical data layer
│       └── brewery_data/
│           └── agg_loc_type/
│               └── process_date=YYYY-MM-DD/ # Partitioned data
│                   └── *.parquet
├── spark-3.1.3-bin-hadoop3.2/ # Apache Spark installation (ignored by Git)
│   └── bin/
│   └── ...
├── src/                       # Source code for scripts and notebooks
│   ├── notebooks/
│   │   └── nb_explorer.ipynb
│   └── scripts/
│       ├── spark/
│       │   ├── aggregation.py     # PySpark script for Gold layer aggregation
│       │   ├── transformation.py  # PySpark script for Silver layer transformation
│       │   └── api_extraction.py  # Standalone API extraction utility
│       └── tests/                 # Unit/Integration tests for Spark scripts
│           ├── test_aggregation_schema.py
│           └── test_transformation_schema.py
│           └── test.py
├── venv/                      # Python Virtual Environment (ignored by Git)
├── requirements.txt           # Python dependencies for Airflow core and providers
├── scripts/requirements_spark.txt # Python dependencies for Spark scripts
├── README.md                  # Project documentation (this file)
└── index.html                 # Interactive documentation (for GitHub Pages)
```

### 4. Getting Started: Local Setup Guide

Follow these comprehensive instructions to set up and run the Brewery Data Pipeline on your local Linux environment.

#### Prerequisites

- **Linux Operating System 🐧:** The commands provided are tailored for Debian-based distributions (e.g., Ubuntu).
- **Visual Studio Code (VS Code):** Or any preferred Integrated Development Environment (IDE) for code editing.
- **Git:** For version control and cloning the repository.
  ```bash
  sudo apt update
  sudo apt install git
  ```

#### Python Environment Setup

It's highly recommended to use a Python virtual environment to manage project-specific dependencies.

1.  **Install Python 3.9 and `venv` module:**
    ```bash
    sudo apt update
    sudo apt install python3.9 python3.9-venv
    ```
2.  **Navigate to your project root:**
    ```bash
    cd ~/Desktop/Apache\ Airflow/ # Adjust path if different
    ```
3.  **Create a Python virtual environment:**
    ```bash
    python3.9 -m venv venv
    ```
4.  **Activate the virtual environment:**
    ```bash
    source venv/bin/activate
    ```
    *(Your terminal prompt should change to include `(venv)`)*

5.  **Install Python dependencies:**
    Your `requirements.txt` should contain:
    ```
    # requirements.txt
    # Core Airflow and Providers
    apache-airflow[postgres,celery,redis]==2.3.2
    apache-airflow-providers-apache-spark==4.0.0
    apache-airflow-providers-http==2.1.2
    # Testing framework
    pytest==8.4.1
    ```
    Install them using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

#### Java Installation

Apache Spark requires a Java Development Kit (JDK) to run.

1.  **Check your Java version:**
    ```bash
    java -version
    ```
2.  **Install JDK 11 (recommended):**
    ```bash
    sudo apt update
    sudo apt install openjdk-11-jdk
    ```

#### Apache Spark Installation

1.  **Download Spark 3.1.3:**
    ```bash
    wget https://archive.apache.org/dist/spark/spark-3.1.3/spark-3.1.3-bin-hadoop3.2.tgz
    ```
2.  **Extract the archive:**
    ```bash
    tar -xvzf spark-3.1.3-bin-hadoop3.2.tgz
    ```
3.  **Create `scripts/requirements_spark.txt`:**
    Your PySpark scripts need `pyspark`. Create this file inside `scripts/`:
    ```
    # scripts/requirements_spark.txt
    pyspark==3.1.3
    ```

#### Apache Airflow Installation & Configuration

1.  **Define Airflow and Python versions:**
    ```bash
    export AIRFLOW_VERSION=2.3.2
    export PYTHON_VERSION=3.9
    export CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
    ```
2.  **Set Airflow and Spark Home directories:**
    Add these to your `~/.bashrc` or `~/.profile` for persistence.
    ```bash
    export AIRFLOW_HOME=$(pwd)/airflow_pipeline
    export SPARK_HOME=$(pwd)/spark-3.1.3-bin-hadoop3.2/
    ```
    *Don't forget to run `source ~/.bashrc` or open a new terminal.*

3.  **Initialize Airflow Database and create an admin user:**
    ```bash
    cd $AIRFLOW_HOME
    airflow db migrate
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com \
        --password admin
    ```
    **Note:** Change the password for production environments!

4.  **(Optional) Configure Webserver for Public Access:**
    For local development, you can disable the login screen. Edit `airflow_pipeline/webserver_config.py` and add:
    ```python
    AUTH_ROLE_PUBLIC = 'Admin'
    ```
    **Warning:** Do not use this in production.

#### Airflow Connections Setup

In the Airflow UI (`http://localhost:8080`), go to **Admin > Connections**.

1.  **`brewery_default` Connection (for API):**
    - **Connection ID:** `brewery_default`
    - **Connection Type:** `HTTP`
    - **Host:** `https://api.openbrewerydb.org`

2.  **`spark_default` Connection (for Spark Submit):**
    - **Connection ID:** `spark_default`
    - **Connection Type:** `Spark`
    - **Host:** `local`
    - **Extra (JSON):** (Use the **absolute path** to your Spark installation)
      ```json
      {
        "spark_home": "/home/enduser/Desktop/Apache Airflow/spark-3.1.3-bin-hadoop3.2"
      }
      ```

#### Running the Pipeline

1.  **Start Airflow in standalone mode:**
    ```bash
    cd $AIRFLOW_HOME
    airflow standalone
    ```
2.  **Access the Airflow UI:**
    Open your browser and navigate to `http://localhost:8080`.

3.  **Activate and Trigger the DAG:**
    - In the UI, find `BreweryDAG` and toggle the switch to enable it.
    - Click the "Play" button to trigger a manual run.

### 5. Scripts Deep Dive: Understanding the Flow

#### `dags/brewery_dag.py`
This is the main Airflow DAG definition file, orchestrating the entire pipeline.

- **Purpose:** Defines the `BreweryDAG` workflow, tasks, dependencies, and schedule.
- **Key Components:**
    - `default_args`: Configures common parameters like `retries` (2) and `retry_delay` (1 minute) for resilience.
    - `DAG object`: Defines the DAG's ID, `start_date`, and `schedule_interval` (`@daily`).
    - `brewery_operator` (Bronze): Uses the custom `BreweryOperator` to extract raw data into a dynamically partitioned path `extract_date={{ ds_nodash }}`.
    - `brewery_transform` (Silver): A `SparkSubmitOperator` that runs `transformation.py`, passing the source, destination, and `process_date` (`{{ ds }}`).
    - `brewery_aggregate` (Gold): A `SparkSubmitOperator` that runs `aggregation.py`.
    - **Dependencies:** `brewery_operator >> brewery_transform >> brewery_aggregate` ensures sequential execution.

#### `plugins/operators/brewery_operator.py`
A custom Airflow Operator to extract data from the API.

- **Purpose:** Orchestrates the API extraction process within an Airflow task.
- **Key Components:**
    - `template_fields`: Makes `file_path` a templated field, allowing dynamic paths.
    - `create_parent_folder()`: Ensures the target directory exists before writing.
    - `execute()`: The main method that calls `BreweryHook().run()` to fetch data and then writes it to the specified file path in the Bronze layer.

#### `hook/brewery_hook.py`
A custom Airflow Hook to handle low-level communication with the API.

- **Purpose:** Manages HTTP requests, URL construction, and pagination logic.
- **Key Components:**
    - `BreweryHook(HttpHook)`: Inherits from the base `HttpHook`.
    - `connect_to_endpoint()`: Sends the GET request.
    - `paginate()`: Implements the core pagination logic, fetching metadata to calculate the total number of pages and iterating through them with a `time.sleep(0.5)` to respect API rate limits.
    - `run()`: The entry point that orchestrates the pagination.

#### `scripts/spark/api_extraction.py`
A simple, standalone Python script for quick local testing of API connectivity. It is **not** part of the orchestrated pipeline.

#### `scripts/spark/transformation.py`
This PySpark script transforms raw Bronze data into curated Silver data.

- **Purpose:** Cleans, structures, and enriches raw data.
- **Key Components:**
    - `validate_schema(df)`: Ensures all expected columns are present in the input DataFrame, raising a `ValueError` if not.
    - `brewery_transformation()`: The main logic that reads raw JSON, adds an `extract_date` column (using the `process_date` from Airflow), and writes the result as a Parquet file to the Silver layer.

#### `scripts/spark/aggregation.py`
This PySpark script aggregates curated Silver data to create analytical views in the Gold layer.

- **Purpose:** Generates business-ready insights.
- **Key Components:**
    - `validate_aggregation_schema(df)`: Validates the input schema for columns required for aggregation.
    - `filter_by_latest_extract_date()`: A crucial function that reads all `process_date` partitions in the Silver layer, identifies the latest one, and filters the DataFrame to use only the most recent data snapshot for aggregation.
    - `get_aggregate()`: Performs the core aggregation, grouping by `brewery_type` and `country` and counting the results.
    - `aggregated_layer()`: The main logic that orchestrates reading, filtering, aggregating, and writing the final data to the Gold layer.

### 6. Testing Your Pipeline with Pytest

The project includes unit tests to ensure the integrity of the data transformation and aggregation logic.

#### How to Run Tests

1.  **Activate your virtual environment:**
    ```bash
    cd ~/Desktop/Apache\ Airflow/ # Project root
    source venv/bin/activate
    ```
2.  **Navigate to the tests directory:**
    ```bash
    cd src/scripts/tests/
    ```
3.  **Run Pytest:**
    ```bash
    pytest
    ```

#### `scripts/tests/test_transformation_schema.py`
- **Purpose:** Validates the schema of the input DataFrame for the `transformation.py` script.
- **Key Features:**
    - Uses a `pytest.fixture(scope="session")` to create a shared `SparkSession`.
    - `test_validate_full_schema_success`: Tests a valid schema, expecting no error.
    - `test_validate_full_schema_missing_column`: Tests an invalid schema, expecting a `ValueError`.

#### `scripts/tests/test_aggregation_schema.py`
- **Purpose:** Validates the schema of the input DataFrame for the `aggregation.py` script.
- **Key Features:**
    - Shares the `SparkSession` fixture.
    - `test_validate_schema_success`: Tests successful validation with all required columns.
    - `test_validate_schema_missing_column`: Tests the failure case when a required column is missing, asserting that a `ValueError` is raised.

### 7. Design Choices & Best Practices

#### Data Ingestion & Partitioning 📊
- **API Pagination:** The `BreweryHook` implements pagination to ensure complete data extraction, using `time.sleep` to respect API rate limits.
- **Date Partitioning:** Using `extract_date` (Bronze) and `process_date` (Silver/Gold) is crucial for performance, scalability, and data management.

#### Testing & Validation ✅
- **Automated Tests:** Unit tests with Pytest for schema validation ensure code quality and data integrity.
- **Runtime Schema Validation:** Functions like `validate_schema` prevent runtime errors by ensuring DataFrames have the expected structure before processing.

#### Architecture & Error Handling 🛠️
- **Medallion Architecture:** The three-layer structure promotes data quality, reusability, and easier troubleshooting.
- **Robust Error Handling:** The Airflow DAG is configured with `retries`. The hooks and Spark scripts use `try-except` blocks for controlled error handling.

#### Version Control & Documentation 📚
- **Git Best Practices:** The project is versioned with Git, and a `.gitignore` file keeps the repository clean.
- **Comprehensive Documentation:** This `README.md` provides clear instructions for setup, execution, and design insights.

### 8. Future Enhancements

- **Dockerization:** Containerize the Spark and Airflow environments for better portability and consistency.
- **Monitoring & Alerting:** Implement dedicated monitoring for data quality, pipeline failures, and performance with alerts (e.g., Slack).
- **Data Catalog:** Integrate a data catalog (e.g., Apache Atlas, Amundsen) for discovery, lineage, and governance.
- **CI/CD Integration:** Automate testing and deployment with a CI/CD pipeline.
- **Cloud Deployment:** Explore deploying on cloud platforms like AWS (EMR, Glue), GCP (Dataproc, Dataflow), or Azure (Databricks).

### 9. Contact

For any questions or further discussions, please feel free to reach out.

---

## <a name="português-pt-br-"></a>Português (PT-BR) 🇧🇷

### Sumário

- [Visão Geral do Projeto](#1-visão-geral-do-projeto)
- [Arquitetura do Data Lake: Camadas Medallion](#2-arquitetura-do-data-lake-camadas-medallion)
- [Estrutura do Projeto](#3-estrutura-do-projeto-1)
- [Primeiros Passos: Guia de Instalação Local](#4-primeiros-passos-guia-de-instalação-local)
  - [Pré-requisitos](#pré-requisitos)
  - [Configuração do Ambiente Python](#configuração-do-ambiente-python)
  - [Instalação do Java](#instalação-do-java)
  - [Instalação do Apache Spark](#instalação-do-apache-spark)
  - [Instalação e Configuração do Apache Airflow](#instalação-e-configuração-do-apache-airflow)
  - [Configuração das Conexões do Airflow](#configuração-das-conexões-do-airflow)
  - [Executando o Pipeline](#executando-o-pipeline)
- [Scripts em Detalhe: Entendendo o Fluxo](#5-scripts-em-detalhe-entendendo-o-fluxo)
  - [`dags/brewery_dag.py`](#dagsbrewery_dagpy-1)
  - [`plugins/operators/brewery_operator.py`](#pluginsoperatorsbrewery_operatorpy-1)
  - [`hook/brewery_hook.py`](#hookbrewery_hookpy-1)
  - [`scripts/spark/api_extraction.py`](#scriptsspsparkapi_extractionpy)
  - [`scripts/spark/transformation.py`](#scriptsspsparktransformationpy)
  - [`scripts/spark/aggregation.py`](#scriptsspsparkaggregationpy)
- [Testando Seu Pipeline com Pytest](#6-testando-seu-pipeline-com-pytest)
  - [Como Executar os Testes](#como-executar-os-testes)
  - [`scripts/tests/test_transformation_schema.py`](#scriptsteststest_transformation_schemapy-1)
  - [`scripts/tests/test_aggregation_schema.py`](#scriptsteststest_aggregation_schemapy-1)
- [Escolhas de Design e Boas Práticas](#7-escolhas-de-design-e-boas-práticas)
  - [Ingestão e Particionamento de Dados](#ingestão-e-particionamento-de-dados-)
  - [Testes e Validação](#testes-e-validação-)
  - [Arquitetura e Tratamento de Erros](#arquitetura-e-tratamento-de-erros-)
  - [Controle de Versão e Documentação](#controle-de-versão-e-documentação-)
- [Melhorias Futuras](#8-melhorias-futuras)
- [Contato](#9-contato-1)

### 1. Visão Geral do Projeto

Este projeto implementa um pipeline de dados robusto e escalável, projetado para extrair, transformar e persistir dados de cervejarias da API Open Brewery DB. A solução utiliza Apache Airflow para orquestração e Apache Spark (PySpark) para processamento distribuído de dados, aderindo estritamente à Arquitetura Medallion para gerenciamento de data lake.

O objetivo principal deste projeto é demonstrar habilidades práticas em:

- **Consumo de API:** Buscar dados de forma eficiente de serviços web externos, incluindo paginação.
- **Transformação de Dados:** Processar dados brutos em formatos estruturados, curados e agregados usando PySpark.
- **Gerenciamento de Data Lake:** Implementar um data lake multi-camadas para qualidade de dados, governança e consultas otimizadas.
- **Orquestração de Workflow:** Construir pipelines de dados agendados e tolerantes a falhas com Apache Airflow, incluindo retentativas e tratamento de erros.
- **Qualidade de Código e Boas Práticas:** Aplicar princípios de modularidade, testabilidade (Pytest), controle de versão (Git) e documentação abrangente.

### 2. Arquitetura do Data Lake: Camadas Medallion

O data lake neste projeto é estruturado seguindo a Arquitetura Medallion, um padrão de design amplamente adotado que organiza os dados em camadas progressivamente refinadas.

#### Camada Bronze (Dados Brutos) 🥉
- **Propósito:** Esta é a zona de aterrissagem para dados brutos e imutáveis diretamente ingeridos da API. Seu objetivo principal é preservar o estado original dos dados como um arquivo histórico.
- **Formato:** JSON (formato nativo da API).
- **Particionamento:** Os dados são particionados por `extract_date` (ex: `extract_date=AAAA-MM-DD`), refletindo a data de execução da tarefa.
- **Processo:** O `BreweryOperator` extrai dados da API e os deposita diretamente nesta camada.

#### Camada Silver (Dados Curados) 🥈
- **Propósito:** Esta camada contém dados limpos, estruturados e validados, otimizados para consumo downstream e processos analíticos.
- **Formato:** Parquet (armazenamento colunar) para desempenho e compressão otimizados.
- **Particionamento:** Os dados são particionados por `process_date` (ex: `process_date=AAAA-MM-DD`), correspondendo à data de execução do DAG do Airflow.
- **Transformações:** Incluem validação de esquema, conversões de tipo de dados e adição de metadados de processamento.
- **Processo:** O script `transformation.py` lê dados da camada Bronze, aplica transformações e grava os dados curados nesta camada.

#### Camada Gold (Dados Agregados/Analíticos) 🥇
- **Propósito:** Esta é a camada final, com dados altamente agregados e refinados, projetados para BI, relatórios e aplicações analíticas.
- **Formato:** Parquet.
- **Particionamento:** Também particionados por `process_date` para alinhar com os ciclos de relatórios.
- **Transformações:** Agregações complexas, como a quantidade de cervejarias por tipo e localização, usando apenas os dados mais recentes disponíveis.
- **Processo:** O script `aggregation.py` lê dados da camada Silver, executa as agregações e grava os resultados nesta camada.

### 3. Estrutura do Projeto

O projeto adere a uma estrutura de arquivos modular e organizada para clareza e manutenibilidade.

```
Apache Airflow/  # Raiz do projeto e repositório Git
├── .git/
├── .gitignore
├── airflow_pipeline/          # Diretório Home do Airflow
│   ├── dags/
│   │   └── brewery_dag.py     # Definição do DAG
│   ├── plugins/
│   │   ├── hook/
│   │   │   └── brewery_hook.py # Hook customizado
│   │   └── operators/
│   │       └── brewery_operator.py # Operador customizado
│   ├── airflow.cfg
│   └── ...
├── data/                      # Armazenamento do Data Lake (ignorado)
│   ├── Bronze/
│   ├── Silver/
│   └── Gold/
├── src/                       # Código-fonte
│   └── scripts/
│       ├── spark/
│       │   ├── aggregation.py
│       │   └── transformation.py
│       └── tests/
│           ├── test_aggregation_schema.py
│           └── test_transformation_schema.py
├── venv/                      # Ambiente Virtual (ignorado)
├── requirements.txt
└── README.md
```

### 4. Primeiros Passos: Guia de Instalação Local

Siga estas instruções para configurar e executar o pipeline em seu ambiente Linux local.

#### Pré-requisitos
- **Sistema Operacional Linux 🐧:** Comandos adaptados para distribuições baseadas em Debian (ex: Ubuntu).
- **VS Code:** Ou outra IDE de sua preferência.
- **Git:**
  ```bash
  sudo apt update
  sudo apt install git
  ```

#### Configuração do Ambiente Python
É altamente recomendável usar um ambiente virtual.

1.  **Instale Python 3.9 e `venv`:**
    ```bash
    sudo apt update
    sudo apt install python3.9 python3.9-venv
    ```
2.  **Navegue até a raiz do projeto:**
    ```bash
    cd /caminho/para/seu/projeto/
    ```
3.  **Crie e ative o ambiente virtual:**
    ```bash
    python3.9 -m venv venv
    source venv/bin/activate
    ```
4.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

#### Instalação do Java
O Spark requer um JDK.

```bash
sudo apt update
sudo apt install openjdk-11-jdk
```

#### Instalação do Apache Spark

1.  **Baixe e extraia o Spark 3.1.3:**
    ```bash
    wget https://archive.apache.org/dist/spark/spark-3.1.3/spark-3.1.3-bin-hadoop3.2.tgz
    tar -xvzf spark-3.1.3-bin-hadoop3.2.tgz
    ```

#### Instalação e Configuração do Apache Airflow

1.  **Defina variáveis de ambiente:**
    Adicione ao seu `~/.bashrc` ou `~/.profile`:
    ```bash
    export AIRFLOW_HOME=$(pwd)/airflow_pipeline
    export SPARK_HOME=$(pwd)/spark-3.1.3-bin-hadoop3.2/
    ```
    *Execute `source ~/.bashrc` ou abra um novo terminal.*

2.  **Inicialize o Airflow e crie um usuário:**
    ```bash
    airflow db migrate
    airflow users create \
        --username admin --password admin \
        --firstname Admin --lastname User \
        --role Admin --email admin@example.com
    ```
    **Aviso:** Use uma senha forte em produção.

#### Configuração das Conexões do Airflow

Na UI do Airflow (`http://localhost:8080`), vá em **Admin > Connections**.

1.  **Conexão `brewery_default` (API):**
    - **ID:** `brewery_default`
    - **Tipo:** `HTTP`
    - **Host:** `https://api.openbrewerydb.org`

2.  **Conexão `spark_default` (Spark):**
    - **ID:** `spark_default`
    - **Tipo:** `Spark`
    - **Host:** `local`
    - **Extra (JSON):** (Use o **caminho absoluto** para sua instalação do Spark)
      ```json
      {
        "spark_home": "/home/usuario/caminho/para/Apache Airflow/spark-3.1.3-bin-hadoop3.2"
      }
      ```

#### Executando o Pipeline

1.  **Inicie o Airflow:**
    ```bash
    airflow standalone
    ```
2.  **Acesse a UI:** `http://localhost:8080`.
3.  **Ative e acione o DAG `BreweryDAG`**.

### 5. Scripts em Detalhe: Entendendo o Fluxo

#### `dags/brewery_dag.py`
Orquestra todo o pipeline, definindo tarefas, dependências e agendamento (`@daily`). Define o fluxo sequencial: `Bronze >> Silver >> Gold`.

#### `plugins/operators/brewery_operator.py`
Operador customizado que extrai dados da API e os salva na camada Bronze.

#### `hook/brewery_hook.py`
Hook customizado que lida com a comunicação com a API, incluindo a lógica de paginação para buscar todos os registros.

#### `scripts/spark/transformation.py`
Script PySpark que transforma dados brutos (Bronze) em dados curados (Silver), adicionando metadados e validando o esquema.

#### `scripts/spark/aggregation.py`
Script PySpark que agrega os dados curados (Silver) para gerar insights analíticos na camada Gold. Garante que apenas os dados do snapshot mais recente sejam usados na agregação.

### 6. Testando Seu Pipeline com Pytest

O projeto inclui testes unitários para garantir a integridade da lógica de transformação e agregação.

#### Como Executar os Testes

1.  Ative seu ambiente virtual.
2.  Navegue até o diretório `src/scripts/tests/`.
3.  Execute o Pytest:
    ```bash
    pytest
    ```

#### `scripts/tests/test_transformation_schema.py`
Valida se o DataFrame de entrada para a transformação contém todas as colunas esperadas da API.

#### `scripts/tests/test_aggregation_schema.py`
Valida se o DataFrame de entrada para a agregação contém as colunas necessárias (`brewery_type`, `country`, `process_date`).

### 7. Escolhas de Design e Boas Práticas

#### Ingestão e Particionamento de Dados 📊
- **API Paginada:** O `BreweryHook` garante a extração completa dos dados.
- **Particionamento por Data:** O uso de `extract_date` e `process_date` é fundamental para desempenho, escalabilidade e gerenciamento dos dados.

#### Testes e Validação ✅
- **Testes Automatizados:** Testes unitários com Pytest demonstram um compromisso com a qualidade e integridade dos dados.
- **Validação de Schema em Tempo de Execução:** Funções de validação nos scripts Spark previnem erros de processamento.

#### Arquitetura e Tratamento de Erros 🛠️
- **Arquitetura Medallion:** A estrutura de três camadas promove qualidade, reusabilidade e facilidade de depuração.
- **Tratamento Robusto de Erros:** O DAG do Airflow está configurado com retentativas, e os scripts usam blocos `try-except` para lidar com falhas de forma controlada.

#### Controle de Versão e Documentação 📚
- **Boas Práticas de Git:** O projeto é versionado, e o `.gitignore` mantém o repositório limpo.
- **Documentação Abrangente:** Este `README.md` fornece instruções claras para setup, execução e insights de design.

### 8. Melhorias Futuras

- **Dockerização:** Containerizar os ambientes para melhorar a portabilidade.
- **Monitoramento e Alerta:** Implementar monitoramento de qualidade de dados e alertas proativos.
- **Catálogo de Dados:** Integrar com soluções como Apache Atlas para governança e descoberta de dados.
- **Integração CI/CD:** Automatizar testes e implantação.
- **Serviços em Nuvem:** Explorar a implantação em plataformas como AWS, GCP ou Azure.

### 9. Contato

Para quaisquer dúvidas ou discussões adicionais, sinta-se à vontade para entrar em contato.

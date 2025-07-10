import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import pyodbc

# Load environment variables from .env file
load_dotenv()

# Get database credentials from the environment
directory = os.getenv('CSV_DIRECTORY')
server = os.getenv('DB_SERVER')
database = os.getenv('DB_DATABASE')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')

# Connection string for pyodbc
pyodbc_connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"UID={username};"
    f"PWD={password};"
)

# Function to ensure the database exists using pyodbc
def ensure_database_exists(db_name):
    try:
        # Connect to the SQL Server master database
        with pyodbc.connect(pyodbc_connection_string, autocommit=True) as conn:
            cursor = conn.cursor()
            # Check if the database exists
            cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = ?", db_name)
            result = cursor.fetchone()
            if result is None:
                print(f"Database '{db_name}' does not exist. Creating...")
                # Create the database
                cursor.execute(f"CREATE DATABASE {db_name}")
                print(f"Database '{db_name}' created successfully.")
            else:
                print(f"Database '{db_name}' already exists.")
    except Exception as e:
        print(f"Error checking/creating database: {e}")

# Ensure the financial_data database exists
ensure_database_exists(database)

# Create the connection URL for SQLAlchemy
connection_url = URL.create(
    "mssql+pyodbc",
    username=username,
    password=password,
    host=server,
    database=database,
    query={"driver": "ODBC Driver 17 for SQL Server"},
)

# Engine for the target database
engine = create_engine(connection_url)

# Function to process and insert data from CSV files
def process_csv(filepath):
    # Read the data
    data = pd.read_csv(filepath, sep=';')
    
    # Adjust numerical columns (replace commas with dots and convert to float)
    numeric_columns = ["Open", "High", "Low", "Close", "YTD Gains"]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = data[column].str.replace(',', '.').astype(float)
    
    # Get table name from file name
    table_name = os.path.splitext(os.path.basename(filepath))[0]
    
    # Insert data into the database
    data.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Data from file '{filepath}' inserted into table '{table_name}'.")

# Process all CSV files in the directory
def process_all_csv(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            filepath = os.path.join(directory, filename)
            try:
                process_csv(filepath)
            except Exception as e:
                print(f"Error processing {filename}: {e}")

# Process CSV files
process_all_csv(directory)

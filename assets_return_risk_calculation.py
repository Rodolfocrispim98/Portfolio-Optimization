import pyodbc
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

# Configurações de conexão ao SQL Server
load_dotenv()

# Obter as credenciais da base de dados
server = os.getenv('DB_SERVER')
database = os.getenv('DB_DATABASE')
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')

# Construir a string de conexão
connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

# Conectar ao SQL Server
try:
    conn = pyodbc.connect(connection_string)
    print("Conexão ao SQL Server estabelecida com sucesso.")
except pyodbc.Error as e:
    print(f"Erro ao conectar ao SQL Server: {e}")
    exit()

# Obter os nomes de todas as tabelas
query_tables = """
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE';
"""
try:
    tables = pd.read_sql(query_tables, conn)['TABLE_NAME'].tolist()
except Exception as e:
    print(f"Erro ao obter os nomes das tabelas: {e}")
    conn.close()
    exit()

# Dicionário para armazenar os retornos diários
returns_dict = {}

# Processar os dados de cada tabela
for table in tables:
    try:
        query = f"SELECT Date, [Close] FROM {table} ORDER BY Date"
        df = pd.read_sql(query, conn)

        # Converter a coluna 'Date' para o formato de data
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)

        # Calcular os retornos diários
        df['Return'] = df['Close'].pct_change()
        returns_dict[table] = df['Return'].dropna()
    except Exception as e:
        print(f"Erro ao processar a tabela {table}: {e}")

# Fechar a conexão
conn.close()

# Criar um DataFrame de retornos
returns_df = pd.DataFrame(returns_dict)

# Calcular os retornos anuais e variâncias
annual_returns = returns_df.mean() * 252  # 252 é o número de dias úteis no ano
annual_variances = returns_df.var() * 252

# Calcular a matriz de covariâncias
cov_matrix = returns_df.cov() * 252

# Exibir os resultados
print("\nRetornos Anuais:")
print(annual_returns)
print("\nRiscos (Variância Anual):")
print(annual_variances)
print("\nMatriz de Covariâncias:")
print(cov_matrix)

# Salvar os resultados em CSV
annual_returns.to_csv("annual_returns.csv")
annual_variances.to_csv("annual_variances.csv")
cov_matrix.to_csv("cov_matrix.csv")

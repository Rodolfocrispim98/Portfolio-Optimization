import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
# .env

# Configurações de conexão ao SQL Server
load_dotenv()

# Obter as credenciais da base de dados
directory= os.getenv('CSV_DIRECTORY')
server = os.getenv('DB_SERVER')
database = os.getenv('DB_DATABASE')
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')

# Construir a string de conexão
connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
try:
    engine = create_engine(connection_string)
    connection = engine.connect()
    print("Conexao bem-sucedida!")
except Exception as e:
    print(f"Erro: {e}")
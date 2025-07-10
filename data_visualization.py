import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

# Configurações de conexão ao SQL Server
load_dotenv()

# Obter as credenciais da base de dados
directory= os.getenv('CSV_DIRECTORY')
server = os.getenv('DB_SERVER')
database = os.getenv('DB_DATABASE')
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')

connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

# Conectar ao SQL Server
try:
    conn = pyodbc.connect(connection_string)
    print("Conexão ao SQL Server estabelecida com sucesso.")
except pyodbc.Error as e:
    print(f"Erro ao conectar ao SQL Server: {e}")
    exit()

# Query para buscar os dados da tabela desejada
query = "SELECT Date, [Close] FROM AAPL ORDER BY Date"

try:
    # Lê os dados do SQL para um DataFrame
    df = pd.read_sql(query, conn)
    print("Dados carregados com sucesso.")
except Exception as e:
    print(f"Erro ao executar a query: {e}")
    conn.close()
    exit()

# Fechar a conexão
conn.close()

# Verificar os primeiros dados
print(df.head())

# Converter a coluna 'DateTime' para formato de data
df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)

# Visualizar os dados com matplotlib
plt.figure(figsize=(10, 6))
plt.plot(df['Date'], df['Close'],'o', label='Preço de Fecho', color='blue')

# Configurações do gráfico
plt.title("Preço de Fecho em Função de Date", fontsize=16)
plt.xlabel("Date", fontsize=12)
plt.ylabel("Preço de Fecho", fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()

# Mostrar o gráfico
plt.show()

import numpy as np
from qiskit import QuantumCircuit, Aer
from qiskit.providers.aer import AerSimulator
from qiskit.algorithms import QAOA
from qiskit.opflow import I, X, Z, StateFn, CircuitStateFn
from qiskit.utils import QuantumInstance
import matplotlib.pyplot as plt
import pyodbc
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


# Exemplo de retorno de ativos
# returns_df = pd.DataFrame({'AAPL': [0.252], 'TSLA': [0.18]})
# Exemplo de cálculo de retornos anuais e matriz de covariância:
annual_returns = returns_df.mean() * 252  # Retornos anuais
cov_matrix = returns_df.cov() * 252  # Matriz de covariância anualizada

# Codificação da função de custo em termos de Hamiltoniano (risco e retorno)
n_assets = len(annual_returns)
cost_operator = 0

# Vamos assumir que a função de custo é uma soma ponderada dos termos de risco e retorno
for i in range(n_assets):
    cost_operator += (annual_returns[i] * X(i))  # Maximizar o retorno (termo linear)
    for j in range(n_assets):
        cost_operator += (cov_matrix.iloc[i, j] * Z(i) @ Z(j))  # Minimizar o risco (termo quadrático)

# Hamiltoniano de mistura
mixer_operator = sum([X(i) for i in range(n_assets)])

# Definindo o QAOA com um número de camadas p = 1
p = 1  # Número de camadas
qaoa = QAOA(cost_operator, mixer_operator, p)

# Definindo o simulador de backend
backend = AerSimulator()  # Alterado para AerSimulator no Qiskit 1.2

# Instanciando o QuantumInstance
quantum_instance = QuantumInstance(backend)

# Executar o QAOA
result = qaoa.compute_minimum_eigenvalue(operator=cost_operator)

# A partir do resultado, obtemos a solução para os pesos
optimal_weights = np.array([result.eigenstate[i] for i in range(n_assets)])

# Exibir os pesos ótimos do portfólio
print("Pesos ótimos do portfólio calculados pelo QAOA:")
print(optimal_weights)

# Agora, vamos calcular o retorno e risco para o portfólio ótimo
optimal_return = np.sum(optimal_weights * annual_returns)
optimal_risk = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))

print("Retorno anual do portfólio ótimo:", optimal_return)
print("Risco (desvio padrão) do portfólio ótimo:", optimal_risk)

# Visualizar os pesos ótimos
plt.bar(range(n_assets), optimal_weights, tick_label=returns_df.columns)
plt.title('Pesos do Portfólio Ótimo usando QAOA')
plt.xlabel('Ações')
plt.ylabel('Pesos')
plt.show()

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
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

# Passo 1: Calcular os retornos anuais e a matriz de covariância
annual_returns = returns_df.mean() * 252  # Retornos anuais
cov_matrix = returns_df.cov() * 252  # Matriz de covariâncias anualizada

# Passo 2: Definir a função objetivo (minimizar o risco, dado o retorno)
def portfolio_variance(weights, cov_matrix):
    return np.dot(weights.T, np.dot(cov_matrix, weights))

# Passo 3: Definir a restrição de que os pesos somam 1
def constraint(weights):
    return np.sum(weights) - 1

# Passo 4: Iniciar a otimização
def optimize_portfolio(cov_matrix, expected_returns):
    n_assets = len(expected_returns)
    
    # Peso inicial (distribuição igual entre as ações)
    initial_weights = np.ones(n_assets) / n_assets
    
    # Definir os limites (os pesos devem estar entre 0 e 1)
    bounds = tuple((0, 1) for asset in range(n_assets))
    
    # Definir as restrições
    constraints = ({'type': 'eq', 'fun': constraint})
    
    # Minimizar a variância
    result = minimize(portfolio_variance, initial_weights, args=(cov_matrix,), method='SLSQP', bounds=bounds, constraints=constraints)
    
    return result.x

# Passo 5: Definir a função para calcular o retorno do portfólio dado os pesos
def portfolio_return(weights, expected_returns):
    return np.sum(weights * expected_returns)

# Passo 6: Calcular os pesos ótimos
optimal_weights = optimize_portfolio(cov_matrix, annual_returns)

# Passo 7: Calcular o retorno e o risco do portfólio ótimo
optimal_return = portfolio_return(optimal_weights, annual_returns)
optimal_risk = np.sqrt(portfolio_variance(optimal_weights, cov_matrix))

print("Pesos ótimos:", optimal_weights)
print("Retorno anual do portfólio ótimo:", optimal_return)
print("Risco (desvio padrão) do portfólio ótimo:", optimal_risk)

# Passo 8: Gerar o gráfico de frentes eficientes

# Vamos gerar múltiplos portfólios aleatórios para mostrar a fronteira eficiente
num_portfolios = 10000
results = np.zeros((3, num_portfolios))

for i in range(num_portfolios):
    # Gerar pesos aleatórios para o portfólio
    weights = np.random.random(len(annual_returns))
    weights /= np.sum(weights)
    
    # Calcular o retorno e o risco do portfólio
    portfolio_ret = portfolio_return(weights, annual_returns)
    portfolio_risk = np.sqrt(portfolio_variance(weights, cov_matrix))
    
    # Guardar os resultados
    results[0, i] = portfolio_ret
    results[1, i] = portfolio_risk
    results[2, i] = portfolio_ret / portfolio_risk  # Sharpe ratio

risk_free_rate = 0.045 #Valor US Treasury bonds a 10Y a 4.5%
sharpe_ratios = (results[0,:] - risk_free_rate) / results[1,:]

# # 2. Encontrar o índice do portfólio ótimo (maior Sharpe Ratio)
optimal_sharpe_idx = np.argmax(sharpe_ratios)
# optimal_sharpe_weights = results[:3, optimal_sharpe_idx]

# # Passo 2: Obter os pesos do portfólio com o melhor Sharpe Ratio
# # O resultado da otimização tem 3 partes: retorno, risco, e Sharpe ratio
# optimal_sharpe_weights = results[:len(annual_returns), optimal_sharpe_idx]  # Usar os pesos corretos

# # Passo 3: Calcular o retorno e o risco do portfólio com o melhor Sharpe Ratio
# optimal_sharpe_return = portfolio_return(optimal_sharpe_weights, annual_returns)
# optimal_sharpe_risk = np.sqrt(portfolio_variance(optimal_sharpe_weights, cov_matrix))

# # Passo 4: Exibir os resultados
# print("Portfólio com o melhor Sharpe Ratio:")
# print(f"Retorno Anual: {optimal_sharpe_return:.4f}")
# print(f"Risco (Desvio Padrão) Anual: {optimal_sharpe_risk:.4f}")
# print(f"Sharpe Ratio: {sharpe_ratios[optimal_sharpe_idx]:.4f}")



# 3. Obter os pesos do portfólio ótimo
# optimal_weights = results[3:, optimal_sharpe_idx]

# 4. Nomes dos ativos (ações)
assets = tables  # Troque com os nomes reais das suas ações



# Plotar a fronteira eficiente
plt.figure(1)
plt.scatter(results[1,:], results[0,:], c=results[2,:], cmap='viridis')
plt.title('Classic Optimization')
plt.xlabel('Risk (Standard Deviation) in %')
plt.ylabel('Annual Return in %')
plt.colorbar(label='Sharpe Ratio')


fig, ax = plt.subplots(figsize=(8, 6))

ax.bar(assets, optimal_weights, color='green')
plt.xticks(rotation=45)
ax.set_title(f'Optimal Portfolio Wheight\'s (Sharpe Ratio: {sharpe_ratios[optimal_sharpe_idx]:.2f})')
ax.set_ylabel('Weights per Stock')

# Exibindo o gráfico
plt.tight_layout()
plt.show()

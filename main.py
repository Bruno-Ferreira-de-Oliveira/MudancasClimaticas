"""Script que analisa dados climáticos do INMET em São Paulo.

Esse módulo gera quatro gráficos que mostram a relação e dados da variação
climática de um ponto específico em São Paulo, fornecido pelo INMET.
"""

import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def carregar_dados(caminho: str):
    """ Lê os CSVs, renomeia, limpa e retorna o df """
    arquivos = sorted(glob.glob(caminho))
    if not arquivos:
        raise FileNotFoundError(f'Nenhum CSV encontrado em "{caminho}". Coloque os arquivos do INMET na pasta csv/')
    lista_tabelas = []
    for arq in arquivos:
        tabela = pd.read_csv(arq, sep=';', decimal=',', skiprows=8, encoding='latin-1')

        for col in tabela.columns:
            nome = col.upper()
            if 'BULBO SECO' in nome:
                tabela = tabela.rename(columns={col: 'Temperatura'})
            elif 'PRECIPITA' in nome:
                tabela = tabela.rename(columns={col: 'Chuva'})
            elif 'UMIDADE RELATIVA DO AR' in nome:
                tabela = tabela.rename(columns={col: 'Umidade'})
            elif 'DATA' in nome:
                tabela = tabela.rename(columns={col: 'Data'})
            elif nome.startswith('HORA'):
                tabela = tabela.rename(columns={col: 'Hora'})

        lista_tabelas.append(tabela)

    df = pd.concat(lista_tabelas, ignore_index=True)

    colunas_uso = ['Temperatura', 'Chuva', 'Umidade']
    for col in colunas_uso:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].replace(-9999, np.nan)

    hora = df['Hora'].str[:2].astype(int)
    df['DataHora'] = pd.to_datetime(df['Data'], format='%Y/%m/%d') + pd.to_timedelta(hora - 3, unit='h')
    df['Data'] = df['DataHora'].dt.normalize()
    df['Ano'] = df['DataHora'].dt.year
    df['Mes'] = df['DataHora'].dt.month

    return df

def grafico_temperatura_2026(df):
    """ Gera e exibe o gráfico de linhas das temperaturas médias diárias em 2026 """
    df_2026 = df[df['Ano'] == 2026]
    media_diaria_2026 = df_2026.groupby('Data')['Temperatura'].mean().reset_index()

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=media_diaria_2026, x='Data', y='Temperatura', color='firebrick')
    plt.title('Evolução da Temperatura Média Diária em 2026 (INMET - SP/Mirante)')
    plt.xlabel('Data')
    plt.ylabel('Temperatura (°C)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def grafico_chuva_mensal(df):
    """ Gera e exibe o gráfico de barras da média de mm
    da chuva total acumulada por mês desde 2020
    """
    chuva_ano_mes = df.groupby(['Ano', 'Mes'])['Chuva'].agg(['sum', 'count']).reset_index()
    chuva_por_hora = chuva_ano_mes.groupby('Mes')['sum'].transform('sum') / chuva_ano_mes.groupby('Mes')['count'].transform('sum')
    horas_no_mes = pd.to_datetime(dict(year=chuva_ano_mes['Ano'], month=chuva_ano_mes['Mes'], day=1)).dt.days_in_month * 24
    chuva_ano_mes['Chuva'] = chuva_ano_mes['sum'] + (horas_no_mes - chuva_ano_mes['count']) * chuva_por_hora
    media_mensal = chuva_ano_mes.groupby('Mes')['Chuva'].mean().reset_index()

    plt.figure(figsize=(9, 5))
    sns.barplot(data=media_mensal, x='Mes', y='Chuva', color='steelblue')
    plt.title('Média de Chuva Acumulada por Mês (INMET - SP/Mirante)')
    plt.xlabel('Mês')
    plt.ylabel('Precipitação Média Mensal (mm)')
    plt.xticks(
        ticks=range(12),
        labels=['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
        )
    plt.tight_layout()
    plt.show()

def grafico_histograma_temperatura(df):
    """ Gera e exibe o histograma com a distribuição das temperaturas """
    plt.figure(figsize=(9, 5))
    sns.histplot(data=df, x='Temperatura', binwidth=2, kde=True, color='coral')
    plt.title('Distribuição de Frequência das Temperaturas (INMET - SP/Mirante)')
    plt.xlabel('Temperatura (°C)')
    plt.ylabel('Quantidade de Registros')
    plt.tight_layout()
    plt.show()

def grafico_dispersao_temp_umidade(df):
    """ Gera e exibe o gráfico de dispersão de temperatura por umidade """
    plt.figure(figsize=(9, 5))
    sns.scatterplot(data=df, x='Temperatura', y='Umidade', alpha=0.1, color='purple', s=15)
    plt.title('Relação entre Temperatura e Umidade do Ar (INMET - SP/Mirante)')
    plt.xlabel('Temperatura (°C)')
    plt.ylabel('Umidade Relativa (%)')
    plt.tight_layout()
    plt.show()

def main():
    """ Função principal do script, utilizada para chamada das outras funções. """
    sns.set_theme(style="whitegrid")
    df = carregar_dados('csv/*.CSV')
    grafico_temperatura_2026(df)
    grafico_chuva_mensal(df)
    grafico_histograma_temperatura(df)
    grafico_dispersao_temp_umidade(df)

if __name__ == "__main__":
    main()

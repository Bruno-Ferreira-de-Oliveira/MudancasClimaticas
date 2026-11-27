"""Gera os dados do site: as mesmas contas do main.py, para cada estado e capital do Brasil."""

import glob
import pandas as pd
import numpy as np

CAMINHO_CSV = 'csv/**/*.[cC][sS][vV]'

ARQUIVO_SITE = 'site/dados.js'

FAIXAS_HISTOGRAMA = np.arange(-10, 45.5, 0.5)

PONTOS_DISPERSAO = 2000

FAIXA_TEMPERATURA = (-10, 45)
FAIXA_UMIDADE = (1, 100)
FAIXA_CHUVA_HORA = (0, 150)

CODIFICACAO_INMET = 'latin-1'

CAPITAIS = {
    'AC': ('A104', 'Rio Branco'),
    'AL': ('A303', 'Maceió'),
    'AP': ('A249', 'Macapá'),
    'AM': ('A101', 'Manaus'),
    'BA': ('A401', 'Salvador'),
    'CE': ('A305', 'Fortaleza'),
    'DF': ('A001', 'Brasília'),
    'ES': ('A612', 'Vitória'),
    'GO': ('A002', 'Goiânia'),
    'MA': ('A203', 'São Luís'),
    'MT': ('A901', 'Cuiabá'),
    'MS': ('A702', 'Campo Grande'),
    'MG': ('A521', 'Belo Horizonte'),
    'PA': ('A201', 'Belém'),
    'PB': ('A320', 'João Pessoa'),
    'PR': ('A807', 'Curitiba'),
    'PE': ('A301', 'Recife'),
    'PI': ('A312', 'Teresina'),
    'RJ': ('A652', 'Rio de Janeiro'),
    'RN': ('A304', 'Natal'),
    'RS': ('A801', 'Porto Alegre'),
    'RO': ('A925', 'Porto Velho'),
    'RR': ('A135', 'Boa Vista'),
    'SC': ('A806', 'Florianópolis'),
    'SP': ('A701', 'São Paulo'),
    'SE': ('A409', 'Aracaju'),
    'TO': ('A009', 'Palmas'),
}

NOMES_ESTADOS = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal',
    'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão',
    'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
    'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco',
    'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima',
    'SC': 'Santa Catarina', 'SP': 'São Paulo', 'SE': 'Sergipe',
    'TO': 'Tocantins',
}

NOMES_MESES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
               'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


def ler_cabecalho(arquivo: str) -> dict:
    """ Lê as 8 primeiras linhas do CSV e devolve a UF, o código e o nome da estação. """
    info = {}
    with open(arquivo, encoding=CODIFICACAO_INMET) as f:
        for _ in range(8):
            linha = f.readline().strip()
            if ':;' in linha:
                chave, valor = linha.split(':;', 1)
                info[chave.strip().upper()] = valor.strip().strip(';')
    return {
        'UF': info.get('UF', '?'),
        'Codigo': info.get('CODIGO (WMO)', '?'),
        'Estacao': info.get('ESTACAO', '?').title(),
    }


def coluna_usada(nome: str) -> bool:
    """ Diz se a coluna é uma das que usamos (data, hora, temperatura, chuva e umidade). """
    nome = nome.upper()
    return (nome == 'DATA' or nome.startswith('HORA') or 'BULBO SECO' in nome
            or 'PRECIPITA' in nome or 'UMIDADE RELATIVA DO AR' in nome)


def resumir_arquivo(arquivo: str) -> dict:
    """ Lê o CSV de uma estação, limpa os dados e devolve os resumos usados nos gráficos. """
    tabela = pd.read_csv(arquivo, sep=';', decimal=',', skiprows=8,
                         encoding=CODIFICACAO_INMET, usecols=coluna_usada)

    for col in tabela.columns:
        nome = col.upper()
        if 'BULBO SECO' in nome:
            tabela = tabela.rename(columns={col: 'Temperatura'})
        elif 'PRECIPITA' in nome:
            tabela = tabela.rename(columns={col: 'Chuva'})
        elif 'UMIDADE RELATIVA DO AR' in nome:
            tabela = tabela.rename(columns={col: 'Umidade'})
        elif nome.startswith('HORA'):
            tabela = tabela.rename(columns={col: 'Hora'})

    for col in ['Temperatura', 'Chuva', 'Umidade']:
        tabela[col] = pd.to_numeric(tabela[col], errors='coerce')
        tabela[col] = tabela[col].replace(-9999, np.nan)

    for col, (minimo, maximo) in [('Temperatura', FAIXA_TEMPERATURA),
                                  ('Umidade', FAIXA_UMIDADE),
                                  ('Chuva', FAIXA_CHUVA_HORA)]:
        tabela[col] = tabela[col].where(tabela[col].between(minimo, maximo))

    hora = tabela['Hora'].astype(str).str[:2].astype(int)
    data_hora = pd.to_datetime(tabela['Data'], format='%Y/%m/%d') + pd.to_timedelta(hora - 3, unit='h')
    tabela['Data'] = data_hora.dt.normalize()
    tabela['Ano'] = data_hora.dt.year
    tabela['Mes'] = data_hora.dt.month

    cabecalho = ler_cabecalho(arquivo)

    diario = tabela.groupby('Data')['Temperatura'].mean().dropna().reset_index()

    mensal = tabela.groupby(['Ano', 'Mes'])['Chuva'].agg(['sum', 'count']).reset_index()

    histograma, _ = np.histogram(tabela['Temperatura'].dropna(), bins=FAIXAS_HISTOGRAMA)

    pontos = tabela[['Temperatura', 'Umidade']].dropna()
    amostra = pontos.sample(n=min(300, len(pontos)), random_state=0)

    for parte in (diario, mensal, amostra):
        parte['UF'] = cabecalho['UF']
        parte['Codigo'] = cabecalho['Codigo']
    return {'cabecalho': cabecalho, 'diario': diario, 'mensal': mensal,
            'histograma': histograma, 'amostra': amostra}


def carregar_dados(caminho: str) -> dict:
    """ Lê todos os CSVs da pasta csv/ e junta os resumos de todas as estações. """
    arquivos = sorted(glob.glob(caminho, recursive=True))
    if not arquivos:
        raise FileNotFoundError(
            f'Nenhum CSV encontrado em "{caminho}". '
            'Extraia os zips do INMET dentro da pasta csv/.'
        )

    diarios, mensais, amostras, estacoes = [], [], [], []
    histogramas = {}
    for i, arq in enumerate(arquivos, start=1):
        r = resumir_arquivo(arq)
        diarios.append(r['diario'])
        mensais.append(r['mensal'])
        amostras.append(r['amostra'])
        estacoes.append(r['cabecalho'])
        codigo = r['cabecalho']['Codigo']
        histogramas[codigo] = histogramas.get(codigo, 0) + r['histograma']
        if i % 250 == 0 or i == len(arquivos):
            print(f'Lidos {i} de {len(arquivos)} arquivos...')

    estacoes = pd.DataFrame(estacoes).drop_duplicates('Codigo', keep='last')
    return {
        'diario': pd.concat(diarios, ignore_index=True),
        'mensal': pd.concat(mensais, ignore_index=True),
        'amostra': pd.concat(amostras, ignore_index=True),
        'histogramas': histogramas,
        'estacoes': estacoes,
    }


def chuva_media_mensal(mensal: pd.DataFrame) -> list:
    """ Calcula a chuva média de cada mês (Jan a Dez), estimando as horas sem dado como no main.py. """
    mensal = mensal.copy()
    soma = mensal.groupby(['Codigo', 'Mes'])[['sum', 'count']].transform('sum')
    chuva_por_hora = soma['sum'] / soma['count'].replace(0, np.nan)
    horas_no_mes = pd.to_datetime(dict(year=mensal['Ano'], month=mensal['Mes'], day=1)).dt.days_in_month * 24
    mensal['Chuva'] = mensal['sum'] + (horas_no_mes - mensal['count']) * chuva_por_hora

    por_ano_mes = mensal.groupby(['Ano', 'Mes'])['Chuva'].mean().reset_index()
    media = por_ano_mes.groupby('Mes')['Chuva'].mean().reindex(range(1, 13))
    return [None if pd.isna(v) else round(float(v), 1) for v in media]


def resumir_grupo(dados: dict, filtro) -> dict:
    """ Prepara os dados dos gráficos de um estado ou de uma capital. """
    diario = filtro(dados['diario'])
    media_dia = diario.groupby('Data')['Temperatura'].mean()
    dias = pd.date_range(media_dia.index.min(), media_dia.index.max(), freq='D')
    media_dia = media_dia.reindex(dias)

    codigos = filtro(dados['estacoes'])['Codigo']
    histograma = sum(dados['histogramas'][c] for c in codigos if c in dados['histogramas'])

    amostra = filtro(dados['amostra'])
    amostra = amostra.sample(n=min(PONTOS_DISPERSAO, len(amostra)), random_state=0)

    return {
        'estacoes': int(len(codigos)),
        'diario': {
            'inicio': dias[0].strftime('%Y-%m-%d'),
            'temperatura': [None if pd.isna(v) else round(float(v), 1) for v in media_dia],
        },
        'chuva_mes': chuva_media_mensal(filtro(dados['mensal'])),
        'histograma': [int(v) for v in histograma],
        'dispersao': {
            'temperatura': amostra['Temperatura'].round(1).tolist(),
            'umidade': amostra['Umidade'].round(0).astype(int).tolist(),
        },
    }


def montar_dados_site(dados: dict) -> dict:
    """ Monta os dados do estado e da capital de cada uma das 27 UFs. """
    ufs = {}
    for uf in sorted(NOMES_ESTADOS):
        codigo, cidade = CAPITAIS[uf]
        estacao = dados['estacoes'][dados['estacoes']['Codigo'] == codigo]
        capital = resumir_grupo(dados, lambda d: d[d['Codigo'] == codigo])
        capital.update({'cidade': cidade, 'codigo': codigo,
                        'estacao': estacao['Estacao'].iloc[0]})
        ufs[uf] = {
            'nome': NOMES_ESTADOS[uf],
            'estado': resumir_grupo(dados, lambda d: d[d['UF'] == uf]),
            'capital': capital,
        }
    return {
        'total_estacoes': int(len(dados['estacoes'])),
        'faixas_histograma': [float(v) for v in FAIXAS_HISTOGRAMA],
        'ufs': ufs,
    }


def salvar_dados_site(dados: dict, arquivo: str):
    """ Grava os dados no arquivo site/dados.js, que o site lê. """
    texto = pd.Series(dados).to_json(force_ascii=False)
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write('// Gerado pelo gerar_dados_site.py. Não edite à mão.\n')
        f.write('const DADOS = ' + texto + ';\n')
    print(f'Dados do site salvos em {arquivo}')


def main():
    """ Função principal: lê os CSVs, calcula os dados e gera o arquivo do site. """
    dados = carregar_dados(CAMINHO_CSV)
    print(f"{len(dados['estacoes'])} estações lidas")
    salvar_dados_site(montar_dados_site(dados), ARQUIVO_SITE)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as erro:
        raise SystemExit(f'Erro: {erro}')

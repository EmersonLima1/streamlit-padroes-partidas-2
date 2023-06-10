import streamlit as st
import pandas as pd

def extrair_resultados(resultado):
    if resultado != '?\n\n?':
        resultado_split = resultado.split('\n\n')
        primeiro_tempo = resultado_split[1]
        tempo_final = resultado_split[0]
        return primeiro_tempo, tempo_final
    else:
        return None, None

def analisar_partidas(df, primeiro_tempo, tempo_final, num_total_partidas, num_conjuntos):
    resultado = {}
    partidas_selecionadas = df[(df['Primeiro tempo'] == primeiro_tempo) & (df['Tempo final'] == tempo_final)]['Partidas']

    for partida in partidas_selecionadas:
        lista_partidas = []
        inicio = partida - 1
        fim = inicio + num_total_partidas

        for i in range(inicio, fim):
            conjunto_partidas = df.loc[i+1:i+num_conjuntos, 'Tempo final'].tolist()
            lista_partidas.append(conjunto_partidas)

        resultado[partida] = lista_partidas

    return resultado

def criar_novo_dicionario(resultado_analise, num_total_partidas):
    novo_dicionario = {}

    for i in range(num_total_partidas):
        novo_dicionario[i + 1] = []

        for chave in resultado_analise:
            if i < len(resultado_analise[chave]):
                novo_dicionario[i + 1].append(resultado_analise[chave][i])

        if len(novo_dicionario[i + 1]) == 0:
            del novo_dicionario[i + 1]
            break

    return novo_dicionario

def processar_planilha(uploaded_file):
    df_resultados = pd.DataFrame()

    # Carregar o arquivo Excel
    xls = pd.ExcelFile(uploaded_file)

    # Obter o nome de cada página no arquivo Excel
    sheet_names = xls.sheet_names

    for sheet_name in sheet_names:
        # Tratando o arquivo Excel e obtendo o DataFrame tratado
        df = pd.read_excel(xls, sheet_name=sheet_name)

        # Define a primeira linha como os nomes das colunas
        df.columns = df.iloc[0]

        # Remove a primeira linha, que agora são os nomes das colunas duplicados
        df = df[1:].reset_index(drop=True)

        # Obtém todas as colunas, exceto as duas últimas
        colunas_para_manter = df.columns[:-3]

        # Mantém apenas as colunas selecionadas
        df = df[colunas_para_manter]

        # Inverte o dataframe
        df = df.sort_index(ascending=False)

        # Reseta o index
        df = df.reset_index(drop=True)

        df['Partidas'] = range(1, len(df) + 1)

        df = df.dropna(subset=['Primeiro tempo', 'Tempo final'])

        df = df[~df['Primeiro tempo'].str.contains('\.', na=False) & ~df['Tempo final'].str.contains('\.', na=False)]

        df['Primeiro tempo'] = df['Primeiro tempo'].replace('oth', '9x9')

        # Remover células com valor "?"
        df = df[(df['Primeiro tempo'] != '?') & (df['Tempo final'] != '?')]

        df_novo = df.copy()

        primeiro_tempo, tempo_final = extrair_resultados(df_novo['Primeiro tempo'].iloc[0])

        if primeiro_tempo is not None and tempo_final is not None:
            resultado_analise = analisar_partidas(df_novo, primeiro_tempo, tempo_final, num_total_partidas, 3)

            novo_dicionario = criar_novo_dicionario(resultado_analise, num_total_partidas)

            df_resultados = pd.concat([df_resultados, pd.DataFrame(novo_dicionario)])

    return df_resultados

# Interface do Streamlit
st.title("Análise de Planilhas")
st.write("Faça o upload de um arquivo Excel para realizar a análise.")

uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xls", "xlsx"])

if uploaded_file is not None:
    df_resultado = processar_planilha(uploaded_file)
    st.write(df_resultado)

# Aqui você pode adicionar o código para criar o DataFrame df_resultados_sintetico
df_resultados_sintetico = pd.DataFrame()

if not df_resultado.empty:
    num_total_partidas = len(df_resultado.columns)
    num_conjuntos = len(df_resultado.index)

    for i in range(1, num_total_partidas + 1):
        data = []
        for j in range(1, num_conjuntos + 1):
            partidas = df_resultado[i][j]
            counts = {}
            for partida in partidas:
                for item in partida:
                    counts[item] = counts.get(item, 0) + 1
            data.extend(list(counts.values()))
        df_resultados_sintetico[i] = data

    # Incluir as colunas do DataFrame df_resultado no DataFrame df_resultados_sintetico
    df_resultados_sintetico.columns = df_resultado.columns

    # Incluir a linha "Total" no DataFrame df_resultados_sintetico
    df_resultados_sintetico.loc['Total'] = df_resultados_sintetico.sum()

    # Adicionar a porcentagem em relação ao número total de chaves
    num_total = df_resultados_sintetico.loc['Total'].sum()
    total_percent = "{:.2%}".format(1 / num_total)

    # Aplicar formatação apenas a partir da segunda coluna em diante
    df_resultados_sintetico.iloc[:, 1:] = df_resultados_sintetico.iloc[:, 1:].applymap(lambda x: str(x) + f'/{num_total} ({float(x)/num_total:.2%})' if isinstance(x, int) else x)

    # Ordenar o DataFrame em ordem decrescente pelas colunas especificadas
    df_resultados_sintetico = df_resultados_sintetico.sort_values(by=df_resultados_sintetico.columns[1:], ascending=False)

    # Resetar os índices do DataFrame após a ordenação
    df_resultados_sintetico = df_resultados_sintetico.reset_index(drop=True)

    st.write(df_resultados_sintetico)

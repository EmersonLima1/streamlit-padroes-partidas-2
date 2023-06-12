import requests
import pandas as pd
import streamlit as st
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(page_title="InPES Futebol Virtual", page_icon=":soccer:")

st.title('**Resultados do Futebol Virtual**')
st.write('\n\n')

# Perguntas para o usuário
primeiro_tempo1 = st.selectbox("Qual o resultado do primeiro tempo?", ['0x0','0x1','0x2','0x3','0x4','0x5','1x0','1x1','1x2','1x3','1x4','1x5','2x0','2x1','2x2','2x3','2x4','2x5','3x0','3x1','3x2','3x3','3x4','3x5','4x0','4x1','4x2','4x3','4x4','4x5','5x0','5x1','5x2','5x3','5x4','5x5'])
tempo_final1 = st.selectbox("Qual o resultado do tempo final?", ['0x0','0x1','0x2','0x3','0x4','0x5','1x0','1x1','1x2','1x3','1x4','1x5','2x0','2x1','2x2','2x3','2x4','2x5','3x0','3x1','3x2','3x3','3x4','3x5','4x0','4x1','4x2','4x3','4x4','4x5','5x0','5x1','5x2','5x3','5x4','5x5'])
num_total_partidas = st.number_input("Qual a quantidade de partidas após a ocorrência do padrão você deseja analisar?", min_value=1, value=50, step=1)
num_conjuntos = st.selectbox("Qual o padrão de tip (de 1 a 5 jogos consecutivos)?", [1, 2, 3, 4, 5])

def gerar_resultados():

  sheet_id = '1-OpwOkZbencR-EGbQiTkgDWKzEY8Y-t0B7TlmRuUlaY'
  url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'

  response = requests.get(url)
  data = response.content

  excel_data = pd.ExcelFile(BytesIO(data), engine='openpyxl')
  sheet_names = excel_data.sheet_names

  for sheet_name in sheet_names:
      
      # Tratando o arquivo Excel e obtendo o DataFrame tratado
      df = excel_data.parse(sheet_name)

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

      # Função para extrair os resultados do primeiro tempo, tempo final e partidas
      def extrair_resultados(resultado):
          if resultado != '?\n\n?':
              resultado_split = resultado.split('\n\n')
              primeiro_tempo = resultado_split[1]
              tempo_final = resultado_split[0]
              return primeiro_tempo, tempo_final
          else:
              return None, None

      # Criando listas vazias para armazenar os valores extraídos
      primeiro_tempo_list = []
      tempo_final_list = []
      partidas_list = []

      # Percorrendo o dataframe original e extraindo os resultados
      for index, row in df.iterrows():
          for col in df.columns[1:]:
              resultado = row[col]
              primeiro_tempo, tempo_final = extrair_resultados(resultado)
              primeiro_tempo_list.append(primeiro_tempo)
              tempo_final_list.append(tempo_final)
              partidas_list.append(col)

      # Criando o novo dataframe com as colunas desejadas
      df_novo = pd.DataFrame({
          'Primeiro tempo': primeiro_tempo_list,
          'Tempo final': tempo_final_list,
      })

      num_linhas = len(df_novo)
      df_novo['Partidas'] = range(1, num_linhas + 1)

      # Obtendo o nome da última coluna
      ultima_coluna = df_novo.columns[-1]

      # Extraindo a coluna "Partidas"
      coluna_partidas = df_novo.pop(ultima_coluna)

      # Inserindo a coluna "Partidas" na terceira posição
      df_novo.insert(0, ultima_coluna, coluna_partidas)

      df_novo = df_novo.dropna(subset=['Primeiro tempo', 'Tempo final'])

      df_novo = df_novo[~df_novo['Primeiro tempo'].str.contains('\.', na=False) & ~df_novo['Tempo final'].str.contains('\.', na=False)]

      df_novo['Primeiro tempo'] = df_novo['Primeiro tempo'].replace('oth', '9x9')

      # Remover células com valor "?"
      df_novo = df_novo[(df_novo['Primeiro tempo'] != '?') & (df_novo['Tempo final'] != '?')]

      df1 = df_novo

      def analisar_partidas(df1, primeiro_tempo, tempo_final, num_total_partidas, num_conjuntos):
          resultado = {}
          partidas_selecionadas = df1[(df1['Primeiro tempo'] == primeiro_tempo) & (df1['Tempo final'] == tempo_final)]['Partidas']
          
          for partida in partidas_selecionadas:
              lista_partidas = []
              inicio = partida - 1
              fim = inicio + num_total_partidas
              
              for i in range(inicio, fim):
                  conjunto_partidas = df1.loc[i+1:i+num_conjuntos, 'Tempo final'].tolist()
                  lista_partidas.append(conjunto_partidas)
              
              resultado[partida] = lista_partidas
          
          return resultado

      # Chamada da função para análise das partidas
      resultado_analise = analisar_partidas(df1, primeiro_tempo1, tempo_final1, num_total_partidas, num_conjuntos)

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

      dicionario = criar_novo_dicionario(resultado_analise, num_total_partidas)

      #num_conjuntos = len(dicionario[1][0])  # Número de valores em cada lista
      # Selecionar linhas com base nas condições
      selecao = (df_novo['Primeiro tempo'] == primeiro_tempo1) & (df_novo['Tempo final'] == tempo_final1)
      df_selecionado = df_novo[selecao]

      # Armazenar o número total de linhas selecionadas
      num_total = len(df_selecionado)

      data = []  # Lista para armazenar os dados das linhas do dataframe

      for key, lista_chave in dicionario.items():
          row = [format(key)]
          AM_counts = [0] * num_conjuntos
          AN_counts = [0] * num_conjuntos
          Over_15_counts = [0] * num_conjuntos
          Over_25_counts = [0] * num_conjuntos
          Over_35_counts = [0] * num_conjuntos
          total_AM = 0
          total_AN = 0
          total_over_15 = 0
          total_over_25 = 0
          total_over_35 = 0
          
          for lista in lista_chave:
              AM_found = False
              AN_found = False
              over_15_found = False
              over_25_found = False
              over_35_found = False
              
              for i, val in enumerate(lista):
                  score1, score2 = val.split('x')
                  score1 = int(score1)
                  score2 = int(score2)
                  
                  if not AM_found and score1 >= 1 and score2 >= 1:
                      AM_counts[i] += 1
                      AM_found = True
                      
                      if score1 + score2 > 1.5:
                          Over_15_counts[i] += 1
                          over_15_found = True
                          
                      if score1 + score2 > 2.5:  # Verificar se não foi contado como over 1.5
                          Over_25_counts[i] += 1
                          over_25_found = True
                          
                      if score1 + score2 > 3.5:  # Verificar se não foi contado como over 1.5 e over 2.5
                          Over_35_counts[i] += 1
                          over_35_found = True
                  
                  if not AN_found and (score1 < 1 or score2 < 1):
                      AN_counts[i] += 1
                      AN_found = True               
                                          
              total_AM += int(AM_found)
              total_AN += int(AN_found)
              total_over_15 += int(over_15_found)
              total_over_25 += int(over_25_found)
              total_over_35 += int(over_35_found)
              
          row.extend(Over_15_counts)
          row.extend(Over_25_counts)
          row.extend(Over_35_counts)
          row.extend(AM_counts)
          row.extend(AN_counts)
          row.append(sum(Over_15_counts))
          row.append(sum(Over_25_counts))
          row.append(sum(Over_35_counts))
          row.append(sum(AM_counts))
          row.append(sum(AN_counts))
          data.append(row)

      columns = ['Partidas após'] + [f'{i} (Over 1.5)' for i in range(1, num_conjuntos+1)] + [f'{i} (Over 2.5)' for i in range(1, num_conjuntos+1)] + [f'{i} (Over 3.5)' for i in range(1, num_conjuntos+1)] + [f'{i} (AM)' for i in range(1, num_conjuntos+1)] + [f'{i} (AN)' for i in range(1, num_conjuntos+1)] + ['Total Over 1.5', 'Total Over 2.5', 'Total Over 3.5', 'Total AM', 'Total AN']
      df = pd.DataFrame(data, columns=columns)
      df.iloc[:, 1:1+num_conjuntos*3] = df.iloc[:, 1:1+num_conjuntos*3].apply(pd.to_numeric)
      df['Total Over 1.5'] = df.iloc[:, 1:1+num_conjuntos].sum(axis=1)
      df['Total Over 2.5'] = df.iloc[:, 1+num_conjuntos:1+2*num_conjuntos].sum(axis=1)
      df['Total Over 3.5'] = df.iloc[:, 1+2*num_conjuntos:1+3*num_conjuntos].sum(axis=1)
      df['Total AM'] = df.iloc[:, 1+3*num_conjuntos:1+4*num_conjuntos].sum(axis=1)
      df['Total AN'] = df.iloc[:, 1+4*num_conjuntos:1+5*num_conjuntos].sum(axis=1)

      # Adicionar a porcentagem em relação ao número total de chaves
      total_percent = "{:.2%}".format(1 / num_total)

      # Aplicar formatação apenas a partir da segunda coluna em diante
      df.iloc[:, 1:] = df.iloc[:, 1:].applymap(lambda x: str(x) + f'/{num_total} ({float(x)/num_total:.2%})' if isinstance(x, int) else x)

      # Ordenar o DataFrame em ordem decrescente pelas colunas especificadas
      df = df.sort_values(by=['Total AM', 'Total AN', 'Total Over 1.5', 'Total Over 2.5', 'Total Over 3.5'], ascending=False)

      # Resetar os índices do DataFrame após a ordenação
      df = df.reset_index(drop=True)

      # Exibir o nome da página atual
      st.write(f"Resultado de {sheet_name}:")
      # Exibir as 10 primeiras linhas do dataframe obtido
      st.write(df.head(10))

# Botão "Gerar resultados"
if st.button("Gerar resultados"):
    gerar_resultados()

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO

def get_bonds(ano):
    # URL do site
    url = f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value={int(ano)}'

    # Fazendo a requisição HTTP
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')

    # Lendo a tabela com pandas
    df = pd.read_html(str(table))[0]
    df['Date'] = pd.to_datetime(df['Date'],format="%m/%d/%Y",errors="coerce")
    df = df.dropna(axis=1).set_index(df['Date']).drop('Date',axis=1)

    # Mostrando a tabela
    return df

titulo = st.title("US Bonds")
anos = st.multiselect("Selecione os anos para a gerar a tabela",range(2020,2026))
gerar_tabela = st.button("Gerar tabela")

if gerar_tabela:
    dfs = []
    progresso = st.progress(0, text="Carregando dados...")
    total = len(anos)

    for i, ano in enumerate(anos):
        try:
            df_ano = get_bonds(ano)
            dfs.append(df_ano)
        except Exception as e:
            st.error(f"Erro ao buscar dados do ano {ano}: {e}")
        progresso.progress((i + 1) / total, text="Carregando...")

    progresso.empty()  # remove a barra ao final

    if dfs:
        df_merge = pd.concat(dfs).sort_values(by="Date", ascending=False)
        st.dataframe(df_merge)

        # exportar para Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_merge.to_excel(writer, index=True, sheet_name="YieldCurve")

            # aplicar formato de data dd/mm/yyyy
            workbook  = writer.book
            worksheet = writer.sheets["YieldCurve"]
            for cell in worksheet["A"][1:]:  # coluna A = Date
                cell.number_format = "DD/MM/YYYY"
            worksheet.column_dimensions["A"].width = 11
        data_xlsx = output.getvalue()

        dowload = st.download_button(
            label="Clique aqui para baixar o arquivo Excel",
            data=data_xlsx,
            file_name="us_bonds_wacc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Nenhum dado carregado.")
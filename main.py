import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from textwrap import wrap
from streamlit_gsheets import GSheetsConnection
from streamlit_js_eval import streamlit_js_eval

from constantes import *
from dados import *
from visualizacoes import *

if "status" not in st.session_state:
    st.session_state.status="INICIO"

match st.session_state.status:
    case "INICIO":
        st.set_page_config(layout = "centered")
        st.header("Painel de controle financeiro")
        with st.expander("Faça sua configuração inicial"):
            st.write("1) Faça uma cópia da planilha base para o seu Google Drive pessoal.")
            st.link_button("Planilha base", "https://docs.google.com/spreadsheets/d/1PowEej-4JGijhx_B3CqVNQ7kUZQKjSYreniuXI7zUTw/edit?usp=sharing")
            st.write("2) Torne a planilha pública no botão de compartilhar no canto superior direito.")
            st.write("3) Preencha os dados na sua planilha de acordo com as instruções presentes nela.")
            st.write("4) Copie o link da sua planilha no navegador e cole no campo abaixo para carregar seu painel.")
        url=st.text_input("Insira o link para a sua planilha do GSheet", key="url_dados")
        
        iniciar=st.button("Carregue meu painel")
        
        if iniciar:
            st.session_state.status="CARREGANDO"
            st.rerun()

    case "CARREGANDO":
        st.set_page_config(layout = "centered")
        st.write("Estou carregando sua planilha")
        url_ori=st.session_state.url_dados if "url_dados" in st.session_state else st.session_state.url
        url=url_ori[:url_ori.index("/edit")]+"/export?format=xlsx"
        
        #url="controle_financeiro.xlsx"
        
        gids=pd.read_excel(url, sheet_name="GIDs", dtype=schemas["gids"], na_filter = False)
        tem_gids = not "" in gids["GID"].tolist()

        if tem_gids:
            #print(gids)
            gids={linha[1].Aba: linha[1].GID for linha in gids.iterrows()}
            conn = st.connection("gsheets", type=GSheetsConnection)
            validacao=aplica_schema(conn.read(spreadsheet = url, worksheet=gids["Validação"], ttl=1), schemas["validacao"], list(converters["validacao"]))
            despesa=aplica_schema(conn.read(spreadsheet = url, worksheet=gids["Despesa"], ttl=1), schemas["despesa"], list(converters["despesa"]))
            receita=aplica_schema(conn.read(spreadsheet = url, worksheet=gids["Receita"], ttl=1), schemas["receita"], list(converters["receita"]))
            gympass=aplica_schema(conn.read(spreadsheet = url, worksheet=gids["Gympass"], ttl=1), schemas["gympass"], list(converters["gympass"]))
            viagem=aplica_schema(conn.read(spreadsheet = url, worksheet=gids["Viagem"], ttl=1), schemas["viagem"], list(converters["viagem"]))
        else:
            validacao=pd.read_excel(url, sheet_name="Validação", dtype=schemas["validacao"], na_filter = False)
            despesa=pd.read_excel(url, sheet_name="Despesa", dtype=schemas["despesa"], na_filter = False, converters=converters["despesa"])
            receita=pd.read_excel(url, sheet_name="Receita", dtype=schemas["receita"], na_filter = False, converters=converters["receita"])
            gympass=pd.read_excel(url, sheet_name="Gympass", dtype=schemas["gympass"], na_filter = False, converters=converters["gympass"])
            viagem=pd.read_excel(url, sheet_name="Viagem", dtype=schemas["viagem"], na_filter = False, converters=converters["viagem"])

        st.write("Terminei, vou verificar se tem algum problema com ela")
        assert_validacao=valida_dataframe(validacao, set(schemas["validacao"].keys())|set(converters["validacao"].keys()), "Validação")
        assert_despesa=valida_dataframe(despesa, set(schemas["despesa"].keys())|set(converters["despesa"].keys()), "Despesa")
        assert_receita=valida_dataframe(receita, set(schemas["receita"].keys())|set(converters["receita"].keys()), "Receita")
        assert_gympass=valida_dataframe(gympass, set(schemas["gympass"].keys())|set(converters["gympass"].keys()), "Gympass")
        assert_viagem=valida_dataframe(viagem, set(schemas["viagem"].keys())|set(converters["viagem"].keys()), "Viagem")
        dados=ajusta_dataframes(validacao, despesa, receita, gympass, viagem)
        assert_integridade=valida_integridade_referencial(dados)
        
        if all([assert_validacao, assert_despesa, assert_receita, assert_gympass, assert_viagem, assert_integridade]):
            st.write("Tudo certo, vou fazer alguns cálculos aqui")
            st.session_state.dados=dados
            st.write("Prontinho! Vou gerar seu painel")
            st.session_state.status="PAINEL"
            st.session_state.url=url_ori
            st.session_state.tem_gids=tem_gids
            if tem_gids:
                st.session_state.conexao=conn
                st.session_state.gids=gids
            st.rerun()
        
    case "PAINEL":
        st.set_page_config(layout = "wide")
        
        _, dia_fatura, datas, _, aglomerado_dia, aglomerado_dia_tipo, gympass_atividades, gympass_mes, anual, despesa_anual_tipo, custo_viagem ,despesas_parceladas=agrega_dfs(st.session_state.dados)
        window_width=streamlit_js_eval(js_expressions='screen.width', key = 'SCR')

        colunas = st.columns(5)
        painel_bot=colunas[0].button("Painel")
        fluxo_bot=colunas[1].button("Fluxo")
        recarregar=colunas[4].button("Recarregar dados")
        
        st.markdown("<h1 style='text-align: center; color: black;'>Meu painel financeiro</h1>", unsafe_allow_html=True)
        hoje=datetime.now()
        if hoje.day<dia_fatura:
            hoje=hoje-relativedelta(months=1)
        anos=datas["ano_fatura"].unique()

        colunas = st.columns(5)
        ano=colunas[0].selectbox("Ano", anos, index=int(np.where(anos==hoje.year)[0][0]) if hoje.year in anos else 0)
        meses=datas[datas["ano_fatura"]==ano]["mes_fatura"].unique()
        mes=colunas[1].selectbox("Mês", meses, index=int(np.where(meses==hoje.month)[0][0]) if hoje.month in meses else 0)
        media_movel=colunas[2].selectbox("Meses média móvel", range(1,7), index=2)
        
        aglomerado_dia=aglomerado_dia[(aglomerado_dia["data"]>=pd.to_datetime(date(ano, mes, dia_fatura))) & (aglomerado_dia["data"]<pd.to_datetime(date(ano+(1 if mes==12 else 0), (mes+1)%12, dia_fatura)))]
        aglomerado_dia["data"]=aglomerado_dia["data"].dt.date
        aglomerado_dia_tipo=aglomerado_dia_tipo[(aglomerado_dia_tipo["data"]>=pd.to_datetime(date(ano, mes, dia_fatura))) & (aglomerado_dia_tipo["data"]<pd.to_datetime(date(ano+(1 if mes==12 else 0), (mes+1)%12, dia_fatura)))]
        aglomerado_dia_tipo["data"]=aglomerado_dia_tipo["data"].dt.date
        gympass_atividades=gympass_atividades[(gympass_atividades["ano"]==int(ano))&(gympass_atividades["mes"]==int(mes))]
        gympass_mes=gympass_mes[gympass_mes["ano"]==int(ano)]
        anual=anual[anual["ano_fatura"]==int(ano)]
        despesa_anual_tipo=despesa_anual_tipo[despesa_anual_tipo["ano_fatura"]==int(ano)]
        custo_viagem=custo_viagem[custo_viagem["ano_fatura"]==int(ano)]
        despesas_parceladas=despesas_parceladas[despesas_parceladas["ano_fatura"]==int(ano)]

        if not aglomerado_dia.empty or not aglomerado_dia_tipo.empty:
            st.header("Resultados mensais")
            with st.expander("", expanded=True):
                colunas = st.columns(2)
                if not aglomerado_dia.empty: colunas[0].altair_chart(gera_visu_evolucao_diaria(aglomerado_dia, window_width/4), use_container_width=True)
                if not aglomerado_dia_tipo.empty: colunas[1].altair_chart(gera_visu_tipo_diaria(aglomerado_dia_tipo, window_width/4), use_container_width=True)

        if not gympass_atividades.empty or not gympass_mes.empty:
            st.header("Gympass")
            with st.expander(""):
                colunas = st.columns(2)
                if not gympass_atividades.empty: colunas[0].altair_chart(gera_visu_gympass_usos(gympass_atividades, window_width/4), use_container_width=True)
                if not gympass_mes.empty: colunas[1].altair_chart(gera_visu_gympass_mes(gympass_mes, media_movel, window_width/4), use_container_width=True)

        if not anual.empty or not despesa_anual_tipo.empty:
            st.header("Resultados anuais")
            with st.expander(""):
                colunas = st.columns(2)
                if not anual.empty: colunas[0].altair_chart(gera_visu_anual(anual, window_width/4), use_container_width=True)
                if not despesa_anual_tipo.empty: colunas[1].altair_chart(gera_visu_tipo_anual(despesa_anual_tipo, window_width/4), use_container_width=True)

        if not custo_viagem.empty or not despesas_parceladas.empty:
            st.header("Outros resultados")
            with st.expander(""):
                colunas = st.columns(2)
                if not custo_viagem.empty: colunas[0].altair_chart(gera_visu_viagens(custo_viagem, window_width/4), use_container_width=True)
                if not despesas_parceladas.empty: colunas[1].altair_chart(gera_visu_parceladas(despesas_parceladas, window_width/4), use_container_width=True)
        
        if fluxo_bot:
            st.session_state.status="FLUXO"
            st.rerun()
        if recarregar:
            st.session_state.status="CARREGANDO"
            st.rerun()
        
    case "FLUXO":
        st.set_page_config(layout = "centered")
        
        gympass=st.session_state.dados["gympass"]
        _, dia_fatura, datas, fluxo, _, _, _, _, _, _, _, _=agrega_dfs(st.session_state.dados)

        colunas = st.columns(5)
        painel_bot=colunas[0].button("Painel")
        fluxo_bot=colunas[1].button("Fluxo")
        recarregar=colunas[4].button("Recarregar dados")
        
        st.header("Fluxo do mês")
        hoje=datetime.now()
        anos=datas["ano_fatura"].unique()

        colunas = st.columns(5)
        ano=colunas[0].selectbox("Ano", anos, index=int(np.where(anos==hoje.year)[0][0]) if hoje.year in anos else 0)
        meses=datas[datas["ano_fatura"]==ano]["mes_fatura"].unique()
        mes=colunas[1].selectbox("Mês", meses, index=int(np.where(meses==hoje.month)[0][0]) if hoje.month in meses else 0)
        tabela=colunas[2].selectbox("Tabela", ["Saldo", "Gympass"], index=0)
        
        fluxo=fluxo[(fluxo["data"]>=pd.to_datetime(date(ano, mes, dia_fatura))) & (fluxo["data"]<pd.to_datetime(date(ano+(1 if mes==12 else 0), (mes+1)%12, dia_fatura)))].drop(columns=["ano_fatura", "mes_fatura"])
        fluxo["data"]=fluxo["data"].dt.date
        gympass=gympass[(gympass["data"]>=pd.to_datetime(date(ano, mes, 1))) & (gympass["data"]<pd.to_datetime(date(ano+(1 if mes==12 else 0), (mes+1)%12, 1)))].drop(columns=["ano", "mes"])
        gympass["data"]=gympass["data"].dt.date
        st.dataframe(fluxo if tabela=="Saldo" else gympass, use_container_width=True, height=550, hide_index=True)
        
        if painel_bot:
            st.session_state.status="PAINEL"
            st.rerun()
        if recarregar:
            st.session_state.status="CARREGANDO"
            st.rerun()
 
    case "CADASTRO":
        st.set_page_config(layout = "centered")

        colunas = st.columns(5)
        painel_bot=colunas[0].button("Painel")
        fluxo_bot=colunas[1].button("Fluxo")
        cad_des=colunas[2].button("Cadastro")
        
        st.header("Novos cadastros")
        colunas=st.columns(5)
        validacao_bot=colunas[0].button("Validação")
        despesa_bot=colunas[1].button("Despesa")
        receita_bot=colunas[2].button("Receita")
        gympass_bot=colunas[3].button("Gympass")
        viagem_bot=colunas[4].button("Viagem")
        
        if "item" in st.session_state:
            # match st.session_state.item:
            if st.session_state.item:
                # case 
                if st.session_state.item=="despesa":
                    validacao=st.session_state.dados[0].replace("nan", np.nan)
                    colunas=st.columns([1,2,1])
                    data=colunas[0].date_input("Data", format="DD/MM/YYYY")
                    descricao=colunas[1].text_input("Descrição")
                    valor=colunas[2].number_input("Valor")
                    colunas=st.columns(4)
                    tipo=colunas[0].selectbox("Tipo", validacao["tipo_de_despesa"].dropna().unique().tolist())
                    transacao=colunas[1].selectbox("Transação", validacao["tipo_de_transacao_de_despesa"].dropna().unique().tolist())
                    conta=colunas[2].selectbox("Conta", validacao["conta"].dropna().unique().tolist())
                    viagem=colunas[3].selectbox("Viagem", validacao["viagem"].dropna().unique().tolist()+[""])
                    
                    cadastrar=st.button("Cadastrar")
                    
                    novo_registro=pd.DataFrame({
                                    "Data":[data.strftime("%d/%m/%Y")],
                                    "Descrição":[descricao],
                                    "Valor":[valor],
                                    "Tipo":[tipo],
                                    "Transação":[transacao],
                                    "Conta":[conta],
                                    "Viagem":[np.nan if viagem=="" else viagem]
                                })
                    print(novo_registro)
                    print(st.session_state.url)
                    if cadastrar:
                        conexao=st.session_state.conexao
                        
                        completo=pd.concat([conexao.read(spreadsheet = st.session_state.url, worksheet=st.session_state.gids["Despesa"]), novo_registro])
                        conexao.update(spreadsheet = st.session_state.url, worksheet=st.session_state.gids["Despesa"], data=completo)

                        st.write("Despesa adicionada")
        
        if validacao_bot:
            st.session_state.item="validacao"
            st.rerun()
        if despesa_bot:
            st.session_state.item="despesa"
            st.rerun()
        if receita_bot:
            st.session_state.item="receita"
            st.rerun()
        if gympass_bot:
            st.session_state.item="gympass"
            st.rerun()
        if viagem_bot:
            st.session_state.item="viagem"
            st.rerun()
        
        if painel_bot:
            st.session_state.status="PAINEL"
            st.rerun()
        if fluxo_bot:
            st.session_state.status="FLUXO"
            st.rerun()



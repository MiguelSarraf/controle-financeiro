import streamlit as st
import pandas as pd
import numpy as np
from pandas.tseries.offsets import DateOffset
from unidecode import unidecode
from datetime import date
from dateutil.relativedelta import relativedelta

from constantes import *

def aplica_schema(df, schema, datas):
    for coluna in schema:
        if schema[coluna]=="float":
            df[coluna]=df[coluna].str.replace("^R\$ *", "", regex=True).str.replace(".", "").str.replace(",", ".")
        df[coluna]=df[coluna].astype(schema[coluna])
    for coluna in datas:
        df[coluna]=pd.to_datetime(df[coluna], format="%d/%m/%Y")
    return df

def valida_dataframe(df, colunas, nome):
    passa=True
    if df.empty:
        st.write(f"A aba {nome} está vazia.")
        passa=False
    if set(df.columns)!=colunas:
        st.write(f"A aba {nome} não contém as colunas corretas.")
        st.write(f"Colunas esperadas: {', '.join(colunas)}")
        passa=False
    return passa

def ajusta_dataframes(validacao, despesa, receita, gympass, viagem):
    dfs={}
    dfs["validacao"]=validacao
    dfs["despesa"]=despesa
    dfs["receita"]=receita
    dfs["gympass"]=gympass
    dfs["viagem"]=viagem
    for nome, df in dfs.items():
        df.columns=[unidecode(coluna.lower().replace(" ", "_")) for coluna in df.columns]
    return dfs

def valida_integridade_referencial(dfs):
    passa=True
    for condicao in integridade:
        tabela, campo, campo_val=condicao
        check=dfs[tabela][campo].isin(dfs["validacao"][campo_val].to_list()).all()
        if not check:
            st.write(f"Coluna {campo} da aba {tabela} tem valores que não pertencem à coluna {campo_val} da aba de validação")
        passa=passa and check
    return passa

def agrega_dfs(dados):
    validacao=dados["validacao"]
    despesa=dados["despesa"]
    receita=dados["receita"]
    gympass=dados["gympass"]
    viagem=dados["viagem"]
    
    dia_fatura=validacao["fechamento_da_fatura"].iloc[0]
    
    datas=despesa.copy()
    datas["ano"]=datas["data"].dt.year
    datas["mes"]=datas["data"].dt.month
    datas=datas[["ano", "mes"]].sort_values(["ano", "mes"], ascending=False).drop_duplicates()
    min_data=date(datas["ano"].min(), datas[datas["ano"]==datas["ano"].min()]["mes"].min(),dia_fatura)-relativedelta(months=1)
    max_data=date(datas["ano"].max(), datas[datas["ano"]==datas["ano"].max()]["mes"].max(),dia_fatura)+relativedelta(months=1)
    datas=pd.DataFrame(index=pd.date_range(min_data, max_data))
    
    datas.reset_index(inplace=True)
    datas.rename(columns={"index":"data"}, inplace=True)

    datas["eh_mes_anterior"]=pd.Series(datas["data"].dt.day<dia_fatura)
    datas["ano_fatura"]=np.where(datas["eh_mes_anterior"], datas["data"]-DateOffset(months=1), datas["data"])
    datas["ano_fatura"]=datas["ano_fatura"].dt.year
    datas["mes_fatura"]=np.where(datas["eh_mes_anterior"], datas["data"]-DateOffset(months=1), datas["data"])
    datas["mes_fatura"]=datas["mes_fatura"].dt.month
    
    despesa["valor"]=-despesa["valor"]
    despesa_receita=pd.concat([despesa[["data", "descricao", "valor", "tipo"]], receita[["data", "descricao", "valor"]]])
    despesa["valor"]=-despesa["valor"]
    
    fluxo=despesa_receita.merge(datas[["data", "ano_fatura", "mes_fatura"]], on="data").fillna("").sort_values("data")
    fluxo=fluxo.fillna(0).round(2)
    
    aglomerado_dia=datas[["data", "ano_fatura", "mes_fatura"]].merge(despesa_receita.groupby("data").agg({"valor":"sum"}).reset_index(), on="data", how="left").set_index("data").groupby(["ano_fatura", "mes_fatura"]).agg({"valor":"cumsum"}).fillna(method='ffill').reset_index()
    aglomerado_dia=aglomerado_dia.fillna(0).round(2)
    
    aglomerado_dia_tipo=datas[["data", "ano_fatura", "mes_fatura"]].merge(despesa.groupby(["data", "tipo"]).agg({"valor":"sum"}).reset_index(), on="data", how="left")
    aglomerado_dia_tipo=aglomerado_dia_tipo.fillna(0).round(2)
    
    gympass["ano"]=gympass["data"].dt.year
    gympass["mes"]=gympass["data"].dt.month
    gympass_atividades=gympass.groupby(["ano", "mes", "atividade", "unidade"]).count().reset_index().rename(columns={"data":"num_usos"})

    gympass_mes=gympass.groupby(["ano", "mes"]).count().reset_index().rename(columns={"data":"num_usos"}).merge(despesa[despesa["descricao"]=="Gympass"].merge(datas, on="data", how="inner").groupby(["ano_fatura", "mes_fatura"])["valor"].sum().reset_index(), left_on=["ano", "mes"], right_on=["ano_fatura", "mes_fatura"])
    gympass_mes["custo_uso"]=(gympass_mes["valor"]/gympass_mes["num_usos"]).round(2)
    
    despesa=despesa.merge(datas[["data", "ano_fatura", "mes_fatura"]], on="data", how="left")
    receita=receita.merge(datas[["data", "ano_fatura", "mes_fatura"]], on="data", how="left")
    
    despesa_anual_tipo=despesa.groupby(["ano_fatura", "mes_fatura", "tipo"]).agg({"valor":"sum"}).reset_index()
    despesa_anual_tipo["um"]=1
    despesa_anual_tipo["data"]=pd.to_datetime({"year":despesa_anual_tipo["ano_fatura"],"month": despesa_anual_tipo["mes_fatura"], "day":despesa_anual_tipo["um"]})
    despesa_anual_tipo=despesa_anual_tipo.fillna(0).round(2)
    
    anual=despesa.groupby(["ano_fatura", "mes_fatura"]).agg({"valor":"sum"}).rename(columns={"valor":"despesa"}).reset_index().merge(receita.groupby(["ano_fatura", "mes_fatura"]).agg({"valor":"sum"}).rename(columns={"valor":"receita"}).reset_index(), on=["ano_fatura", "mes_fatura"], how="outer")
    anual=anual.fillna(0).round(2)
    anual["liquido"]=anual["receita"]-anual["despesa"]
    anual["um"]=1
    anual["data"]=pd.to_datetime({"year":anual["ano_fatura"],"month": anual["mes_fatura"], "day":anual["um"]})
    
    despesa_anual_tipo=despesa_anual_tipo.merge(anual[["data", "despesa"]], on="data")
    despesa_anual_tipo["porcentagem"]=despesa_anual_tipo["valor"]/despesa_anual_tipo["despesa"]
    
    custo_viagem=viagem.merge(despesa[despesa["viagem"].notna()].groupby("viagem").agg({"valor":"sum"}), on="viagem").merge(datas[["data", "ano_fatura", "mes_fatura"]], left_on="data_de_ida", right_on="data", how="left")
    custo_viagem["dias"]=(custo_viagem["data_de_volta"]-custo_viagem["data_de_ida"]).dt.days+1
    custo_viagem["custo"]=custo_viagem["valor"]/(custo_viagem["numero_de_pessoas"]*custo_viagem["dias"])
    custo_viagem=custo_viagem.fillna(0).round(2)
    
    despesas_parceladas=despesa[(despesa["descricao"].str.contains("/")) & (despesa["data"].dt.day==dia_fatura)].groupby(["ano_fatura", "mes_fatura"]).agg({"valor":"sum"}).reset_index()
    despesas_parceladas["um"]=1
    despesas_parceladas["data"]=pd.to_datetime({"year":despesas_parceladas["ano_fatura"],"month": despesas_parceladas["mes_fatura"], "day":despesas_parceladas["um"]})
    despesas_parceladas=despesas_parceladas.fillna(0).round(2)
    
    return validacao, dia_fatura, datas, fluxo, aglomerado_dia, aglomerado_dia_tipo, gympass_atividades, gympass_mes, anual, despesa_anual_tipo, custo_viagem, despesas_parceladas


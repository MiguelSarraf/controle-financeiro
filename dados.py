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

def ajusta_dataframes(validacao, despesa, receita, gympass, viagem, aplicacoes):
    dfs={}
    dfs["validacao"]=validacao
    dfs["despesa"]=despesa
    dfs["receita"]=receita
    dfs["gympass"]=gympass
    dfs["viagem"]=viagem
    dfs["aplicacoes"]=aplicacoes
    for nome, df in dfs.items():
        df.columns=[unidecode(coluna.lower().replace(" ", "_")) for coluna in df.columns]
    return dfs

def valida_integridade_referencial(dfs):
    passa=True
    for condicao in integridade:
        tabela, campo, campo_val=condicao
        if campo_val=="viagem_grupo":
            check=dfs[tabela][campo].isin(dfs["validacao"]["viagem"].to_list()+dfs["validacao"]["grupo"].to_list()).all()
        else:
            check=dfs[tabela][campo].isin(dfs["validacao"][campo_val].to_list()).all()
        if not check:
            st.write(f"Coluna {campo} da aba {tabela} tem valores que não pertencem à coluna {campo_val} da aba de validação")
        passa=passa and check
    return passa

def gera_anos(despesa, dia_fatura):
    return (despesa["data"] - DateOffset(days = dia_fatura)).dt.year.unique()

def gera_meses(despesa, dia_fatura, ano):
    despesa["data"] = despesa["data"] - DateOffset(days = dia_fatura)
    return despesa[despesa["data"].dt.year == ano]["data"].dt.month.unique()

def gera_datas_das_despesas(despesa, dia_fatura):
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

    return datas

def gera_dia_fatura(validacao):
    return validacao["fechamento_da_fatura"].iloc[0]

def gera_hoje(referencia):
    hoje=pd.DataFrame(index=[0])
    hoje["data"]=pd.Timestamp.today()
    hoje["data"]=hoje["data"].dt.date
    hoje=hoje[pd.to_datetime(hoje["data"]).isin(referencia["data"])]

    return hoje

def gera_datas(inicial, final, segunda_variavel=(None, [None])):
    dias_no_mes = (final-inicial).days

    nome, valores = segunda_variavel

    datas = {"data":[inicial + relativedelta(days=dia) for dia in range(dias_no_mes)][:]*len(valores)}
    if nome:
        datas[nome] = []
        for valor in valores:
            datas[nome] += [valor][:]*dias_no_mes

    datas = pd.DataFrame(datas)

    datas["data"] = pd.to_datetime(datas["data"])

    return datas

def gera_datas_do_mes(fatura, segunda_variavel=(None, [None])):
    proxima_fatura = fatura + relativedelta(months=1)

    return gera_datas(fatura, proxima_fatura, segunda_variavel)

def gera_datas_do_ano(fatura, segunda_variavel=(None, [None])):
    primeira_fatura = date(fatura.year, 1, fatura.day)
    ultima_fatura = date(fatura.year, 12, fatura.day) + relativedelta(months=1)

    datas = gera_datas(primeira_fatura, ultima_fatura, segunda_variavel)
    datas["ano"] = fatura.year
    datas["mes"] = np.where(
        datas["data"].dt.day < fatura.day,
        datas["data"].dt.month - 1,
        datas["data"].dt.month
    )

    return datas

def cria_kpis(despesa, receita, gympass, fatura):
    kpis = {"mensais":{}, "gympass":{}, "anuais":{}, "investimento":{}}
    datas_mes = gera_datas_do_mes(fatura)
    datas_ano = gera_datas_do_ano(fatura)

    custo_gympass = despesa[despesa["descricao"] == "Gympass"][["data", "valor"]]
    custo_gympass["ano"] = custo_gympass["data"].dt.year
    custo_gympass["mes"] = custo_gympass["data"].dt.month

    gympass["ano"] = gympass["data"].dt.year
    gympass["mes"] = gympass["data"].dt.month
    gympass = gympass[gympass["ano"] == fatura.year].groupby(["ano", "mes"]).agg({"data":"count"}).reset_index().rename(columns={"data":"usos"}).merge(custo_gympass, on=["ano", "mes"])
    gympass["custo_por_aula"] = gympass["valor"]/gympass["usos"]
    maior_uso = gympass[gympass["usos"] == max(gympass["usos"])]
    menor_uso = gympass[gympass["usos"] == min(gympass["usos"])]

    despesa = despesa[despesa["data"].isin(datas_ano["data"])]
    despesa_parcelada = despesa[(despesa["data"].dt.day == fatura.day) & (despesa["descricao"].str.contains("/"))]
    receita = receita[receita["data"].isin(datas_ano["data"])]

    kpis["investimento"]["Ganho total"] = (f'R${round(sum(receita[receita["aplicacao"]!="nan"]["valor"]), 2)}', "blue")

    kpis["anuais"]["Ganho total"] = (f'R${round(sum(receita["valor"]), 2)}', "blue")
    kpis["anuais"]["Gasto total"] = (f'R${round(sum(despesa["valor"]), 2)}', "red")
    kpis["anuais"]["Saldo final"] = (f'R${round(sum(receita["valor"]) - sum(despesa["valor"]), 2)}', "green")
    kpis["anuais"]["Total parcelado"] = (f'R${round(sum(despesa_parcelada["valor"]), 2)}', "orange")

    despesa = despesa[despesa["data"].isin(datas_mes["data"])]
    despesa_optativa = despesa[despesa["tipo"]=="optativo"]
    receita = receita[receita["data"].isin(datas_mes["data"])]

    kpis["mensais"]["Ganho total"] = (f'R${round(sum(receita["valor"]), 2)}', "blue")
    kpis["mensais"]["Gasto total"] = (f'R${round(sum(despesa["valor"]), 2)}', "red")
    kpis["mensais"]["Saldo final"] = (f'R${round(sum(receita["valor"]) - sum(despesa["valor"]), 2)}', "green")
    kpis["mensais"]["Gasto optativo"] = (f'{round((sum(despesa_optativa["valor"]) / sum(despesa["valor"]))*100, 2)}%', "orange")

    kpis["gympass"]["Total de aulas"] = (f'{sum(gympass["usos"])}', "orange")
    kpis["gympass"]["Mais barato"] = (f'R${round(maior_uso["custo_por_aula"].iloc[0], 2)}/check-in ({maior_uso["usos"].iloc[0]} usos)', "green")
    kpis["gympass"]["Mais caro"] = (f'R${round(menor_uso["custo_por_aula"].iloc[0], 2)}/check-in ({menor_uso["usos"].iloc[0]} usos)', "red")

    return kpis

def colore_valor(val):
    color = 'red' if val[0]=="-" else 'blue'
    return f'color: {color}'

def agrega_saldo_por_dia(despesa, receita, fatura):
    datas=gera_datas_do_mes(fatura)

    despesa = despesa[despesa["data"].isin(datas["data"])].groupby("data").agg({"valor":"sum"}).reset_index()
    receita = receita[receita["data"].isin(datas["data"])].groupby("data").agg({"valor":"sum"}).reset_index()

    despesa["despesa"] = despesa["valor"].cumsum()
    receita["receita"] = receita["valor"].cumsum()

    saldo = datas.merge(receita[["data", "receita"]], on="data", how="left").merge(despesa[["data", "despesa"]], on="data", how="left")
    saldo["saldo"] = saldo["receita"].fillna(method='ffill').fillna(0)-saldo["despesa"].fillna(method='ffill').fillna(0)

    proximo_saldo = saldo[["data", "saldo"]].rename(columns={"saldo": "proximo_saldo"})
    proximo_saldo["data"] = pd.to_datetime(proximo_saldo["data"].dt.date + relativedelta(days=-1))
    saldo = saldo.merge(proximo_saldo, on="data", how="left")

    saldo["positivos"] = np.where((saldo["saldo"] > 0) | (saldo["proximo_saldo"] > 0), saldo["saldo"], np.nan)
    saldo["negativos"] = np.where((saldo["saldo"] < 0) | (saldo["proximo_saldo"] < 0), saldo["saldo"], np.nan)

    return saldo

def agrega_tipos_de_despesa(despesa, fatura):
    datas=gera_datas_do_mes(fatura, ("tipo", despesa["tipo"].dropna().unique()))

    despesa = despesa[despesa["data"].isin(datas["data"])].groupby(["data", "tipo"]).agg({"valor":"sum"}).reset_index()

    despesa = datas.merge(despesa, on=["data", "tipo"], how="left")

    despesa["valor"] = despesa["valor"].fillna(0)

    return despesa

def agrega_usos_gympass_no_mes(gympass, fatura):
    return gympass[(gympass["data"].dt.month == fatura.month) & (gympass["data"].dt.year == fatura.year)].groupby(["unidade", "atividade"]).agg({"data":"count"}).reset_index().rename(columns={"data": "usos"})

def agrega_custo_gympass_por_mes(despesa, gympass, fatura, media_movel):
    custo_gympass = despesa[despesa["descricao"] == "Gympass"][["data", "valor"]]
    custo_gympass["ano"] = custo_gympass["data"].dt.year
    custo_gympass["mes"] = custo_gympass["data"].dt.month
    custo_gympass = custo_gympass.drop(columns=["data"]).drop_duplicates()

    gympass["ano"] = gympass["data"].dt.year
    gympass["mes"] = gympass["data"].dt.month
    gympass = gympass.drop(columns=["data"])
    gympass = gympass[gympass["ano"] == fatura.year].groupby(["ano", "mes"]).agg({"atividade":"count"}).reset_index().rename(columns={"atividade":"usos"}).merge(custo_gympass, on=["ano", "mes"])
    gympass["custo_por_aula"] = gympass["valor"]/gympass["usos"]
    gympass["usos_movel"] = gympass["usos"]
    gympass["valor_movel"] = gympass["valor"]

    for movimento in range(1, media_movel+1):
        gympass_movel = gympass.copy()[["mes", "usos", "valor"]].rename(columns={"usos":"usos_movel_var", "valor":"valor_movel_var"})
        gympass_movel["mes"] += movimento
        gympass = gympass.merge(gympass_movel, on="mes", how="left")
        gympass["usos_movel"] += gympass["usos_movel_var"]
        gympass["valor_movel"] += gympass["valor_movel_var"]
        gympass = gympass.drop(columns=["usos_movel_var", "valor_movel_var"])

    gympass["data"] = np.vectorize(date)(gympass["ano"], gympass["mes"], 1)
    gympass["custo_por_aula_movel"] = gympass["valor_movel"] / gympass["usos_movel"]
    
    return gympass

def agrega_saldo_por_mes(despesa, receita, fatura):
    datas = gera_datas_do_ano(fatura)

    despesa = despesa.merge(datas, on="data")
    receita = receita.merge(datas, on="data")

    despesa = despesa[despesa["ano"] == fatura.year].groupby(["ano", "mes"]).agg({"valor":"sum"}).rename(columns={"valor":"despesa"}).reset_index()
    receita = receita[receita["ano"] == fatura.year].groupby(["ano", "mes"]).agg({"valor":"sum"}).rename(columns={"valor":"receita"}).reset_index()

    saldo = despesa.merge(receita, on=["ano", "mes"], how="left").fillna(0)

    saldo["data"] = pd.to_datetime(np.vectorize(date)(saldo["ano"], saldo["mes"], 1))
    saldo["saldo"] = saldo["receita"] - saldo["despesa"]

    return saldo

def agrega_despesa_parceladas(despesa, fatura):
    datas = gera_datas_do_ano(fatura)
    datas = datas[datas["data"].dt.day == fatura.day]

    return despesa[(despesa["data"].isin(datas["data"])) & (despesa["descricao"].str.contains("/"))].groupby("data").agg({"valor":"sum"}).reset_index()

def agrega_rendimentos_por_mes(receita, fatura):
    datas = gera_datas_do_ano(fatura)

    return receita[receita["aplicacao"]!="nan"].merge(datas, on="data")

def agrega_rendimentos_por_mes_pctg(aplicacoes, receita, fatura):
    datas = gera_datas_do_ano(fatura)

    receita = receita[receita["aplicacao"]!="nan"].merge(datas, on="data")
    investimento_acumulado = receita[["aplicacao", "data", "valor"]].groupby(["aplicacao", "data"]).sum().groupby(level=[0]).cumsum().reset_index()
    investimento_acumulado["data"] = pd.to_datetime(investimento_acumulado["data"].dt.date + relativedelta(months=1))
    investimento_acumulado = investimento_acumulado.rename(columns={"valor": "base"})

    investimento = receita.merge(investimento_acumulado, on = ["data", "aplicacao"],how="left").merge(aplicacoes.groupby("aplicacao").agg({"valor_inicial":"sum"}), on="aplicacao")
    investimento["base"]  = investimento["base"].fillna(0)+investimento["valor_inicial"]
    investimento["pctg"] = investimento["valor"]/investimento["base"]

    return investimento

def agrega_rendimentos(aplicacoes, receita):
    aplicacoes = receita[receita["aplicacao"]!="nan"].groupby("aplicacao").agg({"valor":"sum"}).reset_index().merge(aplicacoes.groupby("aplicacao").agg({"data":"min", "valor_inicial":"sum"}), on="aplicacao")[["aplicacao", "valor", "valor_inicial"]].rename(columns={"valor":"ganho"}).melt(id_vars=["aplicacao"], value_vars=["valor_inicial", "ganho"], var_name="tipo", value_name="valor").replace({"ganho": "Rendimento", "valor_inicial":"Aporte"})
    aplicacoes["order"] = np.where(aplicacoes["tipo"]=="Aporte", 0, 1)
    aplicacoes = aplicacoes.merge(aplicacoes.groupby("aplicacao").agg({"valor":"sum"}).rename(columns={"valor": "total"}), on="aplicacao")
    aplicacoes["y"] = np.where(aplicacoes["tipo"]=="Aporte", aplicacoes["valor"] / 2, aplicacoes["total"] + 2000)
    aplicacoes["percent"] = 100*aplicacoes["valor"]/aplicacoes["total"]
    aplicacoes["texto"] = "R$" + aplicacoes["valor"].round(2).astype(str)
    aplicacoes["texto"] = np.where(aplicacoes["tipo"]=="Aporte", aplicacoes["texto"], aplicacoes["texto"]+" ("+aplicacoes["percent"].round(2).astype(str)+"%)")

    return aplicacoes

def agrega_custo_das_viagens(despesa, viagem, fatura):
    viagem["dias"] = (viagem["data_de_volta"] - viagem["data_de_ida"]).dt.days + 1
    viagem["ano"] = viagem["data_de_ida"].dt.year
    
    viagens = viagem[viagem["ano"] == fatura.year].merge(despesa.groupby("grupo").agg({"valor":"sum"}).reset_index(), left_on="viagem", right_on="grupo")
    viagens["custo"] = viagens["valor"] / (viagens["numero_de_pessoas"] * viagens["dias"])

    viagens["texto"] = "R$" + viagens["custo"].round(2).astype(str)
    viagens["y"] = viagens["custo"] / 2
    
    return viagens

def agrega_custo_dos_grupos(despesa, validacao, fatura):
    grupos = despesa[(despesa["data"].dt.year == fatura.year) & (despesa["grupo"].isin(validacao["grupo"])) & (despesa["grupo"] != "nan")].groupby("grupo").agg({"valor":"sum"}).reset_index()

    grupos["texto"] = "R$" + grupos["valor"].round(2).astype(str)
    grupos["y"] = grupos["valor"] / 2

    return grupos


def agrega_fluxo_saldo(despesa, receita, fatura):
    datas=gera_datas_do_mes(fatura)

    despesa = despesa[despesa["data"].isin(datas["data"])].reset_index()[["data", "descricao", "valor", "tipo"]]
    receita = receita[receita["data"].isin(datas["data"])].reset_index()[["data", "descricao", "valor"]]

    receita["tipo"] = ""
    despesa["valor"] = -despesa["valor"]

    fluxo = pd.concat([despesa, receita]).reset_index().sort_values("data", kind = "stable")

    fluxo["data"] = fluxo["data"].dt.strftime("%d/%m/%Y")
    fluxo["valor"] = fluxo["valor"].apply(lambda val: 'R${:.2f}'.format(val) if val>0 else '-R${:.2f}'.format(-val))

    return fluxo.rename(columns={"data":"Data", "descricao":"Descrição", "valor":"Valor", "tipo":"tipo"}).style.applymap(colore_valor, subset=['Valor'])

def agrega_fluxo_gympass(gympass, fatura):
    gympass = gympass[(gympass["data"].dt.month == fatura.month) & (gympass["data"].dt.year == fatura.year)][["data", "atividade", "unidade"]]

    gympass["data"]=gympass["data"].dt.strftime("%d/%m/%Y")

    return gympass.rename(columns={"data":"Data", "atividade":"Atividade", "unidade":"Unidade"})

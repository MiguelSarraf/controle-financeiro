import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from dateutil.relativedelta import relativedelta

from dados import *

def mostra_kpis(kpis, grupo):
    cols = st.columns(len(kpis[grupo]))

    for col, kpi in zip(cols, kpis[grupo]):
        col.subheader(f"{kpi}: {kpis[grupo][kpi][0]}", divider=kpis[grupo][kpi][1])

#endregion

#region Resultados mensais

def saldo_por_dia(despesa, receita, fatura, height):
    saldo = agrega_saldo_por_dia(despesa, receita, fatura)
    if saldo.empty: return None
    
    hoje = gera_hoje(saldo)

    grafico = alt.Chart(saldo)
    grafico = grafico.mark_line(color="blue").encode(
        x=alt.X("data:T", axis=alt.Axis(title=None,format="%d/%b")),
        y=alt.Y("positivos:Q", axis=alt.Axis(title=None, format="$.2f")),
        tooltip=[alt.Tooltip("saldo:Q", format="$,.2f", title="Valor acumulado"), alt.Tooltip("data:T", format="%d/%m/%Y", title="Data")]
    )+grafico.mark_line(color="red").encode(
        x="data:T",
        y="negativos:Q",
        tooltip=[alt.Tooltip("saldo:Q", format="$,.2f", title="Valor acumulado"), alt.Tooltip("data:T", format="%d/%m/%Y", title="Data")]
    )+alt.Chart(hoje).mark_rule(color="orange", strokeWidth=1.5, strokeDash=[10.10]).encode(
        x="data:T",
        tooltip=[alt.Tooltip("data:T", format="%d/%m/%Y", title="Hoje")]
    )
    
    if height:
        grafico=grafico.properties(
            title="Saldo",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Saldo"
        )

    return grafico.configure_title(fontSize=24)

def tipos_de_despesa(despesa, fatura, height):
    despesa = agrega_tipos_de_despesa(despesa, fatura)
    if despesa.empty: return None

    ordem=['optativo', 'social', 'obrigatório']

    grafico = alt.Chart(despesa).transform_calculate(
        order=f"-indexof({ordem}, datum.tipo)"
    )
    grafico = grafico.mark_area().encode(
        x=alt.X("data:T", axis=alt.Axis(title=None,format="%d/%b")),
        y=alt.Y("valor:Q", axis=alt.Axis(title=None, format="$.2f")),
        color=alt.Color("tipo:N", legend=alt.Legend(orient="top"), scale=alt.Scale(domain=['optativo', 'obrigatório', 'social'], range=["#34a853b0", "#c53929b0", "#ff9900b0"]), sort=ordem),
        order="order:O",
        tooltip=[alt.Tooltip("valor:Q", format="$,.2f", title="Gasto"), alt.Tooltip("data:T", format="%d/%m/%Y", title="Data"), alt.Tooltip("tipo:N", title="Tipo")]
    )
    
    if height:
        grafico=grafico.properties(
            title="Tipos de despesa",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Tipos de despesa"
        )

    return grafico.configure_title(fontSize=24)

#endregion

#region Gympass

def usos_gympass_no_mes(gympass, fatura, height):
    gympass = agrega_usos_gympass_no_mes(gympass, fatura)
    if gympass.empty: return None

    grafico = alt.Chart(gympass)

    grafico = grafico.mark_bar(size=30).encode(
        y=alt.Y("unidade:N", axis=alt.Axis(title=None)),
        x=alt.X("usos:Q", axis=alt.Axis(title=None, orient="top", tickCount=gympass["usos"].max())),
        color=alt.Color("atividade:N", legend=alt.Legend(title="", orient="bottom"), scale=alt.Scale(scheme="category10")),
        yOffset="unidade:N",
        tooltip=alt.value(None)
    )
    
    if height:
        grafico=grafico.properties(
            title="Usos no mês",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Usos no mês"
        )

    return grafico.configure_title(fontSize=24)

def custo_gympass_por_mes(despesa, gympass, fatura, media_movel, height):
    gympass = agrega_custo_gympass_por_mes(despesa, gympass, fatura, media_movel)
    if gympass.empty: return None

    grafico = alt.Chart(gympass)

    grafico = grafico.mark_line(color="blue").encode(
        x=alt.X("data:T", axis=alt.Axis(title=None, format="%b")),
        y=alt.Y("custo_por_aula:Q", axis=alt.Axis(title=None, format="$.2f")),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("usos:Q", format=".0f", title="Check-ins"), alt.Tooltip("custo_por_aula:Q", format="$.2f", title="Custo do check-in"), alt.Tooltip("custo_por_aula_movel:Q", format="$.2f", title="Custo do check-in (móvel)")]
    ) + grafico.mark_line(color="lightblue").encode(
        x=alt.X("data:T", axis=alt.Axis(title=None, format="%b")),
        y=alt.Y("custo_por_aula_movel:Q", axis=alt.Axis(title=None, format="$.2f")),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("usos:Q", format=".0f", title="Check-ins"), alt.Tooltip("custo_por_aula:Q", format="$.2f", title="Custo do check-in"), alt.Tooltip("custo_por_aula_movel:Q", format="$.2f", title="Custo do check-in (móvel)")]
    ) + grafico.mark_rule(color="red", strokeDash=[10.10]).encode(
        y=alt.Y("max(custo_por_aula):Q"),
        tooltip=[alt.Tooltip("max(custo_por_aula):Q", title="Check-in mais caro")]
    ) + grafico.mark_rule(color="green", strokeDash=[10.10]).encode(
        y=alt.Y("min(custo_por_aula):Q"),
        tooltip=[alt.Tooltip("min(custo_por_aula):Q", title="Check-in mais barato")]
    )
    
    if height:
        grafico=grafico.properties(
            title="Custo do check-in",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Custo do check-in"
        )

    return grafico.configure_title(fontSize=24)

#endregion

#region Resultados anuais

def saldo_por_mes(despesa, receita, fatura, height):
    saldo = agrega_saldo_por_mes(despesa, receita, fatura)
    if saldo.empty: return None

    grafico=alt.Chart(saldo)

    grafico=grafico.mark_bar(color="#08c43ab2", size=height/20 if height else None).encode(
        x=alt.X("data:T", axis=alt.Axis(title=None, format="%b", labelAngle=0)),
        y=alt.Y("saldo:Q", axis=alt.Axis(title=None, format="$.2f")),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("receita:Q", format="$.2f", title="Receita"), alt.Tooltip("despesa:Q", format="$.2f", title="Despesa"), alt.Tooltip("saldo:Q", format="$.2f", title="Líquido")]
    )+grafico.mark_line(color="red").encode(
        x=alt.X("data:T", axis=alt.Axis(title=None)),
        y=alt.Y("despesa:Q", axis=alt.Axis(title=None)),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("receita:Q", format="$.2f", title="Receita"), alt.Tooltip("despesa:Q", format="$.2f", title="Despesa"), alt.Tooltip("saldo:Q", format="$.2f", title="Líquido")]
    )+grafico.mark_line(color="blue").encode(
        x=alt.X("data:T", axis=alt.Axis(title=None)),
        y=alt.Y("receita:Q", axis=alt.Axis(title=None)),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("receita:Q", format="$.2f", title="Receita"), alt.Tooltip("despesa:Q", format="$.2f", title="Despesa"), alt.Tooltip("saldo:Q", format="$.2f", title="Líquido")]
    )
    
    if height:
        grafico=grafico.properties(
            title="Saldo",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Saldo"
        )
    
    return grafico.configure_title(fontSize=24)

def despesa_parceladas(despesa, fatura, height):
    parcelas = agrega_despesa_parceladas(despesa, fatura)
    if parcelas.empty: return None

    grafico = alt.Chart(parcelas)

    grafico = grafico.mark_line().encode(
        x=alt.X("data:T", axis=alt.Axis(title=None, format="%b")),
        y=alt.Y("valor:Q", axis=alt.Axis(title=None, format="$.2f")),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("valor:Q", format="$.2f", title="Valor parcelado")]
    )
    
    if height:
        grafico=grafico.properties(
            title="Despesas parceladas",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Despesas parceladas"
        )
    
    return grafico.configure_title(fontSize=24)

#endregion

#region Investimentos

def rendimentos_por_mes(receita, fatura, height):
    rendimentos_mes = agrega_rendimentos_por_mes(receita, fatura)

    grafico = alt.Chart(rendimentos_mes)

    grafico=grafico.mark_line().encode(
        x=alt.X("data:T", axis=alt.Axis(title=None, format="%b", labelAngle=0)),
        y=alt.Y("valor:Q", axis=alt.Axis(title=None, format="$.2f")),
        color=alt.Color("aplicacao:N", legend=alt.Legend(title="Aplicação", orient="bottom")),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("aplicacao:N", title="Aplicação"), alt.Tooltip("valor:Q", format="$.2f", title="Ganho")]
    )
    
    if height:
        grafico=grafico.properties(
            title="Ganhos em investimento por mês",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Ganhos em investimento por mês"
        )
    
    return grafico.configure_title(fontSize=24)

def rendimentos_por_mes_pctg(aplicacoes, receita, fatura, height):
    rendimentos_mes = agrega_rendimentos_por_mes_pctg(aplicacoes, receita, fatura)

    grafico = alt.Chart(rendimentos_mes)

    grafico=grafico.mark_line().encode(
        x=alt.X("data:T", axis=alt.Axis(title=None, format="%b", labelAngle=0)),
        y=alt.Y("pctg:Q", axis=alt.Axis(title=None, format=".2%")),
        color=alt.Color("aplicacao:N", legend=alt.Legend(title="Aplicação", orient="bottom")),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("aplicacao:N", title="Aplicação"), alt.Tooltip("valor:Q", format="$.2f", title="Ganho"), alt.Tooltip("pctg:Q", format=".2%", title="Rendimento")]
    )

    if height:
        grafico=grafico.properties(
            title="Ganhos em investimento por mês (%)",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Ganhos em investimento por mês (%)"
        )
    
    return grafico.configure_title(fontSize=24)

def rendimentos(receita, aplicacoes, height):
    aplicacoes = agrega_rendimentos(aplicacoes, receita)

    grafico_base = alt.Chart(aplicacoes)

    grafico = grafico_base.mark_bar(size=height/4 if height else None).encode(
        x=alt.X("aplicacao:N", axis=alt.Axis(title=None, labelAngle=0)),
        y=alt.Y("sum(valor):Q", axis=alt.Axis(title=None)),
        color=alt.Color("tipo:N", legend=None),
        order=alt.Order("order:Q"),
        tooltip=[alt.Tooltip("aplicacao:N", title="Aplicação"), alt.Tooltip("valor:Q", title="Custo")]
    )

    if height:
        grafico+= grafico_base.mark_text(size=height/20, color="black").encode(
            x=alt.X("aplicacao:N", axis=alt.Axis(title=None, labelAngle=0)),
            y=alt.Y("y:Q", axis=alt.Axis(title=None)),
            order=alt.Order("order:Q"),
            text="texto",
            tooltip=alt.value(None)
        )
    else:
        grafico+= grafico_base.mark_text(color="black").encode(
            x=alt.X("aplicacao:N", axis=alt.Axis(title=None, labelAngle=0)),
            y=alt.Y("y:Q", axis=alt.Axis(title=None)),
            order=alt.Order("order:Q"),
            text="texto",
            tooltip=alt.value(None)
        )

    if height:
        grafico=grafico.properties(
            title="Ganho por aplicação",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Ganho por aplicação"
        )

    return grafico.configure_title(fontSize=24)

#endregion

#region Outros resultados

def custo_das_viagens(despesa, viagem, fatura, height):
    custo_viagem = agrega_custo_das_viagens(despesa, viagem, fatura)
    if custo_viagem.empty: return None

    grafico= alt.Chart(custo_viagem)

    grafico=grafico.mark_bar(size=height/4 if height else None).encode(
        x=alt.X("viagem:N", axis=alt.Axis(title=None, labelAngle=0)),
        y=alt.Y("custo:Q", axis=alt.Axis(title=None)),
        tooltip=[alt.Tooltip("data_de_ida:T", format="%d/%m/%Y", title="Ida"), alt.Tooltip("data_de_volta:T", format="%d/%m/%Y", title="Volta"), alt.Tooltip("dias:Q", format=".0f", title="Dias"), alt.Tooltip("numero_de_pessoas:Q", format=".0f", title="Pessoas")]
    )

    if height:
        grafico+= grafico.mark_text(size=height/20, color="white").encode(
            x=alt.X("viagem:N", axis=alt.Axis(title=None, labelAngle=0)),
            y=alt.Y("y:Q", axis=alt.Axis(title=None)),
            text="texto",
            tooltip=alt.value(None)
        )
    else:
        grafico+= grafico.mark_text(color="white").encode(
            x=alt.X("viagem:N", axis=alt.Axis(title=None, labelAngle=0)),
            y=alt.Y("y:Q", axis=alt.Axis(title=None)),
            text="texto",
            tooltip=alt.value(None)
        )
    
    if height:
        grafico=grafico.properties(
            title="Custo da viagem por dia por pessoa",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Custo da viagem por dia por pessoa"
        )
    
    return grafico.configure_title(fontSize=24)

def custo_dos_grupos(despesa, validacao, fatura, height):
    grupos = agrega_custo_dos_grupos(despesa, validacao, fatura)
    if grupos.empty: return None

    grafico= alt.Chart(grupos)

    grafico=grafico.mark_bar(size=height/4 if height else None).encode(
        x=alt.X("grupo:N", axis=alt.Axis(title=None, labelAngle=0)),
        y=alt.Y("valor:Q", axis=alt.Axis(title=None)),
        tooltip=[alt.Tooltip("grupo:N", title="Grupo"), alt.Tooltip("valor:Q", title="Custo")]
    )

    if height:
        grafico+= grafico.mark_text(size=height/20, color="white").encode(
            x=alt.X("grupo:N", axis=alt.Axis(title=None, labelAngle=0)),
            y=alt.Y("y:Q", axis=alt.Axis(title=None)),
            text="texto",
            tooltip=alt.value(None)
        )
    else:
        grafico+= grafico.mark_text(color="white").encode(
            x=alt.X("grupo:N", axis=alt.Axis(title=None, labelAngle=0)),
            y=alt.Y("y:Q", axis=alt.Axis(title=None)),
            text="texto",
            tooltip=alt.value(None)
        )

    if height:
        grafico=grafico.properties(
            title="Gasto por grupo",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Gasto por grupo"
        )

    return grafico.configure_title(fontSize=24)

#endregion

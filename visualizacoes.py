import pandas as pd
import altair as alt
from dateutil.relativedelta import relativedelta

def gera_visu_evolucao_diaria(dados, height):
    positivos=dados[dados["valor"]>=0]["data"].to_list()
    novos=[]
    for data in positivos:
        if not data-relativedelta(days=1) in positivos:
            novos.append(data-relativedelta(days=1))
    positivos+=novos
    negativos=dados[dados["valor"]<0]["data"].to_list()
    novos=[]
    for data in negativos:
        if not data-relativedelta(days=1) in negativos:
            novos.append(data-relativedelta(days=1))
    negativos+=novos
    
    positivos=dados[dados["data"].isin(positivos)]
    negativos=dados[dados["data"].isin(negativos)]
    
    positivos=dados[["data"]].merge(positivos, on="data", how="left")
    negativos=dados[["data"]].merge(negativos, on="data", how="left")
    
    hoje=pd.DataFrame(index=[0])
    hoje["data"]=pd.Timestamp.today()
    hoje["data"]=hoje["data"].dt.date
    hoje=hoje[hoje["data"].isin(dados["data"])]
    
    resultado_final=pd.DataFrame({"texto":[f"Saldo final:\nR${dados['valor'].iloc[-1].round(2)}"], "x":[positivos["data"].max()], "y":[positivos["valor"].max()]})
    
    grafico= alt.Chart(positivos).mark_line(color="blue").encode(
        x=alt.X("data:T", axis=alt.Axis(title=None,format="%d/%b")),
        y=alt.Y("valor:Q", axis=alt.Axis(title=None, format="$.2f")),
        tooltip=[alt.Tooltip("valor:Q", format="$,.2f", title="Valor acumulado"), alt.Tooltip("data:T", format="%d/%m/%Y", title="Data")]
    )+alt.Chart(negativos).mark_line(color="red").encode(
        x="data:T",
        y="valor:Q",
        tooltip=[alt.Tooltip("valor:Q", format="$,.2f", title="Valor acumulado"), alt.Tooltip("data:T", format="%d/%m/%Y", title="Data")]
    )+alt.Chart(hoje).mark_rule(color="orange", strokeWidth=1.5, strokeDash=[10.10]).encode(
        x="data:T",
        tooltip=[alt.Tooltip("data:T", format="%d/%m/%Y", title="Hoje")]
    )+alt.Chart(resultado_final).mark_text(lineBreak='\n', size=20, xOffset=-70).encode(
        text="texto:N",
        x="x",
        y="y",
        tooltip=alt.value(None)
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

def gera_visu_tipo_diaria(dados, height):
    dados=dados.fillna({"tipo":"optativo", "valor":0})
    ordem=['optativo', 'social', 'obrigatório']
    grafico= alt.Chart(dados).transform_calculate(
        order=f"-indexof({ordem}, datum.tipo)"
    ).mark_area().encode(
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

def gera_visu_gympass_usos(dados, height):
    grafico=alt.Chart(dados).mark_bar(size=20).encode(
        x=alt.X("num_usos:Q", axis=alt.Axis(title=None, orient="top", tickCount=dados["num_usos"].max())),
        yOffset="unidade:N",
        y=alt.Y("unidade:N", axis=alt.Axis(title=None)),
        color=alt.Color("atividade:N", legend=alt.Legend(title="", orient="bottom"), scale=alt.Scale(scheme="category10")),
        tooltip=alt.value(None)
    )
    
    if height:
        grafico=grafico.properties(
            title="Usos do mês",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Usos do mês"
        )
    
    return grafico.configure_title(fontSize=24)

def gera_visu_gympass_mes(dados, media_movel, height):
    gympass_mes_movel=dados[["ano", "mes", "num_usos", "valor"]].set_index(["ano", "mes"]).sort_index().rolling(media_movel).sum().reset_index()
    gympass_mes_movel["custo_uso_movel"]=(gympass_mes_movel["valor"]/gympass_mes_movel["num_usos"]).round(2)
    dados=dados.merge(gympass_mes_movel[["ano", "mes", "custo_uso_movel"]], on=["ano", "mes"], how="inner")
    
    dados["data"]=pd.to_datetime(dados["ano"].astype(str)+dados["mes"].astype(str).str.zfill(2), format="%Y%m")
    
    valor_minimo=dados["custo_uso"].min()
    valor_maximo=dados["custo_uso"].max()
    min_max=pd.concat([dados[dados["custo_uso"]==valor_minimo].head(1), dados[dados["custo_uso"]==valor_maximo].head(1)])
    min_max["eh_maximo"]=min_max["custo_uso"]==valor_maximo
    min_max["texto"]="R$"+min_max["custo_uso"].astype(str)
    grafico=alt.Chart(dados).mark_line(color="blue").encode(
        x=alt.X("data:T", axis=alt.Axis(title=None, format="%b")),
        y=alt.Y("custo_uso:Q", axis=alt.Axis(title=None, format="$.2f")),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("num_usos:Q", format=".0f", title="Check-ins"), alt.Tooltip("custo_uso:Q", format="$.2f", title="Custo do check-in"), alt.Tooltip("custo_uso_movel:Q", format="$.2f", title="Custo do check-in (móvel)")]
    )+alt.Chart(dados).mark_line(color="lightblue").encode(
        x=alt.X("data:T", axis=alt.Axis(title=None)),
        y=alt.Y("custo_uso_movel:Q", axis=alt.Axis(title=None)),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("num_usos:Q", format=".0f", title="Check-ins"), alt.Tooltip("custo_uso:Q", format="$.2f", title="Custo do check-in"), alt.Tooltip("custo_uso_movel:Q", format="$.2f", title="Custo do check-in (móvel)")]
    )+alt.Chart(min_max).mark_text(size=20, yOffset=20, xOffset=20).encode(
        x="data:T",
        y="custo_uso:Q",
        text="texto",
        color=alt.Color("eh_maximo:N", legend=None, scale=alt.Scale(domain=[True, False], range=["red", "green"])),
        tooltip=alt.value(None)
    )
    
    if height:
        grafico=grafico.properties(
            title="Custo mensal da aula",
            height=height
        )
    else:
        grafico=grafico.properties(
            title="Custo mensal da aula"
        )
    
    return grafico.configure_title(fontSize=24)

def gera_visu_anual(dados, height):
    resultado_final=pd.DataFrame({"texto":[f"Saldo final:\nR${dados['liquido'].sum().round(2)}"], "x":[dados["data"].max()], "y":[dados["receita"].max()]})
    
    if height:
        grafico=alt.Chart(dados).mark_bar(color="#08c43ab2", size=height/20)
    else:
        grafico=alt.Chart(dados).mark_bar(color="#08c43ab2")

    grafico=grafico.encode(
        x=alt.X("data:T", axis=alt.Axis(title=None, format="%b", labelAngle=0)),
        y=alt.Y("liquido:Q", axis=alt.Axis(title=None, format="$.2f")),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("receita:Q", format="$.2f", title="Receita"), alt.Tooltip("despesa:Q", format="$.2f", title="Despesa"), alt.Tooltip("liquido:Q", format="$.2f", title="Líquido")]
    )+alt.Chart(dados).mark_line(color="red").encode(
        x=alt.X("data:T", axis=alt.Axis(title=None)),
        y=alt.Y("despesa:Q", axis=alt.Axis(title=None)),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("receita:Q", format="$.2f", title="Receita"), alt.Tooltip("despesa:Q", format="$.2f", title="Despesa"), alt.Tooltip("liquido:Q", format="$.2f", title="Líquido")]
    )+alt.Chart(dados).mark_line(color="blue").encode(
        x=alt.X("data:T", axis=alt.Axis(title=None)),
        y=alt.Y("receita:Q", axis=alt.Axis(title=None)),
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("receita:Q", format="$.2f", title="Receita"), alt.Tooltip("despesa:Q", format="$.2f", title="Despesa"), alt.Tooltip("liquido:Q", format="$.2f", title="Líquido")]
    )+alt.Chart(resultado_final).mark_text(lineBreak='\n', size=20, xOffset=-20, yOffset=-20).encode(
        text="texto:N",
        x=alt.X("x:O", axis=alt.Axis(title=None)),
        y=alt.Y("y:Q", axis=alt.Axis(title=None)),
        tooltip=alt.value(None)
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

def gera_visu_tipo_anual(dados, height):
    ordem=['optativo', 'social', 'obrigatório']

    if height:
        grafico= alt.Chart(dados).transform_calculate(
            order=f"-indexof({ordem}, datum.tipo)"
        ).mark_bar(size=height/20)
    else:
        grafico= alt.Chart(dados).transform_calculate(
            order=f"-indexof({ordem}, datum.tipo)"
        ).mark_bar()
    grafico=grafico.encode(
        x=alt.X("data:T", axis=alt.Axis(title=None, format="%b")),
        y=alt.Y("valor:Q", axis=alt.Axis(title=None, format="$.2f")),
        color=alt.Color("tipo:N", legend=alt.Legend(orient="top"), scale=alt.Scale(domain=['optativo', 'obrigatório', 'social'], range=["#34a853", "#c53929", "#ff9900"]), sort=ordem),
        order="order:O",
        tooltip=[alt.Tooltip("data:T", format="%b/%Y", title="Mês"), alt.Tooltip("valor:Q", format="$.2f", title="Valor"), alt.Tooltip("tipo:N", title="Tipo"), alt.Tooltip("porcentagem:Q", format=".1%", title="Porcentagem")]
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

def gera_visu_viagens(dados, height):
    dados["texto"]="R$"+dados["custo"].astype(str)
    dados["y"]=dados["custo"]/2

    if height:
        grafico= alt.Chart(dados).mark_bar(size=height/4)
    else:
        grafico= alt.Chart(dados).mark_bar()
    grafico=grafico.encode(
        x=alt.X("viagem:N", axis=alt.Axis(title=None, labelAngle=0)),
        y=alt.Y("custo:Q", axis=alt.Axis(title=None)),
        tooltip=[alt.Tooltip("data_de_ida:T", format="%d/%m/%Y", title="Ida"), alt.Tooltip("data_de_volta:T", format="%d/%m/%Y", title="Volta"), alt.Tooltip("dias:Q", format=".0f", title="Dias"), alt.Tooltip("numero_de_pessoas:Q", format=".0f", title="Pessoas")]
    )

    if height:
        grafico+= alt.Chart(dados).mark_text(size=height/20, color="white").encode(
            x=alt.X("viagem:N", axis=alt.Axis(title=None, labelAngle=0)),
            y=alt.Y("y:Q", axis=alt.Axis(title=None)),
            text="texto",
            tooltip=alt.value(None)
        )
    else:
        grafico+= alt.Chart(dados).mark_text(color="white").encode(
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

def gera_visu_parceladas(dados, height):
    grafico= alt.Chart(dados).mark_line().encode(
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

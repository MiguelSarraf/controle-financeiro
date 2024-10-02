import pandas as pd

schemas={
    "validacao":{
        "Tipo de despesa":"str",
        "Tipo de transação de despesa":"str",
        "Tipo de transação de receita":"str",
        "Conta":"str",
        "Atividade no gympass":"str",
        "Unidade do Gympass":"str",
        "Viagem":"str",
        "Fechamento da fatura":"Int32"
    },
    "despesa":{
        "Descrição":"str",
        "Valor":"float",
        "Tipo":"str",
        "Transação":"str",
        "Conta":"str",
        "Viagem":"str"
    },
    "receita":{
        "Descrição":"str",
        "Valor":"float",
        "Transação":"str",
        "Conta":"str",
    },
    "gympass":{
        "Atividade":"str",
        "Unidade":"str",
    },
    "viagem":{
        "Viagem":"str",
        "Número de pessoas":"int",
    },
    "gids":{
        "Aba":"str",
        "GID":"str"
    }
}

integridade=(
    ("despesa", "tipo", "tipo_de_despesa"),
    ("despesa", "transacao", "tipo_de_transacao_de_despesa"),
    ("despesa", "conta", "conta"),
    ("despesa", "viagem", "viagem"),
    ("receita", "transacao", "tipo_de_transacao_de_receita"),
    ("receita", "conta", "conta"),
    ("gympass", "atividade", "atividade_no_gympass"),
    ("gympass", "unidade", "unidade_do_gympass"),
    ("viagem", "viagem", "viagem")
)

converters={
    "validacao":{
    },
    "despesa":{
        "Data":pd.to_datetime,
    },
    "receita":{
        "Data":pd.to_datetime,
    },
    "gympass":{
        "Data":pd.to_datetime,
    },
    "viagem":{
        "Data de ida":pd.to_datetime,
        "Data de volta":pd.to_datetime,
    },
}

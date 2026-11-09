"""
Módulo ETL e Estatísticas — Crescimento Populacional Brasileiro.

Execução:
    python etl_estatisticas.py

Entradas:
    dados/populacao_uf_original.csv
    dados/populacao_brasil_historica_original.csv

Saídas:
    dados/populacao_uf_tratada.csv
    dados/populacao_brasil_historica_tratada.csv
    dados/estatisticas_uf_2025.json
    dados/base_ibge_tratada.xlsx

A base estadual corresponde às 27 UFs na estimativa IBGE de 2025,
com data de referência em 1º de julho de 2025.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
PASTA_DADOS = PASTA / "dados"


def carregar_csv(caminho):
    """Lê CSV com codificação compatível com arquivos gerados no Excel."""
    return pd.read_csv(caminho, encoding="utf-8-sig")


def validar_base_uf(df):
    """Verifica colunas, duplicidades e valores populacionais inválidos."""
    obrigatorias = {"UF", "Estado", "Regiao", "Populacao", "Ano"}
    ausentes = obrigatorias - set(df.columns)
    if ausentes:
        raise ValueError(f"Colunas ausentes na base estadual: {sorted(ausentes)}")

    if df["UF"].duplicated().any():
        duplicadas = df.loc[df["UF"].duplicated(), "UF"].tolist()
        raise ValueError(f"Existem UFs duplicadas: {duplicadas}")

    df["Populacao"] = pd.to_numeric(df["Populacao"], errors="coerce")
    if df["Populacao"].isna().any():
        raise ValueError("Há valores populacionais vazios ou não numéricos.")
    if (df["Populacao"] <= 0).any():
        raise ValueError("A população deve ser maior que zero.")
    if len(df) != 27:
        raise ValueError(f"Esperadas 27 UFs; foram encontradas {len(df)}.")

    return df


def calcular_estatisticas(valores):
    """Calcula tendência central, dispersão, quartis e outliers."""
    serie = pd.Series(valores).dropna().astype(float)
    if serie.empty:
        raise ValueError("Não há valores para calcular as estatísticas.")

    q1 = serie.quantile(0.25)
    q2 = serie.quantile(0.50)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr

    moda = serie.mode()
    moda_resultado = None if len(moda) == len(serie) else moda.tolist()

    outliers = serie[
        (serie < limite_inferior) | (serie > limite_superior)
    ]

    return {
        "quantidade_observacoes": int(serie.count()),
        "media": float(serie.mean()),
        "mediana": float(serie.median()),
        "moda": moda_resultado,
        "q1": float(q1),
        "q2": float(q2),
        "q3": float(q3),
        "iqr": float(iqr),
        "amplitude": float(serie.max() - serie.min()),
        "desvio_padrao_populacional": float(serie.std(ddof=0)),
        "minimo": float(serie.min()),
        "maximo": float(serie.max()),
        "limite_inferior_outliers": float(limite_inferior),
        "limite_superior_outliers": float(limite_superior),
        "outliers": [float(x) for x in outliers.tolist()],
        "criterio_outlier": "Valores abaixo de Q1 - 1,5*IQR ou acima de Q3 + 1,5*IQR."
    }


def tratar_historico(df):
    """Padroniza a série nacional e calcula variações entre observações."""
    obrigatorias = {"Ano", "Populacao_Brasil", "Tipo_Levantamento"}
    ausentes = obrigatorias - set(df.columns)
    if ausentes:
        raise ValueError(f"Colunas ausentes na série histórica: {sorted(ausentes)}")

    df["Ano"] = pd.to_numeric(df["Ano"], errors="raise").astype(int)
    df["Populacao_Brasil"] = pd.to_numeric(
        df["Populacao_Brasil"], errors="raise"
    )
    df = df.sort_values("Ano").drop_duplicates("Ano").reset_index(drop=True)
    df["Variacao_Absoluta"] = df["Populacao_Brasil"].diff()
    df["Variacao_Percentual_Periodo"] = (
        df["Populacao_Brasil"].pct_change() * 100
    )
    intervalo = df["Ano"].diff()
    df["Taxa_Anualizada_Pct"] = (
        (df["Populacao_Brasil"] / df["Populacao_Brasil"].shift(1))
        ** (1 / intervalo) - 1
    ) * 100
    return df


def executar_etl():
    """Executa extração, validação, transformação e carga dos resultados."""
    PASTA_DADOS.mkdir(exist_ok=True)

    uf = carregar_csv(PASTA_DADOS / "populacao_uf_original.csv")
    historico = carregar_csv(
        PASTA_DADOS / "populacao_brasil_historica_original.csv"
    )

    uf = validar_base_uf(uf)
    uf["UF"] = uf["UF"].astype(str).str.strip().str.upper()
    uf["Estado"] = uf["Estado"].astype(str).str.strip()
    uf["Regiao"] = uf["Regiao"].astype(str).str.strip()
    uf["Ano"] = pd.to_numeric(uf["Ano"], errors="raise").astype(int)

    total = uf["Populacao"].sum()
    uf["Participacao_Nacional_Pct"] = uf["Populacao"] / total * 100
    uf["Populacao_Milhoes"] = uf["Populacao"] / 1_000_000
    uf = uf.sort_values("Populacao", ascending=False).reset_index(drop=True)
    uf["Posicao_Ranking"] = np.arange(1, len(uf) + 1)

    historico = tratar_historico(historico)
    estatisticas = calcular_estatisticas(uf["Populacao"])

    uf.to_csv(
        PASTA_DADOS / "populacao_uf_tratada.csv",
        index=False, encoding="utf-8-sig"
    )
    historico.to_csv(
        PASTA_DADOS / "populacao_brasil_historica_tratada.csv",
        index=False, encoding="utf-8-sig"
    )
    (PASTA_DADOS / "estatisticas_uf_2025.json").write_text(
        json.dumps(estatisticas, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    with pd.ExcelWriter(
        PASTA_DADOS / "base_ibge_tratada.xlsx", engine="openpyxl"
    ) as writer:
        uf.to_excel(writer, sheet_name="UF_2025", index=False)
        historico.to_excel(writer, sheet_name="Historico_Brasil", index=False)
        pd.DataFrame(
            [{"Metrica": k, "Valor": json.dumps(v, ensure_ascii=False)
              if isinstance(v, (list, dict)) else v}
             for k, v in estatisticas.items()]
        ).to_excel(writer, sheet_name="Estatisticas", index=False)

    print("ETL concluído.")
    print(f"Total das 27 UFs: {total:,.0f}".replace(",", "."))
    print(f"Média estadual: {estatisticas['media']:,.2f}".replace(",", "."))
    print(f"Mediana: {estatisticas['mediana']:,.0f}".replace(",", "."))
    print(f"Outliers identificados: {len(estatisticas['outliers'])}")


if __name__ == "__main__":
    executar_etl()

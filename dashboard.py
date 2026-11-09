import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from etl_estatisticas import calcular_estatisticas

st.set_page_config(page_title="Brasil em Dados", page_icon="🌎", layout="wide")
st.title(" Brasil em Dados")
st.caption("Crescimento e distribuição populacional — IBGE")

pasta = Path(__file__).parent / "dados"
base_path = pasta / "populacao_uf_tratada.csv"
if not base_path.exists():
    st.error("Base tratada não encontrada. Execute primeiro: python etl_estatisticas.py")
    st.stop()

df = pd.read_csv(base_path, encoding="utf-8-sig")
st.sidebar.header("Filtros")
regioes = ["Todas"] + sorted(df["Regiao"].unique().tolist())
regiao = st.sidebar.selectbox("Região", regioes)
ufs = ["Todas"] + sorted(df["UF"].unique().tolist())
uf = st.sidebar.selectbox("UF", ufs)

f = df.copy()
if regiao != "Todas":
    f = f[f["Regiao"] == regiao]
if uf != "Todas":
    f = f[f["UF"] == uf]
if f.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

total = f["Populacao"].sum()
m = calcular_estatisticas(f["Populacao"])
a, b, c, d = st.columns(4)
a.metric("População no recorte", f"{total:,.0f}".replace(",", "."))
b.metric("Média por UF", f"{m['media']:,.0f}".replace(",", "."))
c.metric("Mediana", f"{m['mediana']:,.0f}".replace(",", "."))
d.metric("UFs no recorte", len(f))

fig = px.bar(f.sort_values("Populacao"), x="Populacao", y="Estado",
             orientation="h", color="Regiao",
             title="População por unidade federativa")
st.plotly_chart(fig, use_container_width=True)

fig2 = px.box(f, y="Populacao", points="all",
              title="Dispersão populacional entre as UFs")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Métricas estatísticas")
st.write({
    "Q1": m["q1"], "Q2 (mediana)": m["q2"], "Q3": m["q3"],
    "IQR": m["iqr"], "Amplitude": m["amplitude"],
    "Desvio padrão populacional": m["desvio_padrao_populacional"],
    "Limite inferior": m["limite_inferior_outliers"],
    "Limite superior": m["limite_superior_outliers"]
})
st.dataframe(f, use_container_width=True, hide_index=True)
st.caption("Fonte: IBGE, Estimativas da População 2025. Referência: 1º de julho de 2025.")

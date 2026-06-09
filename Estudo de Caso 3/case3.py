import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# ESTUDO DE CASO 3 - BALANCO DE ENERGIA DO CIRCUITO
# SE S2 = Fonte / Energia Requerida
# SE S3 = Cliente Livre
# SE S4 = Mercado Regulado / Cliente Cativo
# ============================================================

base = Path(".")

arquivos = {
    ("Fev/25", "SE S2"): base / "Dados de Grandezas eletricas Fev25 - SE S2.xlsx",
    ("Fev/25", "SE S3"): base / "Dados de Grandezas eletricas Fev25 - SE S3.xlsx",
    ("Fev/25", "SE S4"): base / "Dados de Grandezas eletricas Fev25 - SE S4.xlsx",
    ("Out/25", "SE S2"): base / "Dados de Grandezas eletricas Out25 - SE S2.xlsx",
    ("Out/25", "SE S3"): base / "Dados de Grandezas eletricas Out25 - SE S3.xlsx",
    ("Out/25", "SE S4"): base / "Dados de Grandezas eletricas Out25 - SE S4.xlsx",
}

def ler_planilha_grandezas(caminho):
    bruto = pd.read_excel(caminho, header=None)

    linha_cabecalho = None
    for i in range(min(25, len(bruto))):
        linha = bruto.iloc[i].astype(str).str.strip().tolist()
        if "Data" in linha and "kWh fornecido" in linha:
            linha_cabecalho = i
            break

    if linha_cabecalho is None:
        raise ValueError(f"Cabecalho nao encontrado no arquivo: {caminho}")

    df = bruto.iloc[linha_cabecalho + 1:].copy()
    df.columns = bruto.iloc[linha_cabecalho].tolist()

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"])

    colunas_numericas = [
        "kWh fornecido", "kWh recebido",
        "kVArh fornecido", "kVArh recebido",
        "Vln a", "Vln b", "Vln c",
        "Ia", "Ib", "Ic",
        "FP a", "FP b", "FP c"
    ]

    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["kWh fornecido"])
    return df

# ============================================================
# LEITURA DAS BASES
# ============================================================

bases = []
resumo_medidores = []

for (mes, ponto), caminho in arquivos.items():
    df = ler_planilha_grandezas(caminho)
    df["Mes"] = mes
    df["Ponto"] = ponto
    bases.append(df)

    resumo_medidores.append({
        "Mes": mes,
        "Ponto": ponto,
        "Registros": len(df),
        "Inicio": df["Data"].min(),
        "Fim": df["Data"].max(),
        "kWh fornecido": df["kWh fornecido"].sum(),
        "kWh recebido": df["kWh recebido"].sum() if "kWh recebido" in df.columns else 0,
        "Vln a medio": df["Vln a"].mean() if "Vln a" in df.columns else np.nan,
        "Vln b medio": df["Vln b"].mean() if "Vln b" in df.columns else np.nan,
        "Vln c medio": df["Vln c"].mean() if "Vln c" in df.columns else np.nan,
        "Ia medio": df["Ia"].mean() if "Ia" in df.columns else np.nan,
        "Ib medio": df["Ib"].mean() if "Ib" in df.columns else np.nan,
        "Ic medio": df["Ic"].mean() if "Ic" in df.columns else np.nan,
    })

base_final = pd.concat(bases, ignore_index=True)
resumo_medidores = pd.DataFrame(resumo_medidores)

# ============================================================
# TOTAIS POR PONTO
# ============================================================

tabela_energia = (
    resumo_medidores
    .pivot(index="Mes", columns="Ponto", values="kWh fornecido")
    .reset_index()
)

for col in ["SE S2", "SE S3", "SE S4"]:
    if col not in tabela_energia.columns:
        tabela_energia[col] = 0

tabela_energia = tabela_energia[["Mes", "SE S2", "SE S3", "SE S4"]]

# ============================================================
# BALANCO MENSAL
# ============================================================

resultados = []

for _, row in tabela_energia.iterrows():
    mes = row["Mes"]
    se2 = row["SE S2"]  # Fonte / Energia Requerida
    se3_medido = row["SE S3"]  # Cliente Livre medido
    se4 = row["SE S4"]  # Mercado Regulado

    # Regra do enunciado:
    # Fev/25: SE S3 ainda nao entra no circuito da SE S2.
    # Out/25: SE S3 entra no balanco.
    if mes == "Fev/25":
        se3_balanco = 0
    else:
        se3_balanco = se3_medido

    energia_requerida = se2
    mercado_regulado = se4
    mercado_livre = se3_balanco

    perdas = energia_requerida - mercado_regulado - mercado_livre
    perdas_percentual = perdas / energia_requerida * 100 if energia_requerida != 0 else np.nan

    status = "Inconsistente - perdas negativas" if perdas < 0 else "Balanco fisico positivo"

    resultados.append({
        "Mes": mes,
        "Energia Requerida SE S2 (kWh)": energia_requerida,
        "Mercado Regulado SE S4 (kWh)": mercado_regulado,
        "Mercado Livre SE S3 considerado (kWh)": mercado_livre,
        "SE S3 medido na planilha (kWh)": se3_medido,
        "Perdas (kWh)": perdas,
        "Perdas (%)": perdas_percentual,
        "Status": status
    })

balanco = pd.DataFrame(resultados)

# ============================================================
# BALANCO INTERVALAR
# ============================================================

bases_dict = {}
for df in bases:
    bases_dict[(df["Mes"].iloc[0], df["Ponto"].iloc[0])] = df

balanco_intervalar = []

for mes in ["Fev/25", "Out/25"]:
    s2 = bases_dict[(mes, "SE S2")][["Data", "kWh fornecido"]].rename(columns={"kWh fornecido": "SE S2"})
    s4 = bases_dict[(mes, "SE S4")][["Data", "kWh fornecido"]].rename(columns={"kWh fornecido": "SE S4"})

    base_mes = s2.merge(s4, on="Data", how="inner")

    if mes == "Out/25":
        s3 = bases_dict[(mes, "SE S3")][["Data", "kWh fornecido"]].rename(columns={"kWh fornecido": "SE S3"})
        base_mes = base_mes.merge(s3, on="Data", how="inner")
        base_mes["SE S3 considerado"] = base_mes["SE S3"]
    else:
        base_mes["SE S3"] = 0
        base_mes["SE S3 considerado"] = 0

    base_mes["Mes"] = mes
    base_mes["Energia Requerida"] = base_mes["SE S2"]
    base_mes["Mercado Regulado"] = base_mes["SE S4"]
    base_mes["Mercado Livre"] = base_mes["SE S3 considerado"]

    base_mes["Perdas"] = (
        base_mes["Energia Requerida"]
        - base_mes["Mercado Regulado"]
        - base_mes["Mercado Livre"]
    )

    base_mes["Perdas (%)"] = np.where(
        base_mes["Energia Requerida"] != 0,
        base_mes["Perdas"] / base_mes["Energia Requerida"] * 100,
        np.nan
    )

    balanco_intervalar.append(base_mes)

balanco_intervalar = pd.concat(balanco_intervalar, ignore_index=True)

# ============================================================
# GRAFICO 1 - BALANCO MENSAL POR COMPONENTE
# ============================================================

plt.figure(figsize=(10, 6))
x = np.arange(len(balanco))
largura = 0.22

plt.bar(x - largura, balanco["Energia Requerida SE S2 (kWh)"] / 1000, width=largura, label="Energia Requerida - SE S2")
plt.bar(x, balanco["Mercado Regulado SE S4 (kWh)"] / 1000, width=largura, label="Mercado Regulado - SE S4")
plt.bar(x + largura, balanco["Mercado Livre SE S3 considerado (kWh)"] / 1000, width=largura, label="Mercado Livre - SE S3")

plt.xticks(x, balanco["Mes"])
plt.ylabel("Energia (MWh)")
plt.title("Caso 3 - Balanco mensal de energia do circuito")
plt.grid(axis="y", alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("caso3_balanco_mensal_componentes.png", dpi=300, bbox_inches="tight")
plt.show()

# ============================================================
# GRAFICO 2 - PERDAS MENSAIS
# ============================================================

plt.figure(figsize=(8, 5))
plt.bar(balanco["Mes"], balanco["Perdas (kWh)"] / 1000)
plt.axhline(0, color="black", linewidth=1)
plt.title("Caso 3 - Perdas eletricas calculadas")
plt.ylabel("Perdas (MWh)")
plt.xlabel("Ciclo")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("caso3_perdas_mensais.png", dpi=300, bbox_inches="tight")
plt.show()

# ============================================================
# GRAFICO 3 - PERDAS INTERVALARES
# ============================================================

for mes in ["Fev/25", "Out/25"]:
    dados = balanco_intervalar[balanco_intervalar["Mes"] == mes].copy()
    dados = dados.sort_values("Data")
    dados["Indice"] = range(1, len(dados) + 1)

    plt.figure(figsize=(14, 5.5))
    plt.plot(dados["Indice"], dados["Perdas"], linewidth=1.2, label=f"Perdas por intervalo - {mes}")
    plt.axhline(0, color="black", linewidth=1)

    plt.title(f"Caso 3 - Perdas intervalares - {mes}")
    plt.xlabel("Intervalo de medicao")
    plt.ylabel("Perdas por intervalo (kWh)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    nome = f"caso3_perdas_intervalares_{mes.replace('/', '_')}.png"
    plt.savefig(nome, dpi=300, bbox_inches="tight")
    plt.show()

# ============================================================
# EXPORTACAO
# ============================================================

resumo_medidores.to_csv("caso3_resumo_medidores.csv", sep=";", decimal=",", index=False)
balanco.to_csv("caso3_balanco_mensal.csv", sep=";", decimal=",", index=False)
balanco_intervalar.to_csv("caso3_balanco_intervalar.csv", sep=";", decimal=",", index=False)

with pd.ExcelWriter("caso3_resultados_balanco_energia.xlsx", engine="openpyxl") as writer:
    resumo_medidores.to_excel(writer, sheet_name="Resumo Medidores", index=False)
    balanco.to_excel(writer, sheet_name="Balanco Mensal", index=False)
    balanco_intervalar.to_excel(writer, sheet_name="Balanco Intervalar", index=False)

# ============================================================
# RESULTADOS NO TERMINAL
# ============================================================

print("\n==============================")
print("RESUMO DOS MEDIDORES")
print("==============================")
print(resumo_medidores.round(2))

print("\n==============================")
print("BALANCO MENSAL")
print("==============================")
print(balanco.round(2))

print("\nArquivos gerados:")
print("- caso3_resumo_medidores.csv")
print("- caso3_balanco_mensal.csv")
print("- caso3_balanco_intervalar.csv")
print("- caso3_resultados_balanco_energia.xlsx")
print("- caso3_balanco_mensal_componentes.png")
print("- caso3_perdas_mensais.png")
print("- caso3_perdas_intervalares_Fev_25.png")
print("- caso3_perdas_intervalares_Out_25.png")

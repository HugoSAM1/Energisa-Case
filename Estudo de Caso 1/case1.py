import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ==================================================
# 0. CAMINHO DOS ARQUIVOS
# ==================================================

base = Path(".")

arquivo_p1 = base / "Dados de Grandezas eletricas Fev-25 SE S1 P1.xlsx"
arquivo_p2 = base / "Dados de Grandezas eletricas Fev-25 SE S1 P2.xlsx"


# ==================================================
# 1. FUNÇÃO PARA LER AS PLANILHAS
# ==================================================

def ler(caminho):
    bruto = pd.read_excel(caminho, header=None)
    cab = None

    for i in range(min(20, len(bruto))):
        linha = bruto.iloc[i].astype(str).str.strip().tolist()

        if "Data" in linha and "kWh fornecido" in linha:
            cab = i
            break

    if cab is None:
        raise ValueError(f"Cabeçalho não encontrado no arquivo: {caminho}")

    df = bruto.iloc[cab + 1:].copy()
    df.columns = bruto.iloc[cab].tolist()

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"])

    colunas_usadas = [
        "kWh fornecido",
        "Vln a",
        "Vln b",
        "Vln c"
    ]

    for c in colunas_usadas:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=colunas_usadas)

    return df


# ==================================================
# 2. LEITURA DAS BASES P1 E P2
# ==================================================

p1 = ler(arquivo_p1)
p2 = ler(arquivo_p2)


# ==================================================
# 3. IDENTIFICAÇÃO DA ANOMALIA NO P2
# ==================================================

tensoes = p2[["Vln a", "Vln b", "Vln c"]]

# Tensão de referência: mediana das três fases
vref = tensoes.median(axis=1)

# Maior desvio percentual entre as fases
desvio = (
    tensoes
    .sub(vref, axis=0)
    .abs()
    .div(vref, axis=0)
    .max(axis=1)
)

# Considera anomalia quando o desequilíbrio de tensão for maior que 5%
anomalia = desvio > 0.05


# ==================================================
# 4. CONSTRUÇÃO DAS CURVAS DO P2
# ==================================================

p2 = p2.copy()

# Curva original registrada pelo medidor
p2["P2_original"] = p2["kWh fornecido"]

# Curto prazo:
# Regra 1 TI: fator 1,5 nos intervalos anômalos
p2["P2_curto_prazo"] = np.where(
    anomalia,
    p2["kWh fornecido"] * 1.5,
    p2["kWh fornecido"]
)

# Médio prazo:
# Recomposição técnica pela consistência das tensões trifásicas
fator_medio = (3 * vref) / (
    p2["Vln a"] + p2["Vln b"] + p2["Vln c"]
)

fator_medio = (
    fator_medio
    .replace([np.inf, -np.inf], np.nan)
    .fillna(1)
)

p2["P2_medio_prazo"] = np.where(
    anomalia,
    p2["kWh fornecido"] * fator_medio,
    p2["kWh fornecido"]
)

# Índice sequencial para o eixo X
p2["Indice"] = range(1, len(p2) + 1)


# ==================================================
# 5. CONSTRUÇÃO DAS CURVAS DA SE S1
# ==================================================
# S1 = P1 + P2

s1 = p1[["Data", "kWh fornecido"]].rename(
    columns={"kWh fornecido": "P1"}
)

s1 = s1.merge(
    p2[[
        "Data",
        "P2_original",
        "P2_curto_prazo",
        "P2_medio_prazo"
    ]],
    on="Data",
    how="inner"
)

s1["S1_original"] = s1["P1"] + s1["P2_original"]
s1["S1_curto_prazo"] = s1["P1"] + s1["P2_curto_prazo"]
s1["S1_medio_prazo"] = s1["P1"] + s1["P2_medio_prazo"]

s1["Indice"] = range(1, len(s1) + 1)


# ==================================================
# 6. GRÁFICO P2
# ==================================================

plt.figure(figsize=(12, 5.5))

plt.plot(
    p2["Indice"],
    p2["P2_original"],
    color="purple",
    label="P2 original / medição com falha",
    linewidth=1.5
)

plt.plot(
    p2["Indice"],
    p2["P2_curto_prazo"],
    color="blue",
    label="P2 curto prazo - Fator corretivo ",
    linewidth=1.5
)

plt.plot(
    p2["Indice"],
    p2["P2_medio_prazo"],
    color="red",
    label="P2 médio prazo - recomposição técnica",
    linewidth=1.5
)

plt.title(
    "P2 - Comparação entre Medição Original e Curvas Recompostas",
    fontsize=14,
    fontweight="bold"
)

plt.xlabel("Intervalo de medição")
plt.ylabel("Energia ativa EAE por intervalo (kWh)")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    "grafico_P2_original_curto_medio.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==================================================
# 7. GRÁFICO S1
# ==================================================

plt.figure(figsize=(12, 5.5))

plt.plot(
    s1["Indice"],
    s1["S1_original"],
    color="purple",
    label="S1 original",
    linewidth=1.5
)

plt.plot(
    s1["Indice"],
    s1["S1_curto_prazo"],
    color="blue",
    label="S1 curto prazo - P2 com Fator corretivo",
    linewidth=1.5
)

plt.plot(
    s1["Indice"],
    s1["S1_medio_prazo"],
    color="red",
    label="S1 médio prazo - P2 recomposto tecnicamente",
    linewidth=1.5
)

plt.title(
    "SE S1 - Impacto da Recomposição da Medição do P2",
    fontsize=14,
    fontweight="bold"
)

plt.xlabel("Intervalo de medição")
plt.ylabel("Energia ativa EAE por intervalo (kWh)")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    "grafico_S1_original_curto_medio.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==================================================
# 8. RESUMO NUMÉRICO
# ==================================================

resumo = pd.DataFrame({
    "Curva": [
        "P2 original",
        "P2 curto prazo - Fator corretivo",
        "P2 médio prazo - recomposição técnica",
        "S1 original",
        "S1 curto prazo - P2 Fator corretivo",
        "S1 médio prazo - P2 recomposto"
    ],
    "Energia total MWh": [
        p2["P2_original"].sum() / 1000,
        p2["P2_curto_prazo"].sum() / 1000,
        p2["P2_medio_prazo"].sum() / 1000,
        s1["S1_original"].sum() / 1000,
        s1["S1_curto_prazo"].sum() / 1000,
        s1["S1_medio_prazo"].sum() / 1000
    ]
})

print("\nResumo das curvas:")
print(resumo.round(2))

resumo.to_csv(
    "resumo_intervalar_P2_S1_curto_medio.csv",
    sep=";",
    decimal=",",
    index=False
)

print("\nArquivos gerados:")
print("- grafico_P2_original_curto_medio.png")
print("- grafico_S1_original_curto_medio.png")
print("- resumo_intervalar_P2_S1_curto_medio.csv")
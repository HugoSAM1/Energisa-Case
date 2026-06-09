import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error

# ==================================================
# 1. CAMINHO DOS ARQUIVOS
# ==================================================

base = Path(".")

arquivo_energia = base / "Curva de Energia Requerida Diária - 2015 - 2025.xlsx"
arquivo_temp = base / "Curva da temperatura média - 2019 - 2025.xlsx"


# ==================================================
# 2. LEITURA DAS BASES
# ==================================================

energia = pd.read_excel(arquivo_energia)
temperatura = pd.read_excel(arquivo_temp)

energia["Data"] = pd.to_datetime(energia["Data"], errors="coerce")
temperatura["Data"] = pd.to_datetime(temperatura["Data"], errors="coerce")

energia = energia.dropna(subset=["Data", "EMS"])
temperatura = temperatura.dropna(subset=["Data"])

col_temp = "Temperatura média da cidade de Campo Grande"

energia["EMS"] = pd.to_numeric(energia["EMS"], errors="coerce")
temperatura[col_temp] = pd.to_numeric(temperatura[col_temp], errors="coerce")

energia = energia.dropna(subset=["EMS"])
temperatura = temperatura.dropna(subset=[col_temp])


# ==================================================
# 3. JUNÇÃO DAS BASES
# ==================================================

df = energia.merge(
    temperatura[["Data", col_temp]],
    on="Data",
    how="left"
)

df = df.rename(columns={
    "EMS": "Energia_Requerida",
    col_temp: "Temperatura"
})

df["Mes"] = df["Data"].dt.month

df["Temperatura"] = df.groupby("Mes")["Temperatura"].transform(
    lambda x: x.fillna(x.mean())
)

df = df.dropna(subset=["Temperatura"])


# ==================================================
# 4. CRIAÇÃO DAS VARIÁVEIS DO MODELO
# ==================================================

df["Ano"] = df["Data"].dt.year
df["Mes"] = df["Data"].dt.month
df["Dia"] = df["Data"].dt.day
df["Dia_Ano"] = df["Data"].dt.dayofyear
df["Dia_Semana"] = df["Data"].dt.weekday
df["Fim_Semana"] = df["Dia_Semana"].isin([5, 6]).astype(int)

df["Tendencia"] = (df["Data"] - df["Data"].min()).dt.days

df["Seno_Anual"] = np.sin(2 * np.pi * df["Dia_Ano"] / 365)
df["Cosseno_Anual"] = np.cos(2 * np.pi * df["Dia_Ano"] / 365)

df["Proxy_GD_Tendencia"] = df["Tendencia"]


# ==================================================
# 5. TREINAMENTO DO RANDOM FOREST
# ==================================================

features = [
    "Ano",
    "Mes",
    "Dia",
    "Dia_Ano",
    "Dia_Semana",
    "Fim_Semana",
    "Temperatura",
    "Tendencia",
    "Seno_Anual",
    "Cosseno_Anual",
    "Proxy_GD_Tendencia"
]

X = df[features]
y = df["Energia_Requerida"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    shuffle=False
)

modelo = RandomForestRegressor(
    n_estimators=500,
    max_depth=12,
    min_samples_leaf=3,
    random_state=42,
    n_jobs=-1
)

modelo.fit(X_train, y_train)

y_pred = modelo.predict(X_test)
mape = mean_absolute_percentage_error(y_test, y_pred)

print(f"MAPE do modelo: {mape:.2%}")


# ==================================================
# 6. BASE FUTURA - SETEMBRO E OUTUBRO/2025
# ==================================================

datas_futuras = pd.date_range(
    start="2025-09-01",
    end="2025-10-31",
    freq="D"
)

futuro = pd.DataFrame({"Data": datas_futuras})

futuro["Ano"] = futuro["Data"].dt.year
futuro["Mes"] = futuro["Data"].dt.month
futuro["Dia"] = futuro["Data"].dt.day
futuro["Dia_Ano"] = futuro["Data"].dt.dayofyear
futuro["Dia_Semana"] = futuro["Data"].dt.weekday
futuro["Fim_Semana"] = futuro["Dia_Semana"].isin([5, 6]).astype(int)

futuro["Tendencia"] = (futuro["Data"] - df["Data"].min()).dt.days

futuro["Seno_Anual"] = np.sin(2 * np.pi * futuro["Dia_Ano"] / 365)
futuro["Cosseno_Anual"] = np.cos(2 * np.pi * futuro["Dia_Ano"] / 365)

futuro["Proxy_GD_Tendencia"] = futuro["Tendencia"]

temp_media_mes = df.groupby("Mes")["Temperatura"].mean()
futuro["Temperatura"] = futuro["Mes"].map(temp_media_mes)


# ==================================================
# 7. PROJEÇÃO
# ==================================================

futuro["Realista_MWh"] = modelo.predict(futuro[features])

futuro["Otimista_MWh"] = futuro["Realista_MWh"] * 0.95
futuro["Pessimista_MWh"] = futuro["Realista_MWh"] * 1.05


# ==================================================
# 8. RESUMO MENSAL
# ==================================================

resumo_mensal = (
    futuro
    .groupby("Mes")[["Otimista_MWh", "Realista_MWh", "Pessimista_MWh"]]
    .sum()
)

resumo_mensal.index = resumo_mensal.index.map({
    9: "Setembro/25",
    10: "Outubro/25"
})

print("\nResumo mensal projetado:")
print(resumo_mensal.round(2))


# ==================================================
# FUNÇÃO AUXILIAR PARA FORMATAR DATAS DIÁRIAS
# ==================================================

def formatar_eixo_diario(ax):
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    plt.xticks(rotation=90, fontsize=8)


# ==================================================
# 9. GRÁFICO DIÁRIO COMPLETO - SETEMBRO E OUTUBRO
# ==================================================

plt.figure(figsize=(20, 7))

plt.plot(
    futuro["Data"],
    futuro["Otimista_MWh"],
    color="green",
    linewidth=1.8,
    label="Cenário otimista"
)

plt.plot(
    futuro["Data"],
    futuro["Realista_MWh"],
    color="blue",
    linewidth=2.5,
    label="Cenário realista"
)

plt.plot(
    futuro["Data"],
    futuro["Pessimista_MWh"],
    color="red",
    linewidth=1.8,
    label="Cenário pessimista"
)

plt.title(
    "EMP1 - Projeção Diária da Energia Requerida - Set/25 e Out/25",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Data")
plt.ylabel("Energia Requerida projetada (MWh/dia)")
plt.grid(True, alpha=0.3)
plt.legend()

ax = plt.gca()
formatar_eixo_diario(ax)

plt.tight_layout()

plt.savefig(
    "grafico_diario_completo_set_out_2025.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==================================================
# 10. GRÁFICO DIÁRIO - SETEMBRO
# ==================================================

setembro = futuro[futuro["Mes"] == 9]

plt.figure(figsize=(16, 6))

plt.plot(
    setembro["Data"],
    setembro["Otimista_MWh"],
    color="green",
    linewidth=2,
    label="Cenário otimista"
)

plt.plot(
    setembro["Data"],
    setembro["Realista_MWh"],
    color="blue",
    linewidth=3,
    label="Cenário realista"
)

plt.plot(
    setembro["Data"],
    setembro["Pessimista_MWh"],
    color="red",
    linewidth=2,
    label="Cenário pessimista"
)

plt.title(
    "EMP1 - Projeção Diária da Energia Requerida - Setembro/25",
    fontsize=14,
    fontweight="bold"
)

plt.xlabel("Data")
plt.ylabel("Energia Requerida projetada (MWh/dia)")
plt.grid(True, alpha=0.3)
plt.legend()

ax = plt.gca()
formatar_eixo_diario(ax)

plt.tight_layout()

plt.savefig(
    "grafico_diario_setembro_2025.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==================================================
# 11. GRÁFICO DIÁRIO - OUTUBRO
# ==================================================

outubro = futuro[futuro["Mes"] == 10]

plt.figure(figsize=(16, 6))

plt.plot(
    outubro["Data"],
    outubro["Otimista_MWh"],
    color="green",
    linewidth=2,
    label="Cenário otimista"
)

plt.plot(
    outubro["Data"],
    outubro["Realista_MWh"],
    color="blue",
    linewidth=3,
    label="Cenário realista"
)

plt.plot(
    outubro["Data"],
    outubro["Pessimista_MWh"],
    color="red",
    linewidth=2,
    label="Cenário pessimista"
)

plt.title(
    "EMP1 - Projeção Diária da Energia Requerida - Outubro/25",
    fontsize=14,
    fontweight="bold"
)

plt.xlabel("Data")
plt.ylabel("Energia Requerida projetada (MWh/dia)")
plt.grid(True, alpha=0.3)
plt.legend()

ax = plt.gca()
formatar_eixo_diario(ax)

plt.tight_layout()

plt.savefig(
    "grafico_diario_outubro_2025.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==================================================
# 12. GRÁFICO EXECUTIVO - FAIXA DE CENÁRIOS
# ==================================================

plt.figure(figsize=(14, 6))

plt.fill_between(
    futuro["Data"],
    futuro["Otimista_MWh"],
    futuro["Pessimista_MWh"],
    alpha=0.25,
    color="lightblue",
    label="Faixa de cenários"
)

plt.plot(
    futuro["Data"],
    futuro["Realista_MWh"],
    color="navy",
    linewidth=3,
    label="Cenário realista"
)

plt.title(
    "EMP1 - Projeção da Energia Requerida com Faixa de Cenários",
    fontsize=14,
    fontweight="bold"
)

plt.xlabel("Data")
plt.ylabel("Energia Requerida projetada (MWh/dia)")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    "grafico_executivo_faixa_cenarios_set_out_2025.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==================================================
# 13. GRÁFICO ENERGIA X TEMPERATURA
# ==================================================

fig, ax1 = plt.subplots(figsize=(14, 6))

ax1.plot(
    futuro["Data"],
    futuro["Realista_MWh"],
    color="blue",
    linewidth=2.5,
    label="Energia Requerida projetada"
)

ax1.set_xlabel("Data")
ax1.set_ylabel("Energia Requerida projetada (MWh/dia)")
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()

ax2.plot(
    futuro["Data"],
    futuro["Temperatura"],
    color="orange",
    linestyle="--",
    linewidth=2,
    label="Temperatura média"
)

ax2.set_ylabel("Temperatura média (°C)")

plt.title(
    "EMP1 - Energia Requerida Projetada x Temperatura",
    fontsize=14,
    fontweight="bold"
)

linhas1, labels1 = ax1.get_legend_handles_labels()
linhas2, labels2 = ax2.get_legend_handles_labels()

ax1.legend(
    linhas1 + linhas2,
    labels1 + labels2,
    loc="upper left"
)

plt.tight_layout()

plt.savefig(
    "grafico_energia_vs_temperatura_set_out_2025.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==================================================
# 14. BASE HORÁRIA
# ==================================================

perfil_horario = np.array([
    0.035, 0.032, 0.030, 0.029, 0.030, 0.033,
    0.038, 0.043, 0.046, 0.047, 0.045, 0.042,
    0.039, 0.037, 0.036, 0.038, 0.043, 0.050,
    0.058, 0.062, 0.058, 0.052, 0.045, 0.040
])

perfil_horario = perfil_horario / perfil_horario.sum()

linhas_horarias = []

for _, row in futuro.iterrows():
    for hora in range(24):
        linhas_horarias.append({
            "Data": row["Data"],
            "Hora": hora,
            "Otimista_MWh": row["Otimista_MWh"] * perfil_horario[hora],
            "Realista_MWh": row["Realista_MWh"] * perfil_horario[hora],
            "Pessimista_MWh": row["Pessimista_MWh"] * perfil_horario[hora],
        })

horario = pd.DataFrame(linhas_horarias)


# ==================================================
# 15. GRÁFICO PERFIL HORÁRIO MÉDIO
# ==================================================

perfil_medio = (
    horario
    .groupby("Hora")[["Otimista_MWh", "Realista_MWh", "Pessimista_MWh"]]
    .mean()
)

plt.figure(figsize=(12, 5.5))

plt.plot(
    perfil_medio.index,
    perfil_medio["Otimista_MWh"],
    color="green",
    linewidth=2,
    label="Otimista"
)

plt.plot(
    perfil_medio.index,
    perfil_medio["Realista_MWh"],
    color="blue",
    linewidth=3,
    label="Realista"
)

plt.plot(
    perfil_medio.index,
    perfil_medio["Pessimista_MWh"],
    color="red",
    linewidth=2,
    label="Pessimista"
)

plt.title(
    "EMP1 - Perfil Horário Médio Projetado",
    fontsize=14,
    fontweight="bold"
)

plt.xlabel("Hora do dia")
plt.ylabel("Energia Requerida média (MWh/h)")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    "grafico_perfil_horario_medio_random_forest.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==================================================
# 16. SALVAR RESULTADOS
# ==================================================

futuro.to_csv(
    "projecao_diaria_random_forest_set_out_2025.csv",
    sep=";",
    decimal=",",
    index=False
)

horario.to_csv(
    "projecao_horaria_random_forest_set_out_2025.csv",
    sep=";",
    decimal=",",
    index=False
)

resumo_mensal.to_csv(
    "resumo_mensal_random_forest_set_out_2025.csv",
    sep=";",
    decimal=","
)

print("\nArquivos gerados:")
print("- grafico_diario_completo_set_out_2025.png")
print("- grafico_diario_setembro_2025.png")
print("- grafico_diario_outubro_2025.png")
print("- grafico_executivo_faixa_cenarios_set_out_2025.png")
print("- grafico_energia_vs_temperatura_set_out_2025.png")
print("- grafico_perfil_horario_medio_random_forest.png")
print("- projecao_diaria_random_forest_set_out_2025.csv")
print("- projecao_horaria_random_forest_set_out_2025.csv")
print("- resumo_mensal_random_forest_set_out_2025.csv")
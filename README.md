# Energisa - Data Analytics Case

Projeto desenvolvido para resolução de estudos de caso envolvendo análise de medição, projeção de demanda energética e balanço energético em sistemas de distribuição.

## Objetivo

Aplicar técnicas de análise de dados, engenharia elétrica e machine learning para resolução de problemas relacionados a:

* Qualidade de medição;
* Correção de falhas de SMF;
* Projeção de Energia Requerida;
* Balanço energético;
* Identificação de perdas;
* Suporte à tomada de decisão operacional.

---

## Estudo de Caso 1 – Análise de Medição da SE S1

### Objetivos

* Identificar a causa da redução de consumo observada;
* Avaliar os diagramas fasoriais;
* Propor soluções de curto, médio e longo prazo;
* Recompor a curva de carga.

### Principais conclusões

* Identificada inconsistência na fase B da medição P2;
* Aplicação de recomposição emergencial utilizando fator 1,5;
* Recomposição técnica baseada em comportamento histórico e validação operacional.

---

## Estudo de Caso 2 – Projeção da Energia Requerida

### Metodologia

* Python
* Pandas
* Scikit-Learn
* Random Forest Regressor

### Variáveis utilizadas

* Histórico de Energia Requerida;
* Temperatura média;
* Tendência temporal;
* Sazonalidade semanal;
* Sazonalidade anual;
* Evolução da geração distribuída.

### Resultados

| Mês         |    Otimista |    Realista |  Pessimista |
| ----------- | ----------: | ----------: | ----------: |
| Setembro/25 | 708.223 MWh | 745.498 MWh | 782.773 MWh |
| Outubro/25  | 746.814 MWh | 786.120 MWh | 825.426 MWh |

---

## Estudo de Caso 3 – Balanço Energético

### Objetivos

* Calcular Energia Requerida;
* Quantificar Mercado Livre;
* Quantificar Mercado Regulado;
* Determinar perdas;
* Identificar inconsistências de medição.

### Principais conclusões

* Perdas negativas identificadas em outubro/25;
* Evidência de inconsistência entre fonte e cargas;
* Necessidade de auditoria dos sistemas de medição;
* Proposta de automação para monitoramento contínuo do balanço energético.

---

## Tecnologias

* Python
* Pandas
* NumPy
* Matplotlib
* Scikit-Learn
* OpenPyXL

---

## Autor

Projeto desenvolvido para fins de avaliação técnica e demonstração de competências em análise de dados aplicadas ao setor elétrico.


# src/ui/constants.py

API_URL = "http://127.0.0.1:8000"
#https://spatial-analysis-algorithms-1.onrender.com/ 
#http://127.0.0.1:8000

METRIC_OPTIONS = {
    "Birth Rate (per 1,000 Inh.)": "birth_rate_per_1000",
    "Total Births": "total_births",
    "Births by Mothers <20 y.o.": "births_mother_under20",
    "Births by Mothers 20-29 y.o.": "births_mother_20to29",
    "Births by Mothers 30-39 y.o.": "births_mother_30to39",
    "Births by Mothers 40+ y.o.": "births_mother_40plus",
}

METRIC_OPTIONS_SINAN = {
    "Taxa de Prevalência (por 100.000 hab.)": "prevalence_per_100000",
    "Total de Casos Confirmados": "total_cases"
}
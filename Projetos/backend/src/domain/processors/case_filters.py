"""
Filtros de casos (cor/raça, sexo, faixa etária e escolaridade) comuns ao SINAN e ao e-SUS.

Os dois sistemas codificam os campos de forma diferente:
- SINAN (via pysus): CS_RACA '1'..'5'/'9', CS_SEXO 'M'/'F'/'I', CS_ESCOL_N '00'..'10'
- e-SUS Notifica:    CS_RACA 'Parda', 'Branca'..., CS_SEXO 'Masculino'/'Feminino',
                     CS_ESCOL_N 'EF Incompleto', 'EM Completo'...
A escolaridade do e-SUS é menos detalhada; os códigos do SINAN são agrupados nas mesmas categorias.
Ambos usam NU_IDADE_N no formato do SINAN: 1º dígito = unidade (1 hora, 2 dia, 3 mês, 4 ano),
demais dígitos = valor. Ex.: '4056' = 56 anos.
"""
import unicodedata
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd

RACE_CODES: Dict[str, str] = {
    "1": "branca", "2": "preta", "3": "amarela", "4": "parda", "5": "indigena", "9": "ignorado",
}
RACE_LABELS: Dict[str, str] = {
    "branca": "Branca", "preta": "Preta", "amarela": "Amarela",
    "parda": "Parda", "indigena": "Indígena", "ignorado": "Ignorado",
}

SEX_CODES: Dict[str, str] = {"m": "masculino", "f": "feminino", "i": "ignorado"}
SEX_LABELS: Dict[str, str] = {"masculino": "Masculino", "feminino": "Feminino", "ignorado": "Ignorado"}

# Chaves: códigos do SINAN e rótulos do e-SUS já normalizados (minúsculas, sem acentos)
EDUCATION_CODES: Dict[str, str] = {
    "00": "nenhuma", "nenhuma": "nenhuma",
    "01": "fundamental_incompleto", "02": "fundamental_incompleto", "03": "fundamental_incompleto",
    "ef incompleto": "fundamental_incompleto",
    "04": "fundamental_completo", "ef completo": "fundamental_completo",
    "05": "medio_incompleto", "em incompleto": "medio_incompleto",
    "06": "medio_completo", "em completo": "medio_completo",
    "07": "superior", "08": "superior", "superior": "superior",
    "09": "ignorado", "ignorado": "ignorado",
    "10": "nao_se_aplica", "nao se aplica": "nao_se_aplica",
}
EDUCATION_LABELS: Dict[str, str] = {
    "nenhuma": "Nenhuma/Analfabeto",
    "fundamental_incompleto": "Fundamental incompleto",
    "fundamental_completo": "Fundamental completo",
    "medio_incompleto": "Médio incompleto",
    "medio_completo": "Médio completo",
    "superior": "Superior",
    "ignorado": "Escolaridade ignorada",
    "nao_se_aplica": "Escolaridade não se aplica",
}

AGE_UNIT_YEARS = "4"

# Faixas etárias fixas: código -> (idade mínima, idade máxima ou None = sem limite), em anos completos
AGE_GROUPS: Dict[str, Tuple[int, Optional[int]]] = {
    "0_14": (0, 14), "15_29": (15, 29), "30_39": (30, 39), "40_49": (40, 49),
    "50_59": (50, 59), "60_69": (60, 69), "70_79": (70, 79), "80_mais": (80, None),
}
AGE_GROUP_LABELS: Dict[str, str] = {
    "0_14": "<15 anos", "15_29": "15-29 anos", "30_39": "30-39 anos", "40_49": "40-49 anos",
    "50_59": "50-59 anos", "60_69": "60-69 anos", "70_79": "70-79 anos", "80_mais": "80+ anos",
}


def normalize_text(value: Any) -> str:
    """Minúsculas e sem acentos, para comparar rótulos de fontes diferentes."""
    text = unicodedata.normalize("NFKD", str(value).strip().lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


@dataclass
class CaseFilters:
    races: Optional[List[str]] = None
    sexes: Optional[List[str]] = None
    age_groups: Optional[List[str]] = None
    education_levels: Optional[List[str]] = None

    def is_empty(self) -> bool:
        return not (self.races or self.sexes or self.age_groups or self.education_levels)

    def to_dict(self) -> Dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value not in (None, [])}

    def describe(self) -> str:
        """Descrição curta para títulos de mapas. Ex.: 'Parda, Preta | Feminino | 30-39 anos, 40-49 anos'."""
        parts = []
        if self.races:
            parts.append(", ".join(RACE_LABELS.get(r, r) for r in self.races))
        if self.sexes:
            parts.append(", ".join(SEX_LABELS.get(s, s) for s in self.sexes))
        if self.age_groups:
            parts.append(", ".join(AGE_GROUP_LABELS.get(g, g) for g in self.age_groups))
        if self.education_levels:
            parts.append(", ".join(EDUCATION_LABELS.get(e, e) for e in self.education_levels))
        return " | ".join(parts)


def _normalized_race(series: pd.Series) -> pd.Series:
    normalized = series.map(normalize_text)
    return normalized.map(lambda value: RACE_CODES.get(value, value))


def _normalized_sex(series: pd.Series) -> pd.Series:
    normalized = series.map(normalize_text)
    return normalized.map(lambda value: SEX_CODES.get(value, value))


def _normalized_education(series: pd.Series) -> pd.Series:
    normalized = series.map(normalize_text)
    return normalized.map(lambda value: EDUCATION_CODES.get(value, value))


def age_in_years(series: pd.Series) -> pd.Series:
    """Converte NU_IDADE_N para anos completos (menores de 1 ano = 0). Inválidos viram NaN."""
    text = series.astype(str).str.strip()
    unit = text.str[:1]
    value = pd.to_numeric(text.str[1:], errors="coerce")
    years = value.where(unit == AGE_UNIT_YEARS)
    return years.mask(unit.isin(["1", "2", "3"]) & value.notna(), 0)


def _age_groups(series: pd.Series) -> pd.Series:
    """Converte NU_IDADE_N para o código da faixa etária (AGE_GROUPS). Idade inválida vira NaN."""
    ages = age_in_years(series)
    groups = pd.Series(pd.NA, index=series.index, dtype=object)
    for code, (age_from, age_to) in AGE_GROUPS.items():
        in_group = ages >= age_from
        if age_to is not None:
            in_group &= ages <= age_to
        groups[in_group.fillna(False)] = code
    return groups


def apply_case_filters(df: pd.DataFrame, filters: Optional[CaseFilters]) -> pd.DataFrame:
    """Filtra os registros de notificação. Filtros cuja coluna não existe na base são ignorados."""
    if filters is None or filters.is_empty() or df.empty:
        return df

    mask = pd.Series(True, index=df.index)

    if filters.races and "CS_RACA" in df.columns:
        mask &= _normalized_race(df["CS_RACA"]).isin(filters.races)

    if filters.sexes and "CS_SEXO" in df.columns:
        mask &= _normalized_sex(df["CS_SEXO"]).isin(filters.sexes)

    if filters.age_groups and "NU_IDADE_N" in df.columns:
        # União das faixas marcadas
        mask &= _age_groups(df["NU_IDADE_N"]).isin(filters.age_groups)

    if filters.education_levels and "CS_ESCOL_N" in df.columns:
        mask &= _normalized_education(df["CS_ESCOL_N"]).isin(filters.education_levels)

    return df[mask.fillna(False)]


# --- Distribuições para gráficos -----------------------------------------------------------

NOT_INFORMED = "nao_informado"
DISTRIBUTION_COLUMNS = {"race": "CS_RACA", "sex": "CS_SEXO", "age_group": "NU_IDADE_N", "education": "CS_ESCOL_N"}
DISTRIBUTION_NORMALIZERS = {
    "race": _normalized_race,
    "sex": _normalized_sex,
    "age_group": _age_groups,
    "education": _normalized_education,
}
DISTRIBUTION_CATEGORIES = {
    "race": set(RACE_LABELS),
    "sex": set(SEX_LABELS),
    "age_group": set(AGE_GROUPS),
    "education": set(EDUCATION_LABELS),
}


def count_distributions(df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
    """
    Conta os registros por categoria de cada variável dos filtros (mesmas categorias da API).
    Valores vazios ou fora das categorias conhecidas viram 'nao_informado'.
    Variáveis cuja coluna não existe na base são omitidas.
    """
    distributions: Dict[str, Dict[str, int]] = {}
    for variable, column in DISTRIBUTION_COLUMNS.items():
        if column not in df.columns:
            continue
        values = DISTRIBUTION_NORMALIZERS[variable](df[column].dropna()).reindex(df.index)
        values = values.where(values.isin(DISTRIBUTION_CATEGORIES[variable]), NOT_INFORMED)
        distributions[variable] = {str(k): int(v) for k, v in values.value_counts().items()}
    return distributions

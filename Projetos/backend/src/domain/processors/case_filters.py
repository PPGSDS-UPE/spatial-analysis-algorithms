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
from typing import List, Optional, Dict, Any

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


def normalize_text(value: Any) -> str:
    """Minúsculas e sem acentos, para comparar rótulos de fontes diferentes."""
    text = unicodedata.normalize("NFKD", str(value).strip().lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


@dataclass
class CaseFilters:
    races: Optional[List[str]] = None
    sexes: Optional[List[str]] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    education_levels: Optional[List[str]] = None

    def is_empty(self) -> bool:
        return not (self.races or self.sexes or self.education_levels
                    or self.age_min is not None or self.age_max is not None)

    def to_dict(self) -> Dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value not in (None, [])}

    def describe(self) -> str:
        """Descrição curta para títulos de mapas. Ex.: 'Parda, Preta | Feminino | 20-59 anos'."""
        parts = []
        if self.races:
            parts.append(", ".join(RACE_LABELS.get(r, r) for r in self.races))
        if self.sexes:
            parts.append(", ".join(SEX_LABELS.get(s, s) for s in self.sexes))
        if self.age_min is not None or self.age_max is not None:
            if self.age_max is None:
                parts.append(f"{self.age_min}+ anos")
            elif self.age_min is None:
                parts.append(f"até {self.age_max} anos")
            else:
                parts.append(f"{self.age_min}-{self.age_max} anos")
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


def apply_case_filters(df: pd.DataFrame, filters: Optional[CaseFilters]) -> pd.DataFrame:
    """Filtra os registros de notificação. Filtros cuja coluna não existe na base são ignorados."""
    if filters is None or filters.is_empty() or df.empty:
        return df

    mask = pd.Series(True, index=df.index)

    if filters.races and "CS_RACA" in df.columns:
        mask &= _normalized_race(df["CS_RACA"]).isin(filters.races)

    if filters.sexes and "CS_SEXO" in df.columns:
        mask &= _normalized_sex(df["CS_SEXO"]).isin(filters.sexes)

    if (filters.age_min is not None or filters.age_max is not None) and "NU_IDADE_N" in df.columns:
        ages = age_in_years(df["NU_IDADE_N"])
        if filters.age_min is not None:
            mask &= ages >= filters.age_min
        if filters.age_max is not None:
            mask &= ages <= filters.age_max

    if filters.education_levels and "CS_ESCOL_N" in df.columns:
        mask &= _normalized_education(df["CS_ESCOL_N"]).isin(filters.education_levels)

    return df[mask.fillna(False)]

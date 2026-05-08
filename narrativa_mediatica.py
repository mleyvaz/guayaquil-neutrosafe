"""
Análisis narrativo mediático sobre violencia en Guayaquil.

Extensión del MVP `Copy_of_LLM_fsQCA_GuayaquilNEWS.ipynb` (Gemini CLI, abril 2026)
con tres mejoras críticas:

  1. fsQCA FUZZY (no crisp): membership continuo en [0, 1] usando confidence_textual.
  2. N-fsQCA (extension neutrosofica): cada claim mediático produce triplete (T, I, F)
     que permite representar paraconsistencia entre fuentes.
  3. Conexión con el dataset estructural (14 indicadores) para contraste
     "narrativa mediática vs estructura empírica".

Cuando se ejecuta sin OpenAI API key, usa un dataset sintético basado en los
patrones documentados en el MVP original, claramente etiquetado como "demo".
Para datos reales, ejecutar el notebook MVP con API key y reemplazar `data_claims`.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence, Iterable
import pandas as pd
import numpy as np

from neutrosophic_core import TIFTriplet, svnwa


# 8 condiciones causales del MVP
CONDITIONS = {
    "A_gang_fragmentation": "Fragmentación o alianzas entre bandas",
    "B_drug_routes_ports":  "Control de rutas del narcotráfico/puertos",
    "C_extortion_vacunas":  "Extorsión y vacunas",
    "D_territorial_war":    "Guerra territorial",
    "E_weapons_traffic":    "Tráfico de armas",
    "F_prison_link":        "Vínculo con cárceles",
    "G_institutional_weakness": "Debilidad institucional",
    "H_economic_pressure":  "Presión económica",
}
COND_KEYS = list(CONDITIONS.keys())
OUTCOME_KEY = "Y_violence_spike"


# Mapeo conceptual: condiciones mediáticas <-> indicadores estructurales (encuesta)
# Permite contraste prensa vs encuesta. Mapping curado, editable.
NARRATIVE_TO_STRUCTURAL = {
    "A_gang_fragmentation":     ["pandillas"],
    "B_drug_routes_ports":      [],  # no hay analogo directo en encuesta
    "C_extortion_vacunas":      ["pandillas", "leydeficiente"],
    "D_territorial_war":        ["pandillas", "policiainsuficiente"],
    "E_weapons_traffic":        ["leydeficiente"],
    "F_prison_link":            ["politicasgubernamentalesineficaces"],
    "G_institutional_weakness": ["corrupcion", "politicasgubernamentalesineficaces",
                                  "leydeficiente"],
    "H_economic_pressure":      ["desempleo", "pobreza", "brechaingresos"],
}


# =================================================================
# DATASET SINTETICO (representativo del MVP, marcado como demo)
# =================================================================
# Basado en los patrones tipicos que reportan: Reuters, Swissinfo, El Pais,
# El Universo, Expreso. Estructura: cada claim incluye polaridad + confianza.
# Para datos reales, ejecutar `MVP_fsQCA_original.ipynb` con OpenAI API key.

DEMO_CLAIMS_DATA = [
    # Reuters 2025-10-29 — fragmentation tras crackdown
    {"case_id": "N001", "source": "Reuters", "polarity": {
        "A_gang_fragmentation": 0.95, "D_territorial_war": 0.85,
        "G_institutional_weakness": 0.45, "F_prison_link": 0.50,
    }, "confidence": 0.85, "outcome_y": 1.0},
    # Swissinfo — traiciones y nuevas alianzas
    {"case_id": "N002", "source": "Swissinfo", "polarity": {
        "A_gang_fragmentation": 0.90, "D_territorial_war": 0.80,
        "C_extortion_vacunas": 0.40,
    }, "confidence": 0.78, "outcome_y": 1.0},
    # El País 2025-03-07 — 22 asesinados
    {"case_id": "N003", "source": "El País", "polarity": {
        "D_territorial_war": 0.90, "A_gang_fragmentation": 0.65,
        "G_institutional_weakness": 0.70, "B_drug_routes_ports": 0.55,
    }, "confidence": 0.82, "outcome_y": 1.0},
    # El Universo
    {"case_id": "N004", "source": "El Universo", "polarity": {
        "C_extortion_vacunas": 0.85, "A_gang_fragmentation": 0.50,
        "G_institutional_weakness": 0.60, "F_prison_link": 0.40,
    }, "confidence": 0.72, "outcome_y": 1.0},
    # Expreso
    {"case_id": "N005", "source": "Expreso", "polarity": {
        "B_drug_routes_ports": 0.85, "F_prison_link": 0.65,
        "E_weapons_traffic": 0.50, "G_institutional_weakness": 0.45,
    }, "confidence": 0.70, "outcome_y": 1.0},
    # InSight Crime — analisis estructural
    {"case_id": "N006", "source": "InSight Crime", "polarity": {
        "B_drug_routes_ports": 0.95, "F_prison_link": 0.85,
        "A_gang_fragmentation": 0.70, "G_institutional_weakness": 0.65,
    }, "confidence": 0.90, "outcome_y": 1.0},
    # Diario Extra — narrativa popular
    {"case_id": "N007", "source": "Diario Extra", "polarity": {
        "C_extortion_vacunas": 0.90, "D_territorial_war": 0.65,
    }, "confidence": 0.55, "outcome_y": 1.0},
    # Primicias — analisis de politica publica
    {"case_id": "N008", "source": "Primicias", "polarity": {
        "G_institutional_weakness": 0.85, "F_prison_link": 0.65,
        "H_economic_pressure": 0.55,
    }, "confidence": 0.80, "outcome_y": 1.0},
    # AP News
    {"case_id": "N009", "source": "AP News", "polarity": {
        "B_drug_routes_ports": 0.85, "D_territorial_war": 0.75,
        "A_gang_fragmentation": 0.55,
    }, "confidence": 0.78, "outcome_y": 1.0},
    # BBC Mundo
    {"case_id": "N010", "source": "BBC Mundo", "polarity": {
        "G_institutional_weakness": 0.75, "B_drug_routes_ports": 0.70,
        "H_economic_pressure": 0.60, "A_gang_fragmentation": 0.50,
    }, "confidence": 0.82, "outcome_y": 1.0},
    # France 24 — estructura macro
    {"case_id": "N011", "source": "France 24", "polarity": {
        "H_economic_pressure": 0.80, "G_institutional_weakness": 0.70,
        "B_drug_routes_ports": 0.60,
    }, "confidence": 0.75, "outcome_y": 1.0},
    # El Comercio
    {"case_id": "N012", "source": "El Comercio", "polarity": {
        "A_gang_fragmentation": 0.75, "C_extortion_vacunas": 0.65,
        "F_prison_link": 0.55,
    }, "confidence": 0.72, "outcome_y": 1.0},
    # PlanV — analisis critico
    {"case_id": "N013", "source": "PlanV", "polarity": {
        "G_institutional_weakness": 0.95, "H_economic_pressure": 0.70,
        "F_prison_link": 0.60,
    }, "confidence": 0.88, "outcome_y": 1.0},
    # GK
    {"case_id": "N014", "source": "GK", "polarity": {
        "G_institutional_weakness": 0.85, "C_extortion_vacunas": 0.60,
        "H_economic_pressure": 0.55,
    }, "confidence": 0.78, "outcome_y": 1.0},
    # La Hora — perspectiva regional
    {"case_id": "N015", "source": "La Hora", "polarity": {
        "C_extortion_vacunas": 0.75, "A_gang_fragmentation": 0.50,
    }, "confidence": 0.65, "outcome_y": 1.0},
    # Mongabay — pesca-narcotrafico
    {"case_id": "N016", "source": "Mongabay", "polarity": {
        "B_drug_routes_ports": 0.95, "H_economic_pressure": 0.65,
    }, "confidence": 0.80, "outcome_y": 1.0},
]


def load_demo_claims() -> pd.DataFrame:
    """
    Carga datos N-fsQCA. Prioridad:
    1. real_data/nfsqca_live.csv  (actualización automática diaria vía GitHub Actions)
    2. Datos demo sintéticos basados en los 16 medios del MVP original
    """
    live_path = Path(__file__).parent / "real_data" / "nfsqca_live.csv"
    if live_path.exists():
        try:
            df_live = pd.read_csv(live_path, encoding="utf-8")
            # nfsqca_live.csv tiene formato largo (condicion, T, I, F)
            # Convertir a formato ancho compatible con el pipeline existente
            if "condicion" in df_live.columns and "T" in df_live.columns:
                rows = []
                for i, r in df_live.iterrows():
                    row = {
                        "case_id": f"live_{i}",
                        "source": "live_feed",
                        "confidence": 1.0 - float(r.get("I", 0.2)),
                        OUTCOME_KEY: float(r.get("T", 0.5)),
                    }
                    for k in COND_KEYS:
                        row[k] = float(r["T"]) if r["condicion"] == k else 0.0
                    rows.append(row)
                df = pd.DataFrame(rows)
                df._is_live = True
                return df
        except Exception:
            pass

    # Fallback: datos demo sintéticos
    rows = []
    for c in DEMO_CLAIMS_DATA:
        row = {"case_id": c["case_id"], "source": c["source"],
               "confidence": c["confidence"], OUTCOME_KEY: c["outcome_y"]}
        for k in COND_KEYS:
            row[k] = c["polarity"].get(k, 0.0)
        rows.append(row)
    return pd.DataFrame(rows)


def load_live_nfsqca_summary() -> pd.DataFrame | None:
    """
    Carga el resumen N-fsQCA en vivo (T, I, F por condición).
    Retorna None si no hay datos en vivo disponibles.
    """
    live_path = Path(__file__).parent / "real_data" / "nfsqca_live.csv"
    if live_path.exists():
        try:
            return pd.read_csv(live_path, encoding="utf-8")
        except Exception:
            pass
    return None


# =================================================================
# fsQCA FUZZY — calibracion + truth table
# =================================================================
def calibrate_fuzzy(value: float, low: float = 0.3, high: float = 0.7) -> float:
    """
    Direct calibration to [0, 1] membership: linear mapping.
    For full fsQCA logistic calibration, use Ragin-Davey approach.
    """
    if value <= low:
        return 0.0
    if value >= high:
        return 1.0
    return (value - low) / (high - low)


def build_truth_table_fuzzy(df: pd.DataFrame, conds: Sequence[str],
                             outcome: str) -> pd.DataFrame:
    """
    Fuzzy truth table: each row is a configuration, with consistency = sum(min(X,Y)) / sum(X).
    Simplified version (no full fsQCA minimization, which requires R-QCA).
    """
    # For each case, determine its dominant configuration (which conditions > 0.5)
    cases = []
    for _, r in df.iterrows():
        config = tuple(int(r[c] >= 0.5) for c in conds)
        cases.append({
            "config": config,
            "memb": min(r[c] if r[c] >= 0.5 else (1 - r[c]) for c in conds),
            "y": r[outcome],
        })
    cf = pd.DataFrame(cases)
    grouped = cf.groupby("config", as_index=False).agg(
        n_cases=("y", "count"),
        sum_memb_y=("memb", lambda x: sum(min(m, y) for m, y in zip(x, cf.loc[x.index, "y"]))),
        sum_memb=("memb", "sum"),
        y_mean=("y", "mean"),
    )
    grouped["consistency"] = grouped["sum_memb_y"] / grouped["sum_memb"].replace(0, np.nan)
    return grouped.sort_values("n_cases", ascending=False).reset_index(drop=True)


# =================================================================
# N-fsQCA — extension neutrosofica de fsQCA
# =================================================================
def claims_to_tif(df_claims: pd.DataFrame, condition: str) -> TIFTriplet:
    """
    Para una condicion C, agregar todas las claims mediaticas a triplete (T, I, F).

      T = consenso de fuentes que afirman C como causa (mean ponderado)
      F = consenso de fuentes que la niegan (1 - polaridad si negativa)
      I = disagreement entre fuentes (varianza de polaridades * 4)

    Permite que T + F > 1 cuando hay paraconsistencia mediatica.
    """
    polarities = df_claims[condition].to_numpy()
    confidences = df_claims["confidence"].to_numpy()
    if len(polarities) == 0:
        return TIFTriplet(0.0, 1.0, 0.0)

    w = confidences / confidences.sum() if confidences.sum() > 0 else np.ones_like(confidences) / len(confidences)
    mean_pol = float((polarities * w).sum())
    # T: solo el componente positivo del consenso
    T = float(max(0.0, mean_pol))
    # F: solo el componente "no menciona / desestima" (1 - polaridad para casos con C bajo)
    low_polarity_w = w[polarities < 0.3].sum()
    F = float(low_polarity_w * 0.8)  # discount factor (no es lo mismo afirmar negacion que omitir)
    # I: disagreement entre fuentes
    var = float(((polarities - mean_pol) ** 2 * w).sum())
    I = float(min(var * 4.0, 1.0))

    return TIFTriplet(T=min(T, 1.0), I=I, F=min(F, 1.0))


def n_fsqca_table(df_claims: pd.DataFrame) -> pd.DataFrame:
    """N-fsQCA por condicion: triplete (T, I, F) + regimen."""
    rows = []
    for cond in COND_KEYS:
        t = claims_to_tif(df_claims, cond)
        rows.append({
            "condicion": cond,
            "descripcion": CONDITIONS[cond],
            "T": round(t.T, 3),
            "I": round(t.I, 3),
            "F": round(t.F, 3),
            "regimen": t.regime(),
            "paraconsistente": t.is_paraconsistent(),
        })
    return pd.DataFrame(rows).sort_values("T", ascending=False).reset_index(drop=True)


# =================================================================
# Contraste narrativa mediatica vs encuesta estructural
# =================================================================
def contrast_with_structural(n_fsqca_df: pd.DataFrame,
                              structural_means: dict[str, float]) -> pd.DataFrame:
    """
    Contraste prensa vs encuesta:
      Para cada condicion mediatica C, comparar T mediatico contra el promedio
      del / los indicadores estructurales mapeados.

      Si prensa T alto pero estructural bajo → narrativa amplificada.
      Si prensa T bajo pero estructural alto → narrativa silenciada.
    """
    rows = []
    for _, r in n_fsqca_df.iterrows():
        cond = r["condicion"]
        struct_keys = NARRATIVE_TO_STRUCTURAL.get(cond, [])
        if struct_keys:
            struct_mean = float(np.mean([structural_means.get(k, 0) for k in struct_keys]))
        else:
            struct_mean = float("nan")
        gap = r["T"] - struct_mean if not np.isnan(struct_mean) else float("nan")
        rows.append({
            "condicion": cond,
            "T_prensa": r["T"],
            "indicadores_encuesta": ", ".join(struct_keys) if struct_keys else "(sin mapeo)",
            "promedio_encuesta": round(struct_mean, 3) if not np.isnan(struct_mean) else None,
            "gap_prensa_minus_encuesta": round(gap, 3) if not np.isnan(gap) else None,
            "interpretacion": _interpret_gap(gap),
        })
    return pd.DataFrame(rows).sort_values(
        "gap_prensa_minus_encuesta",
        key=lambda s: s.fillna(-99), ascending=False).reset_index(drop=True)


def _interpret_gap(gap: float) -> str:
    if pd.isna(gap):
        return "(sin mapeo a encuesta)"
    if gap > 0.3:
        return "Narrativa AMPLIFICADA (prensa > encuesta)"
    if gap < -0.3:
        return "Narrativa SILENCIADA (encuesta > prensa)"
    return "Alineada"


if __name__ == "__main__":
    print("=== Demo claims (16 noticias sinteticas) ===\n")
    df = load_demo_claims()
    print(df.head(5).to_string())
    print(f"\nTotal: {len(df)} claims; outcome rate: {df[OUTCOME_KEY].mean():.2f}\n")

    print("=== N-fsQCA: triplete (T, I, F) por condicion ===\n")
    nfs = n_fsqca_table(df)
    print(nfs.to_string())

    print(f"\nCondiciones paraconsistentes (T+F>1): {nfs['paraconsistente'].sum()}")
    print(f"Distribucion de regimenes:")
    print(nfs['regimen'].value_counts().to_string())

    print("\n=== Contraste con encuesta estructural ===\n")
    struct_means = {
        "pandillas": 0.62, "leydeficiente": 0.66, "policiainsuficiente": 0.58,
        "corrupcion": 0.61, "politicasgubernamentalesineficaces": 0.62,
        "desempleo": 0.59, "pobreza": 0.58, "brechaingresos": 0.61,
    }
    contrast = contrast_with_structural(nfs, struct_means)
    print(contrast.to_string())

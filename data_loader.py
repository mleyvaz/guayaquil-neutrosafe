"""
Data loader: parses ViolenciaGuayaquil2_clean.csv and assembles a triadic
(T, I, F) matrix per analysis unit (sector / encuesta).

The dataset has 14 variables:
  Drivers estructurales (11): desempleo, pobreza, brechaingresos,
    desintegracionfamiliar, pandillas, faltaespaciospublicos,
    infraestructuradeficiente, policiainsuficiente,
    politicasgubernamentalesineficaces, corrupcion, leydeficiente
  Outcomes (3): percepcionviolencia, violenciafrecuente, sentimientoinseguridad

Each row is treated as one analysis unit. Synthetic sector names are
assigned for visualization purposes (clearly marked as demo-labels in
the dashboard).
"""
from __future__ import annotations
import os
import pandas as pd
import numpy as np
from typing import Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "data.csv")

DRIVER_COLS = [
    "desempleo", "pobreza", "brechaingresos",
    "desintegracionfamiliar", "pandillas", "faltaespaciospublicos",
    "infraestructuradeficiente", "policiainsuficiente",
    "politicasgubernamentalesineficaces", "corrupcion", "leydeficiente",
]
OUTCOME_COLS = ["percepcionviolencia", "violenciafrecuente", "sentimientoinseguridad"]

# Demo sector names (Guayaquil, parroquias urbanas reales).
# Marked clearly in dashboard as illustrative assignment.
DEMO_SECTORS = [
    "Tarqui — Bastión Popular", "Tarqui — Flor de Bastión", "Tarqui — Mucho Lote",
    "Febres-Cordero — Suburbio Oeste", "Febres-Cordero — Batallón del Suburbio",
    "Letamendi — 9 de Octubre", "García Moreno — Centenario",
    "Ximena — Floresta", "Ximena — Guasmo Sur", "Ximena — Guasmo Norte",
    "Ximena — Trinitaria", "Ximena — Cisne 2",
    "Pascuales — Mucho Lote 2", "Pascuales — Las Orquídeas",
    "Olmedo — Centro Sur", "Sucre — Centro Norte",
    "Roca — Urdesa Central", "Rocafuerte — Av. Pichincha",
    "9 de Octubre — Centro Histórico", "Carbo — Centro Bancario",
    "Bolívar — Sagrario", "Pedro Carbo — La Pradera",
    "Tenguel — Sur Rural", "Posorja — Suroeste Rural",
    "El Morro — Litoral", "Puná — Insular",
    "Juan Gómez Rendón — Progreso", "Chongón — Vía Costa",
]


def load_raw() -> pd.DataFrame:
    """Load raw CSV with comma-decimal handling."""
    df = pd.read_csv(DATA_PATH, decimal=",", thousands=None)
    # Coerce all to float (the CSV uses quoted strings for some 1.0 values)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna()
    return df


def assign_sectors(df: pd.DataFrame) -> pd.DataFrame:
    """Assign demo sector names. Clearly labeled as illustrative."""
    n = len(df)
    sectors = []
    # Cycle through demo sectors so we have multiple "observations" per sector
    for i in range(n):
        sectors.append(DEMO_SECTORS[i % len(DEMO_SECTORS)])
    df = df.copy()
    df.insert(0, "sector_demo", sectors)
    return df


def aggregate_by_sector(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate observations to sector level (mean of values per sector)."""
    agg = df.groupby("sector_demo")[DRIVER_COLS + OUTCOME_COLS].mean().reset_index()
    return agg


def build_tif_matrix(df_raw: pd.DataFrame, df_agg: pd.DataFrame) -> pd.DataFrame:
    """
    Construct (T, I, F) per (sector, indicator).

    For each sector × indicator:
      T = mean of value across observations of that sector (evidence of risk)
      F = 1 - mean (evidence of safety/complement; see Limitations §4)
      I = epistemic gap, computed as inter-observation std × 2 (capped at 1)
    """
    rows = []
    for _, r in df_agg.iterrows():
        sector = r["sector_demo"]
        obs = df_raw[df_raw["sector_demo"] == sector]
        for col in DRIVER_COLS + OUTCOME_COLS:
            val = float(r[col])
            T = round(val, 4)
            F = round(max(0.0, 1.0 - val - 0.1), 4)
            std = obs[col].std() if len(obs) > 1 else 0.15
            I = round(min(float(std * 2.0), 1.0), 4)
            rows.append({
                "sector": sector, "indicador": col,
                "T": T, "I": I, "F": F,
            })
    return pd.DataFrame(rows)


def load_and_prepare() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = load_raw()
    raw = assign_sectors(raw)
    agg = aggregate_by_sector(raw)
    tif = build_tif_matrix(raw, agg)
    return raw, agg, tif


if __name__ == "__main__":
    raw, agg, tif = load_and_prepare()
    print(f"Raw observations: {len(raw)} filas, {len(raw.columns)} columnas")
    print(f"Sectores agregados: {len(agg)}")
    print(f"Matriz TIF (sector x indicador): {len(tif)} filas")
    print()
    print("=== Primeras 3 filas raw ===")
    print(raw.head(3).to_string(max_cols=8))
    print()
    print("=== Primeros 3 sectores agregados ===")
    print(agg.head(3).to_string(max_cols=8))
    print()
    print("=== Primeras 6 filas TIF ===")
    print(tif.head(6).to_string())

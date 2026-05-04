"""
IPVE — Indice Pluriversal de Vulnerabilidad Estructural.

Reemplazo conceptualmente correcto del IVN escalar erróneo del archivo
200_ANALISIS_DATOS_VULNERABILIDAD.md (que sumaba T + I − F).

El IPVE NO es escalar. Es un objeto compuesto que:

  1. Devuelve el VECTOR triádico (T, I, F) por sector e indicador.
  2. Devuelve el RÉGIMEN (C1..C5) por sector e indicador.
  3. SOLO produce un score escalar pessimista/optimista para triage,
     SIEMPRE acompañado del triplete subyacente.

NO se debe usar el score como métrica única. Hacer eso reproduce el error
ontológico del IVN escalar.
"""
from __future__ import annotations
import pandas as pd
from typing import Optional
from neutrosophic_core import TIFTriplet, svnwa


# Pesos por defecto de indicadores estructurales (suman 1).
# Editables. Calibrados para que drivers estructurales (~70%) pesen más
# que outcomes percibidos (~30%) — refleja el énfasis en condiciones,
# no en percepción inmediata.
DEFAULT_WEIGHTS = {
    # Drivers estructurales (peso conjunto ~0.70)
    "desempleo": 0.10,
    "pobreza": 0.10,
    "brechaingresos": 0.06,
    "desintegracionfamiliar": 0.05,
    "pandillas": 0.08,
    "faltaespaciospublicos": 0.06,
    "infraestructuradeficiente": 0.05,
    "policiainsuficiente": 0.05,
    "politicasgubernamentalesineficaces": 0.05,
    "corrupcion": 0.05,
    "leydeficiente": 0.05,
    # Outcomes percibidos (peso conjunto ~0.30)
    "percepcionviolencia": 0.10,
    "violenciafrecuente": 0.10,
    "sentimientoinseguridad": 0.10,
}


def aggregate_sector(tif_df: pd.DataFrame, sector: str,
                     weights: Optional[dict] = None) -> TIFTriplet:
    """
    Aggregate (T, I, F) for one sector across all indicators using SVNWA.

    Returns a triplet that PRESERVES the triadic structure.
    NOT a scalar.
    """
    weights = weights or DEFAULT_WEIGHTS
    sub = tif_df[tif_df["sector"] == sector].copy()
    if sub.empty:
        raise ValueError(f"No data for sector {sector}")
    triplets = [TIFTriplet(T=float(r["T"]), I=float(r["I"]), F=float(r["F"])) for _, r in sub.iterrows()]
    w = [weights.get(r["indicador"], 0.05) for _, r in sub.iterrows()]
    return svnwa(triplets, w)


def ipve_table(tif_df: pd.DataFrame,
               weights: Optional[dict] = None) -> pd.DataFrame:
    """
    Return a per-sector table with:
      sector, T, I, F, regimen, score_pessimistic, score_optimistic, paraconsistent

    The two scores are TRIAGE-only. NEVER displayed without (T, I, F) alongside.
    """
    rows = []
    for sector in sorted(tif_df["sector"].unique()):
        agg = aggregate_sector(tif_df, sector, weights)
        rows.append({
            "sector": sector,
            "T": round(agg.T, 4),
            "I": round(agg.I, 4),
            "F": round(agg.F, 4),
            "regimen": agg.regime(),
            "score_triage_pess": round(agg.score_pessimistic(), 4),
            "score_triage_opt": round(agg.score_optimistic(), 4),
            "paraconsistente": agg.is_paraconsistent(),
        })
    return pd.DataFrame(rows)


def top_indicators_for_sector(tif_df: pd.DataFrame, sector: str,
                              by: str = "T", n: int = 5) -> pd.DataFrame:
    """Return top-n indicators for a sector, sorted by T (risk) or I (uncertainty)."""
    sub = tif_df[tif_df["sector"] == sector].copy()
    if by not in ("T", "I", "F"):
        raise ValueError("by must be T, I, or F")
    return sub.sort_values(by, ascending=False).head(n).reset_index(drop=True)


if __name__ == "__main__":
    from data_loader import load_and_prepare

    _, _, tif = load_and_prepare()
    ipve = ipve_table(tif)
    print("=== IPVE por sector (28 unidades) ===\n")
    print(ipve.to_string())
    print(f"\nSectores en regimen paraconsistente: "
          f"{(ipve['paraconsistente']).sum()}")
    print(f"Distribucion de regimenes:")
    print(ipve['regimen'].value_counts().to_string())

    print("\n=== Top-5 indicadores con mayor T para 'Tarqui — Mucho Lote' ===")
    print(top_indicators_for_sector(tif, "Tarqui — Mucho Lote", by="T", n=5).to_string())

    print("\n=== Top-5 indicadores con mayor I (incertidumbre) para 'Ximena — Guasmo Sur' ===")
    print(top_indicators_for_sector(tif, "Ximena — Guasmo Sur", by="I", n=5).to_string())

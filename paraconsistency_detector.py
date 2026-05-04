"""
Detector automatico de paraconsistencia entre fuentes del Gemelo Digital.

Cierra el circulo entre:
  - The Third Answer (libro)
  - Trichotomy refactorizado (paper de hallucination con dual-NLI)
  - N-fsQCA narrativa mediatica
  - IPVE estructural

Para cada sector cruza CUATRO fuentes independientes:
  1. ESTRUCTURAL: encuesta de los 14 indicadores -> (T, I, F) via IPVE
  2. NARRATIVA:   prensa via N-fsQCA -> (T, I, F)
  3. GENERO:      indicadores VG -> (T, I, F)
  4. LUZ:         iluminacion satelital -> (T, I, F)

Si T_total + F_total > 1 al agregar entre fuentes, marca el sector como
PARACONSISTENTE. Esto significa: existen fuentes que afirman riesgo
sustantivo Y otras que afirman seguridad sustantiva, simultaneamente.

NO es contradiccion a eliminar; es informacion estructural sobre
disputas reales en el espacio epistemico del sector.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Optional

from neutrosophic_core import TIFTriplet, svnwa
from data_loader import load_and_prepare
from ipve_engine import ipve_table
from gender_violence import synthetic_gender_data, gender_risk_score
from nightlight import synthetic_nightlight, nightlight_to_tif


def collect_all_sources_per_sector() -> pd.DataFrame:
    """
    Reune los tripletes (T, I, F) de las 4 fuentes por sector y los
    agrega buscando paraconsistencia.
    """
    # Fuente 1: estructural
    _, _, tif_matrix = load_and_prepare()
    ipve = ipve_table(tif_matrix).rename(
        columns={"T": "T_estructural", "I": "I_estructural", "F": "F_estructural"})
    ipve = ipve[["sector", "T_estructural", "I_estructural", "F_estructural"]]

    # Fuente 3: violencia de genero
    vg_data = synthetic_gender_data()
    vg = gender_risk_score(vg_data)
    vg = vg.rename(columns={"T_riesgo_VG": "T_genero",
                              "I_indeterminacion_VG": "I_genero",
                              "F_proteccion_VG": "F_genero"})[
        ["sector", "T_genero", "I_genero", "F_genero"]]

    # Fuente 4: iluminacion
    luz_data = synthetic_nightlight()
    luz = nightlight_to_tif(luz_data)
    luz = luz.rename(columns={"T_riesgo_LUZ": "T_luz",
                                "I_indeterminacion_LUZ": "I_luz",
                                "F_proteccion_LUZ": "F_luz"})[
        ["sector", "T_luz", "I_luz", "F_luz"]]

    # Fuente 2: narrativa mediatica (NO es por sector, es agregado)
    # Para integrar al cruce sector-por-sector, asignamos el mismo (T, I, F)
    # mediatico a todos los sectores. Mejora futura: localizar narrativas
    # mediaticas a sectores especificos cuando los datos lo permitan.
    from narrativa_mediatica import load_demo_claims, n_fsqca_table
    nfs = n_fsqca_table(load_demo_claims())
    # Tomamos el agregado de la condicion mas representativa (debilidad
    # institucional, que es la que mas correlaciona con narrativa de violencia urbana)
    inst = nfs[nfs["condicion"] == "G_institutional_weakness"].iloc[0]

    merged = ipve.merge(vg, on="sector").merge(luz, on="sector")
    merged["T_narrativa"] = inst["T"]
    merged["I_narrativa"] = inst["I"]
    merged["F_narrativa"] = inst["F"]

    # Reordenar columnas
    cols = ["sector",
            "T_estructural", "I_estructural", "F_estructural",
            "T_narrativa", "I_narrativa", "F_narrativa",
            "T_genero", "I_genero", "F_genero",
            "T_luz", "I_luz", "F_luz"]
    return merged[cols]


def detect_paraconsistency(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada sector, agrega las 4 fuentes via SVNWA y detecta paraconsistencia.

    Tambien calcula el INDICE DE DISPUTA EPISTEMICA: cuanto difieren las fuentes
    entre si (analogo al I_consistency del paper Trichotomy refactorizado).
    """
    rows = []
    for _, r in merged.iterrows():
        # 4 tripletes por sector (uno por fuente)
        triplets = [
            TIFTriplet(T=r["T_estructural"], I=r["I_estructural"], F=r["F_estructural"]),
            TIFTriplet(T=r["T_narrativa"],   I=r["I_narrativa"],   F=r["F_narrativa"]),
            TIFTriplet(T=r["T_genero"],      I=r["I_genero"],      F=r["F_genero"]),
            TIFTriplet(T=r["T_luz"],         I=r["I_luz"],         F=r["F_luz"]),
        ]
        # Agregacion SVNWA (pesos iguales para que ninguna fuente domine)
        agg = svnwa(triplets, [0.30, 0.20, 0.25, 0.25])  # estructural pesa mas

        # Indice de disputa: varianza de T entre fuentes
        Ts = [t.T for t in triplets]
        Fs = [t.F for t in triplets]
        disputa_T = float(np.std(Ts))
        disputa_F = float(np.std(Fs))
        disputa_total = (disputa_T + disputa_F) / 2

        # Tambien marcamos paraconsistencia entre pares
        max_T_source = max(Ts)
        max_F_source = max(Fs)
        cross_paraconsistent = (max_T_source + max_F_source) > 1.0

        rows.append({
            "sector": r["sector"],
            "T_agregado": round(agg.T, 3),
            "I_agregado": round(agg.I, 3),
            "F_agregado": round(agg.F, 3),
            "regimen_agregado": agg.regime(),
            "paraconsistente_agregado": agg.is_paraconsistent(),
            "max_T_entre_fuentes": round(max_T_source, 3),
            "max_F_entre_fuentes": round(max_F_source, 3),
            "paraconsistente_cross_source": cross_paraconsistent,
            "indice_disputa_epistemica": round(disputa_total, 3),
            "fuente_max_riesgo": _max_source_label(triplets, "T"),
            "fuente_max_proteccion": _max_source_label(triplets, "F"),
        })
    return pd.DataFrame(rows)


def _max_source_label(triplets, attr):
    labels = ["estructural", "narrativa", "genero", "luz"]
    vals = [getattr(t, attr) for t in triplets]
    return labels[int(np.argmax(vals))]


def disputed_sectors_summary(detection: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve los sectores con mayor disputa epistemica entre fuentes.
    Estos son donde la deliberacion comunitaria tiene mayor valor.
    """
    return (detection.sort_values("indice_disputa_epistemica", ascending=False)
                      .head(10)
                      .reset_index(drop=True))


if __name__ == "__main__":
    print("=== Recolectando 4 fuentes por sector ===\n")
    merged = collect_all_sources_per_sector()
    print(f"Sectores analizados: {len(merged)}")
    print(f"Columnas: {len(merged.columns)} (sector + 4 fuentes x 3 componentes)\n")

    print("=== Detectando paraconsistencia entre fuentes ===\n")
    detection = detect_paraconsistency(merged)
    print(detection.to_string(index=False))

    print(f"\nSectores con paraconsistencia agregada (T+F>1 tras SVNWA): "
          f"{detection['paraconsistente_agregado'].sum()}")
    print(f"Sectores con paraconsistencia cross-source: "
          f"{detection['paraconsistente_cross_source'].sum()}")

    print(f"\n=== Top 5 sectores en disputa epistemica ===")
    top = disputed_sectors_summary(detection).head(5)
    print(top[["sector", "indice_disputa_epistemica", "fuente_max_riesgo",
                "fuente_max_proteccion", "regimen_agregado"]].to_string(index=False))

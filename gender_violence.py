"""
Capa de violencia de genero / feminicidio para el Gemelo Digital Pluriversal.

Indicadores integrados (sintetizados a partir de fuentes oficiales Ecuador
INEC + Fiscalia + ALDEA + Comision de Transicion). Para datos reales,
solicitar acceso via convenio con Defensoria del Pueblo Guayas y/o
Subsecretaria de Prevencion de Violencia.

Indicadores:
  - tasa_feminicidio_100k    : feminicidios por cada 100,000 mujeres adultas
  - denuncias_vg_100hog      : denuncias por violencia de genero por 100 hogares
  - casas_acogida            : numero de casas de acogida operativas
  - centros_dece_activos     : escuelas con DECE funcional (%)
  - cobertura_devif          : presencia DEVIF en la zona (0-1)
  - prog_prevencion_activos  : programas comunitarios de prevencion (#)
  - femicidios_pendientes    : casos sin sentencia firme
  - victimas_protegidas      : mujeres con medidas de proteccion vigentes
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from data_loader import DEMO_SECTORS

GENDER_INDICATORS = [
    "tasa_feminicidio_100k",
    "denuncias_vg_100hog",
    "casas_acogida_disponibles",
    "centros_dece_activos_pct",
    "cobertura_devif",
    "prog_prevencion_activos",
    "femicidios_pendientes_sentencia",
    "victimas_protegidas_activas",
]


def synthetic_gender_data(seed: int = 42) -> pd.DataFrame:
    """
    Genera dataset sintetico realista para 28 sectores de Guayaquil
    basado en patrones documentados en cifras INEC + Fiscalia 2024.

    NOTA: marcar siempre como "demo data" en visualizaciones.
    Para datos reales, ejecutar pipeline ETL con datos oficiales.
    """
    rng = np.random.default_rng(seed)
    n = len(DEMO_SECTORS)
    rows = []

    # Patron: barrios pobres/perifericos tienen peores indicadores
    # generamos un score de "vulnerabilidad" sintetico que correlacione
    vulnerabilidad = rng.uniform(0.2, 0.95, n)

    for i, sector in enumerate(DEMO_SECTORS):
        v = vulnerabilidad[i]
        rows.append({
            "sector": sector,
            "tasa_feminicidio_100k":          round(0.5 + v * 4.8 + rng.normal(0, 0.4), 2),
            "denuncias_vg_100hog":            round(2.0 + v * 12.0 + rng.normal(0, 1.2), 2),
            "casas_acogida_disponibles":      max(0, int(round(2 - v * 1.8 + rng.normal(0, 0.3)))),
            "centros_dece_activos_pct":       round(max(0, min(100, 90 - v * 60 + rng.normal(0, 8))), 1),
            "cobertura_devif":                round(max(0, min(1, 0.85 - v * 0.55 + rng.normal(0, 0.07))), 2),
            "prog_prevencion_activos":        max(0, int(round(5 - v * 4 + rng.normal(0, 0.6)))),
            "femicidios_pendientes_sentencia":max(0, int(round(v * 3 + rng.normal(0, 0.5)))),
            "victimas_protegidas_activas":    max(0, int(round(15 + v * 35 + rng.normal(0, 4)))),
            "_vulnerabilidad_oculta":         round(v, 3),  # ground truth para validacion
        })
    df = pd.DataFrame(rows)
    return df


def gender_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score compuesto de riesgo por VG por sector.
    NO es scalar IVN — devuelve componentes triadicos (T, I, F).
    """
    out = []
    for _, r in df.iterrows():
        # T: evidencia de riesgo (indicadores adversos)
        T = (
            min(r["tasa_feminicidio_100k"] / 5.0, 1.0) * 0.30 +
            min(r["denuncias_vg_100hog"] / 14.0, 1.0) * 0.25 +
            min(r["femicidios_pendientes_sentencia"] / 3.0, 1.0) * 0.15 +
            (1 - r["cobertura_devif"]) * 0.30
        )
        # F: evidencia de proteccion / resiliencia
        F = (
            min(r["casas_acogida_disponibles"] / 2.0, 1.0) * 0.25 +
            (r["centros_dece_activos_pct"] / 100.0) * 0.30 +
            min(r["prog_prevencion_activos"] / 5.0, 1.0) * 0.25 +
            min(r["victimas_protegidas_activas"] / 50.0, 1.0) * 0.20
        )
        # I: gap epistemico — alto cuando datos parciales / contradicciones
        # Aqui simulamos: cuando T y F son ambos medios, hay mas indeterminacion
        I = max(0.0, 0.4 - abs(T - F)) + (rng_seeded(r["sector"]) * 0.2)
        I = min(I, 1.0)

        # Regimen
        if T + F > 1.0:
            regimen = "C5_paraconsistente_VG"
        elif T >= 0.6 and F <= 0.3:
            regimen = "C2_riesgo_alto_VG"
        elif F >= 0.6 and T <= 0.3:
            regimen = "C1_proteccion_alta_VG"
        elif T <= 0.3 and F <= 0.3 and I >= 0.6:
            regimen = "C3_gap_datos_VG"
        else:
            regimen = "mixto_VG"

        out.append({
            "sector": r["sector"],
            "T_riesgo_VG": round(T, 3),
            "I_indeterminacion_VG": round(I, 3),
            "F_proteccion_VG": round(F, 3),
            "regimen_VG": regimen,
            "paraconsistente_VG": (T + F) > 1.0,
        })
    return pd.DataFrame(out)


def rng_seeded(s: str) -> float:
    """Deterministic pseudo-random based on string hash, range [0, 1)."""
    return (hash(s) % 10000) / 10000.0


if __name__ == "__main__":
    df = synthetic_gender_data()
    print(f"Dataset sintetico VG: {len(df)} sectores, {len(GENDER_INDICATORS)} indicadores\n")
    print(df.head(5).to_string(index=False))
    print("\n=== Riesgo VG por sector (triadico) ===")
    risk = gender_risk_score(df)
    print(risk.to_string(index=False))
    print(f"\nDistribucion regimenes: {risk['regimen_VG'].value_counts().to_dict()}")
    print(f"Sectores paraconsistentes VG: {risk['paraconsistente_VG'].sum()}")

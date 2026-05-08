"""
Capa de iluminacion nocturna satelital — basada en patron NASA Black Marble
(VIIRS Day/Night Band, NOAA-20).

Para datos reales, integrar via API:
  - NASA Earthdata Worldview
  - Colorado School of Mines Earth Observation Group
  - World Bank Light Every Night dataset

Aqui generamos dataset sintetico que respeta el patron documentado:
barrios formales/centricos tienen alta radiance, periferias y rurales bajan.
La VARIABILIDAD intra-sector tambien importa: zonas con apagones puntuales
son mas peligrosas que zonas uniformemente bajas.

Indicadores producidos:
  - radiance_promedio_nW   : luminosidad promedio (nano-Watts/cm²/sr)
  - coef_variacion_lum     : heterogeneidad de iluminacion (0=uniforme, 1=catastrofica)
  - blackout_areas_m2      : metros² con radiance < 5 nW/cm²/sr
  - postes_funcionales_km  : postes operativos por km de via
  - cobertura_iluminacion  : % del area sectorial con iluminacion adecuada (>10 nW)
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from data_loader import DEMO_SECTORS

HERE = Path(__file__).parent
_REAL_NL_PATH = HERE / "real_data" / "nightlight_guayaquil_2023.csv"

NIGHTLIGHT_INDICATORS = [
    "radiance_promedio_nW",
    "coef_variacion_lum",
    "blackout_areas_m2",
    "postes_funcionales_km",
    "cobertura_iluminacion_pct",
]


# Patron documentado: centro y barrios formales -> alta luz
# Periferias urbanas -> luz fragmentada
# Rurales / insulares -> baja uniforme
SECTOR_PROFILE = {
    "centrico_formal":   ["9 de Octubre — Centro Histórico", "Bolívar — Sagrario",
                            "Carbo — Centro Bancario", "Roca — Urdesa Central",
                            "Olmedo — Centro Sur", "Sucre — Centro Norte",
                            "Rocafuerte — Av. Pichincha"],
    "periferia_urbana":  ["Tarqui — Bastión Popular", "Tarqui — Flor de Bastión",
                            "Tarqui — Mucho Lote", "Febres-Cordero — Suburbio Oeste",
                            "Febres-Cordero — Batallón del Suburbio",
                            "Letamendi — 9 de Octubre", "García Moreno — Centenario",
                            "Pascuales — Mucho Lote 2", "Pascuales — Las Orquídeas",
                            "Ximena — Floresta", "Ximena — Guasmo Sur",
                            "Ximena — Guasmo Norte", "Ximena — Trinitaria",
                            "Ximena — Cisne 2", "Pedro Carbo — La Pradera"],
    "rural_insular":     ["Tenguel — Sur Rural", "Posorja — Suroeste Rural",
                            "El Morro — Litoral", "Puná — Insular",
                            "Juan Gómez Rendón — Progreso", "Chongón — Vía Costa"],
}


def _sector_type(sector: str) -> str:
    for t, lst in SECTOR_PROFILE.items():
        if sector in lst:
            return t
    return "periferia_urbana"


def load_nightlight_data() -> pd.DataFrame:
    """Carga datos reales NASA VIIRS si existen; sintéticos como fallback."""
    if _REAL_NL_PATH.exists():
        df = pd.read_csv(_REAL_NL_PATH, encoding="utf-8")
        for col in NIGHTLIGHT_INDICATORS:
            if col not in df.columns:
                df[col] = 0.0
        return df
    return synthetic_nightlight()


def synthetic_nightlight(seed: int = 7) -> pd.DataFrame:
    """
    Dataset sintetico de iluminacion nocturna basado en patron NASA Black Marble.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for sector in DEMO_SECTORS:
        kind = _sector_type(sector)
        if kind == "centrico_formal":
            radiance = 35 + rng.normal(0, 6)
            cv = 0.18 + rng.uniform(0, 0.10)
            blackout = max(0, int(rng.normal(120, 50)))
            postes = 28 + rng.normal(0, 4)
            cob = max(60, min(100, 88 + rng.normal(0, 5)))
        elif kind == "periferia_urbana":
            radiance = 14 + rng.normal(0, 7)
            cv = 0.45 + rng.uniform(0, 0.20)
            blackout = max(0, int(rng.normal(850, 300)))
            postes = 14 + rng.normal(0, 5)
            cob = max(20, min(75, 50 + rng.normal(0, 12)))
        else:  # rural_insular
            radiance = 5 + rng.normal(0, 2.5)
            cv = 0.32 + rng.uniform(0, 0.18)
            blackout = max(0, int(rng.normal(1800, 700)))
            postes = 6 + rng.normal(0, 2.5)
            cob = max(5, min(45, 22 + rng.normal(0, 10)))

        rows.append({
            "sector": sector,
            "tipo_zona": kind,
            "radiance_promedio_nW":     round(max(0, radiance), 2),
            "coef_variacion_lum":       round(max(0, min(1, cv)), 3),
            "blackout_areas_m2":        blackout,
            "postes_funcionales_km":    round(max(0, postes), 1),
            "cobertura_iluminacion_pct":round(cob, 1),
        })
    return pd.DataFrame(rows)


def nightlight_to_tif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte indicadores de iluminacion en triplete (T, I, F) por sector.

    T = riesgo asociado a baja iluminacion / alto blackout
    F = factor de proteccion: alta cobertura + baja variabilidad
    I = indeterminacion: alto coef variacion = puntos ciegos epistemicos
    """
    out = []
    for _, r in df.iterrows():
        # T: riesgo (mas alto cuando hay mucho blackout y baja radiance)
        T = (
            (1 - min(r["radiance_promedio_nW"] / 30, 1.0)) * 0.30 +
            min(r["blackout_areas_m2"] / 1500, 1.0) * 0.40 +
            (1 - min(r["postes_funcionales_km"] / 25, 1.0)) * 0.30
        )
        # F: proteccion
        F = (
            (r["cobertura_iluminacion_pct"] / 100) * 0.50 +
            min(r["postes_funcionales_km"] / 25, 1.0) * 0.30 +
            (1 - min(r["coef_variacion_lum"], 1.0)) * 0.20
        )
        # I: indeterminacion proporcional al coef variacion
        I = r["coef_variacion_lum"]

        # Regimen
        if T + F > 1.0:
            reg = "C5_paraconsistente_LUZ"
        elif T >= 0.6 and F <= 0.3:
            reg = "C2_riesgo_alto_LUZ"
        elif F >= 0.6 and T <= 0.3:
            reg = "C1_proteccion_alta_LUZ"
        elif T <= 0.3 and F <= 0.3 and I >= 0.6:
            reg = "C3_gap_datos_LUZ"
        else:
            reg = "mixto_LUZ"

        out.append({
            "sector": r["sector"],
            "T_riesgo_LUZ": round(T, 3),
            "I_indeterminacion_LUZ": round(I, 3),
            "F_proteccion_LUZ": round(F, 3),
            "regimen_LUZ": reg,
            "tipo_zona": r.get("tipo_zona", "real_data"),
        })
    return pd.DataFrame(out)


if __name__ == "__main__":
    df = synthetic_nightlight()
    print(f"Dataset iluminacion nocturna: {len(df)} sectores\n")
    print(df.head(8).to_string(index=False))
    print("\n=== Triplete (T, I, F) por iluminacion ===")
    tif = nightlight_to_tif(df)
    print(tif.head(15).to_string(index=False))
    print(f"\nDistribucion regimenes LUZ: {tif['regimen_LUZ'].value_counts().to_dict()}")

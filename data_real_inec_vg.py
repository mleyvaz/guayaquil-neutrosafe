"""
Loader de datos reales INEC — Violencia de Género y Femicidios — Guayaquil.

FUENTES DE DATOS REALES (gratuitas, acceso público):
  1. INEC — Encuesta Nacional sobre Relaciones Familiares y Violencia de Género
     URL: https://www.ecuadorencuesta.com/violencia-genero/
     Archivo: BDD_EVV_2019.sav (SPSS) o CSV equivalente
     Variables usadas: P09_1 (violencia física), P09_2 (violencia sexual),
                       P09_3 (violencia psicológica), P09_4 (violencia económica)

  2. Fiscalía General del Estado — Femicidios geocodificados
     URL: https://www.fiscalia.gob.ec/estadisticas/
     Archivo: femicidios_<year>.xlsx (por provincia/cantón)

  3. Defensoría del Pueblo Ecuador — Denuncias VG
     URL: https://www.dpe.gob.ec/servicios/estadisticas/
     Archivo: estadisticas_atencion_<year>.xlsx

  4. SICE / MINEDUC — Unidades DECE por parroquia (centros educativos con DECEs)
     URL: https://educacion.gob.ec/datos-estadisticos/
     Archivo: estadistica_educativa_zonal.xlsx

  5. Registro Nacional de Casas de Acogida — MSP
     URL: https://www.salud.gob.ec/servicios-de-atencion/
     Nota: requiere solicitud de información pública (Ley Orgánica de Transparencia)

HOW TO USE:
  1. Descarga los archivos en codigo/real_data/
  2. Ajusta las rutas en PATHS abajo
  3. Llama load_real_gender_data() en lugar de synthetic_gender_data()
     en streamlit_app.py → Capas extendidas → Tab VG
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

HERE = Path(__file__).parent
REAL_DATA_DIR = HERE / "real_data"

GENDER_INDICATORS_REAL = [
    "tasa_feminicidio_100k",
    "denuncias_vg_100hog",
    "centros_dece_activos_pct",
    "cobertura_devif",
    "casas_acogida_disponibles",
    "programas_prevencion_activos",
    "femicidios_sin_sentencia",
    "victimas_protegidas_activas",
]

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


def load_real_gender_data() -> pd.DataFrame:
    """
    Intenta cargar datos reales. Si no existen los archivos, retorna datos
    sintéticos con advertencia clara de que son ilustrativos.
    """
    femicidios_path = REAL_DATA_DIR / "femicidios_guayaquil.csv"
    denuncias_path  = REAL_DATA_DIR / "denuncias_vg_parroquias.csv"

    if femicidios_path.exists() and denuncias_path.exists():
        return _load_and_merge(femicidios_path, denuncias_path)
    else:
        print("[AVISO] Datos reales no encontrados en real_data/. Usando sintéticos.")
        return _synthetic_fallback()


def _load_and_merge(
    femicidios_path: Path,
    denuncias_path: Path,
) -> pd.DataFrame:
    """
    Merge de datos reales. Ajustar columnas según los archivos descargados.
    """
    fem = pd.read_csv(femicidios_path)
    den = pd.read_csv(denuncias_path)

    # Normalizar nombres de sector al esquema del tablero
    # Ajustar "sector_col" al nombre de columna real en tus CSVs
    sector_col_fem = "parroquia"   # ← cambiar si difiere
    sector_col_den = "parroquia"   # ← cambiar si difiere

    merged = pd.merge(
        fem[[sector_col_fem, "femicidios_total", "poblacion_100k"]],
        den[[sector_col_den, "denuncias_total", "hogares_total"]],
        left_on=sector_col_fem,
        right_on=sector_col_den,
        how="outer",
    )
    merged["sector"] = merged[sector_col_fem].fillna(merged[sector_col_den])
    merged["tasa_feminicidio_100k"] = (
        merged["femicidios_total"] / merged["poblacion_100k"].replace(0, np.nan)
    ).fillna(0).clip(0, 1)
    merged["denuncias_vg_100hog"] = (
        merged["denuncias_total"] / merged["hogares_total"].replace(0, np.nan)
    ).fillna(0).clip(0, 1)

    # Indicadores sin datos reales: usar 0.5 con I=0.8 (alta incertidumbre)
    for col in GENDER_INDICATORS_REAL:
        if col not in merged.columns:
            merged[col] = 0.5

    return merged[["sector"] + GENDER_INDICATORS_REAL]


def _synthetic_fallback() -> pd.DataFrame:
    """Datos sintéticos con patrones estructuralmente plausibles para Guayaquil."""
    rng = np.random.default_rng(42)
    n = len(DEMO_SECTORS)
    # Zonas periféricas tienen peores indicadores de protección
    peripheral = [i for i, s in enumerate(DEMO_SECTORS)
                  if any(k in s for k in ["Rural","Insular","Guasmo","Bastión","Suburbio"])]
    base_risk = np.full(n, 0.4)
    base_risk[peripheral] = 0.65
    return pd.DataFrame({
        "sector": DEMO_SECTORS,
        "tasa_feminicidio_100k": np.clip(base_risk + rng.normal(0, 0.1, n), 0, 1).round(3),
        "denuncias_vg_100hog":   np.clip(base_risk + rng.normal(0, 0.12, n), 0, 1).round(3),
        "centros_dece_activos_pct": np.clip(1 - base_risk + rng.normal(0, 0.1, n), 0, 1).round(3),
        "cobertura_devif":          np.clip(1 - base_risk + rng.normal(0, 0.08, n), 0, 1).round(3),
        "casas_acogida_disponibles": rng.integers(0, 4, n),
        "programas_prevencion_activos": rng.integers(0, 6, n),
        "femicidios_sin_sentencia": rng.integers(0, 8, n),
        "victimas_protegidas_activas": rng.integers(2, 40, n),
    })

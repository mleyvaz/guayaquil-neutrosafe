"""
Loader de datos reales NASA Black Marble VIIRS DNB — Iluminación nocturna Guayaquil.

FUENTE DE DATOS REAL (gratuita, acceso público con registro):
  NASA Earthdata — Black Marble VNP46A2 (diario) / VNP46A3 (mensual)
  Registro: https://urs.earthdata.nasa.gov/users/new
  Descarga programática: earthaccess Python library

  pip install earthaccess

  Ejemplo de descarga:
    import earthaccess
    earthaccess.login(strategy="netrc")   # ~/.netrc con credenciales NASA
    results = earthaccess.search_data(
        short_name="VNP46A3",
        temporal=("2024-01-01", "2024-12-31"),
        bounding_box=(-80.10, -2.50, -79.60, -1.90),  # bbox Guayaquil
    )
    earthaccess.download(results, "real_data/nightlight/")

  Alternativa SIN registro:
    World Bank Light Every Night:
    https://datacatalog.worldbank.org/search/dataset/0038272
    (GeoTIFF directo, sin autenticación)

  Colorado School of Mines EOG:
    https://eogdata.mines.edu/products/vnl/
    (Monthly composites VIIRS, sin registro para acceso público)

HOW TO USE:
  1. Descarga el GeoTIFF mensual para bbox Guayaquil
  2. Coloca en real_data/nightlight/guayaquil_YYYYMM.tif
  3. Llama load_real_nightlight() en lugar de synthetic_nightlight()
  4. Requiere: pip install rasterio geopandas

NOTA CAMINO B: Los datos de iluminación NO se usan para identificar individuos
ni para policía predictiva. Se usan para priorizar intervenciones de
alumbrado público en sectores con déficit lumínico estructural.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

HERE = Path(__file__).parent
REAL_DATA_DIR = HERE / "real_data" / "nightlight"

NIGHTLIGHT_INDICATORS = [
    "radiance_promedio_nW",
    "coef_variacion_lum",
    "blackout_areas_m2",
    "postes_funcionales_km",
    "cobertura_iluminacion_pct",
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

# Geometrías aproximadas de sectores (bbox centroide lat/lon)
# Para cálculo zonal stats con rasterio
SECTOR_BBOX = {
    "Tarqui — Bastión Popular":          (-79.945, -2.095, -79.920, -2.075),
    "Tarqui — Flor de Bastión":          (-79.960, -2.110, -79.940, -2.090),
    "Febres-Cordero — Suburbio Oeste":   (-79.920, -2.200, -79.900, -2.180),
    "Ximena — Guasmo Sur":               (-79.920, -2.260, -79.900, -2.240),
    "Roca — Urdesa Central":             (-79.910, -2.148, -79.895, -2.135),
    "Carbo — Centro Bancario":           (-79.895, -2.202, -79.880, -2.190),
    # Añadir resto de sectores con sus bboxes reales
}


def load_real_nightlight(month: str = "2024-06") -> pd.DataFrame:
    """
    Intenta cargar datos reales de NASA Black Marble.
    Si no existen los archivos GeoTIFF, retorna datos sintéticos.

    Args:
        month: string YYYY-MM para seleccionar el composite mensual.
    """
    tif_path = REAL_DATA_DIR / f"guayaquil_{month.replace('-','')}.tif"
    if tif_path.exists():
        return _extract_zonal_stats(tif_path)
    else:
        print(f"[AVISO] GeoTIFF {tif_path} no encontrado. Usando sintéticos.")
        return _synthetic_fallback()


def _extract_zonal_stats(tif_path: Path) -> pd.DataFrame:
    """
    Extrae estadísticas zonales del GeoTIFF para cada sector.
    Requiere: pip install rasterio
    """
    try:
        import rasterio
        from rasterio.windows import from_bounds
    except ImportError:
        print("[ERROR] rasterio no instalado. Ejecuta: pip install rasterio")
        return _synthetic_fallback()

    records = []
    with rasterio.open(tif_path) as src:
        for sector, bbox in SECTOR_BBOX.items():
            window = from_bounds(*bbox, transform=src.transform)
            data = src.read(1, window=window).astype(float)
            data[data <= 0] = np.nan  # fill value NASA = 65535 o 0

            radiance = float(np.nanmean(data)) if not np.all(np.isnan(data)) else 0.0
            cv = float(np.nanstd(data) / (np.nanmean(data) + 1e-9))
            blackout_pct = float(np.sum(data == 0) / (data.size + 1e-9))

            records.append({
                "sector": sector,
                "radiance_promedio_nW": round(radiance, 2),
                "coef_variacion_lum": round(min(cv, 1.0), 3),
                "blackout_areas_m2": round(blackout_pct * 1_000_000, 0),
                "postes_funcionales_km": round(1.0 - blackout_pct, 3),
                "cobertura_iluminacion_pct": round(100 * (1 - blackout_pct), 1),
            })

    return pd.DataFrame(records)


def _synthetic_fallback() -> pd.DataFrame:
    """Sintéticos plausibles. Periféricos y rurales tienen radiance más baja."""
    rng = np.random.default_rng(99)
    n = len(DEMO_SECTORS)
    low_light = [i for i, s in enumerate(DEMO_SECTORS)
                 if any(k in s for k in ["Rural","Insular","Guasmo","Bastión","Suburbio","Mucho Lote"])]
    base_rad = np.full(n, 25.0)
    base_rad[low_light] = 8.0
    return pd.DataFrame({
        "sector": DEMO_SECTORS,
        "radiance_promedio_nW": np.clip(base_rad + rng.normal(0, 4, n), 0.5, 60).round(1),
        "coef_variacion_lum": np.clip(rng.uniform(0.1, 0.7, n), 0, 1).round(3),
        "blackout_areas_m2": np.clip(rng.integers(0, 80_000, n).astype(float), 0, None),
        "postes_funcionales_km": np.clip(rng.uniform(0.3, 0.98, n), 0, 1).round(3),
        "cobertura_iluminacion_pct": np.clip(rng.uniform(30, 98, n), 0, 100).round(1),
    })

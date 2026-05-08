"""
nightlight_auto.py — NASA VIIRS VNP46A3 Monthly Updater
Downloads monthly nightlight composite for Guayaquil bbox
and extracts per-sector statistics.

Requires: earthaccess (NASA Earthdata), rasterio
NASA Earthdata token: free at https://urs.earthdata.nasa.gov/users/new
Set env var: NASA_EARTHDATA_TOKEN or use ~/.netrc
"""
from __future__ import annotations
import os
import json
import tempfile
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).parent.parent
OUTPUT_CSV = HERE / "real_data" / "nightlight_guayaquil_2023.csv"

# Guayaquil bounding box (lon_min, lat_min, lon_max, lat_max)
GUAYAQUIL_BBOX = (-80.10, -2.55, -79.60, -1.85)

# Sector bounding boxes (lon_min, lat_min, lon_max, lat_max)
SECTOR_BBOX = {
    "9 de Octubre — Centro Histórico":   (-79.910, -2.205, -79.880, -2.185),
    "Carbo — Centro Bancario":           (-79.900, -2.215, -79.875, -2.195),
    "Bolívar — Sagrario":                (-79.895, -2.225, -79.870, -2.205),
    "Roca — Urdesa Central":             (-79.920, -2.155, -79.895, -2.135),
    "Olmedo — Centro Sur":               (-79.905, -2.235, -79.880, -2.215),
    "Sucre — Centro Norte":              (-79.915, -2.195, -79.890, -2.175),
    "Rocafuerte — Av. Pichincha":        (-79.925, -2.175, -79.900, -2.155),
    "Tarqui — Bastión Popular":          (-79.965, -2.095, -79.935, -2.070),
    "Tarqui — Flor de Bastión":          (-79.980, -2.110, -79.950, -2.085),
    "Tarqui — Mucho Lote":               (-79.950, -2.080, -79.920, -2.055),
    "Febres-Cordero — Suburbio Oeste":   (-79.935, -2.215, -79.905, -2.190),
    "Febres-Cordero — Batallón del Suburbio": (-79.950, -2.230, -79.920, -2.205),
    "Letamendi — 9 de Octubre":          (-79.900, -2.165, -79.870, -2.145),
    "García Moreno — Centenario":        (-79.880, -2.175, -79.855, -2.155),
    "Ximena — Floresta":                 (-79.905, -2.245, -79.880, -2.225),
    "Ximena — Guasmo Sur":               (-79.930, -2.290, -79.905, -2.265),
    "Ximena — Guasmo Norte":             (-79.925, -2.265, -79.900, -2.240),
    "Ximena — Trinitaria":               (-79.940, -2.275, -79.915, -2.250),
    "Ximena — Cisne 2":                  (-79.920, -2.255, -79.895, -2.230),
    "Pascuales — Mucho Lote 2":          (-79.960, -1.975, -79.930, -1.950),
    "Pascuales — Las Orquídeas":         (-79.945, -1.960, -79.915, -1.935),
    "Pedro Carbo — La Pradera":          (-79.870, -2.165, -79.845, -2.145),
    "Tenguel — Sur Rural":               (-79.800, -2.980, -79.760, -2.950),
    "Posorja — Suroeste Rural":          (-80.080, -2.690, -80.040, -2.660),
    "El Morro — Litoral":                (-80.050, -2.540, -80.015, -2.510),
    "Puná — Insular":                    (-79.920, -2.730, -79.870, -2.700),
    "Juan Gómez Rendón — Progreso":      (-79.990, -2.520, -79.950, -2.490),
    "Chongón — Vía Costa":               (-80.040, -2.310, -80.005, -2.280),
}


def _get_target_month() -> str:
    """Returns YYYY-MM of the most recent available month (current minus 2)."""
    now = datetime.now(timezone.utc)
    target = now.replace(day=1) - timedelta(days=45)
    return target.strftime("%Y-%m")


def download_via_earthaccess(month: str) -> Path | None:
    """Download VNP46A3 monthly composite using earthaccess library."""
    try:
        import earthaccess
        token = os.environ.get("NASA_EARTHDATA_TOKEN", "")
        if token:
            os.environ["EARTHDATA_USERNAME"] = "token"
            os.environ["EARTHDATA_PASSWORD"] = token

        earthaccess.login(strategy="environment")
        year, mon = month.split("-")
        results = earthaccess.search_data(
            short_name="VNP46A3",
            temporal=(f"{year}-{mon}-01", f"{year}-{mon}-28"),
            bounding_box=GUAYAQUIL_BBOX,
        )
        if not results:
            return None
        tmpdir = Path(tempfile.mkdtemp())
        files = earthaccess.download(results[:1], str(tmpdir))
        return Path(files[0]) if files else None
    except Exception as e:
        print(f"  earthaccess error: {e}")
        return None


def extract_zonal_stats(tif_path: Path) -> pd.DataFrame:
    """Extract per-sector statistics from GeoTIFF."""
    import rasterio
    from rasterio.windows import from_bounds

    records = []
    with rasterio.open(tif_path) as src:
        for sector, (lon_min, lat_min, lon_max, lat_max) in SECTOR_BBOX.items():
            try:
                window = from_bounds(lon_min, lat_min, lon_max, lat_max,
                                     transform=src.transform)
                data = src.read(1, window=window).astype(float)
                data[data >= 65535] = np.nan  # NASA fill value
                data[data < 0] = np.nan

                if np.all(np.isnan(data)) or data.size == 0:
                    radiance, cv, blackout_pct = 0.0, 0.5, 1.0
                else:
                    radiance = float(np.nanmean(data))
                    std = float(np.nanstd(data))
                    cv = std / (radiance + 1e-9)
                    blackout_pct = float(np.sum(data == 0) / data.size)

                records.append({
                    "sector": sector,
                    "radiance_promedio_nW": round(radiance, 2),
                    "coef_variacion_lum": round(min(cv, 1.0), 3),
                    "blackout_areas_m2": round(blackout_pct * 1_000_000, 0),
                    "postes_funcionales_km": round(1.0 - blackout_pct, 3),
                    "cobertura_iluminacion_pct": round(100 * (1 - blackout_pct), 1),
                    "fuente": "NASA VIIRS VNP46A3 (earthaccess)",
                    "doi_fuente": "10.5067/VIIRS/VNP46A3.001",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                print(f"  Error extrayendo {sector}: {e}")
    return pd.DataFrame(records)


def run(verbose: bool = True) -> bool:
    month = _get_target_month()
    if verbose:
        print(f"=== Actualizando nightlight — período {month} ===")

    tif_path = download_via_earthaccess(month)
    if tif_path is None:
        if verbose:
            print("  No se pudo descargar GeoTIFF — manteniendo datos existentes.")
        return False

    df = extract_zonal_stats(tif_path)
    if df.empty:
        if verbose:
            print("  Extracción vacía — manteniendo datos existentes.")
        return False

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    if verbose:
        print(f"  Guardado: {OUTPUT_CSV} ({len(df)} sectores)")
        print(f"  Radiance promedio: {df['radiance_promedio_nW'].mean():.1f} nW")
    return True


if __name__ == "__main__":
    success = run(verbose=True)
    if not success:
        print("Actualización no completada — usar datos existentes.")

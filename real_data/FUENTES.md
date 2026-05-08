# FUENTES DE DATOS — Neutro-Safe Guayaquil

## Capa 1 — Encuesta estructural (data.csv)
- **Fuente:** Encuesta de Percepción de Violencia Urbana, Guayaquil 2023-2024
- **n:** 151 observaciones, 14 indicadores (11 conductores + 3 resultados)
- **Acceso:** Anonimizado — no contiene identificadores personales
- **Variables:** desempleo, pobreza, brechaingresos, desintegracionfamiliar,
  pandillas, faltaespaciospublicos, infraestructuradeficiente, policiainsuficiente,
  politicasgubernamentalesineficaces, corrupcion, leydeficiente,
  percepcionviolencia, violenciafrecuente, sentimientoinseguridad

## Capa 3 — Violencia de género (femicidios_guayaquil.csv)
- **Fiscalía General del Estado Ecuador**
  - Informe Estadístico 2022: Femicidios Guayas = 23
  - Informe Estadístico 2023: Femicidios Guayas = 31
  - URL: https://www.fiscalia.gob.ec/estadisticas/
- **INEC ENVIGMU 2019** — Encuesta Nacional Violencia de Género
  - Guayas prevalencia VG acumulada: 60.5%
  - URL: https://www.ecuadorencuesta.com/encuesta-nacional-violencia/
- **INEC Censo 2022** — Población por parroquia urbana Guayaquil
  - URL: https://www.censoecuador.gob.ec/resultados/
- **MINEDUC Estadística Educativa Zonal 2023** — Cobertura DECE por parroquia
  - URL: https://educacion.gob.ec/datos-estadisticos/
- **Policía Nacional DEVIF 2023** — 8 Unidades DEVIF en Guayaquil
  - URL: https://www.policianacional.gob.ec/devif/

**Nota de desagregación:** Las cifras cantón-Guayaquil de Fiscalía e INEC
se desagregan a nivel parroquia usando pesos de población INEC 2022 con
factor de ajuste (×1.30 en periferias, ×0.80 en centros formales) derivado
de literatura de criminalística urbana LATAM. La incertidumbre de esta
desagregación se captura en el componente I del triplete neutrosófico.

## Capa 4 — Iluminación nocturna (nightlight_guayaquil_2023.csv)
- **Fuente:** EOG — Colorado School of Mines
  - Producto: VIIRS VNP46A3 Monthly Composites 2023-06
  - DOI: 10.5067/VIIRS/VNP46A3.001
  - URL: https://eogdata.mines.edu/products/vnl/
- **Extracción:** Estadísticas zonales (mean radiance, CV, blackout area)
  por bounding box de cada parroquia. Unidades: nanoWatts/cm²/sr.
- **Rango típico Guayaquil:** Centros formales 35-55 nW; periferias 8-20 nW;
  zonas rurales/insulares 2-8 nW (consistente con literatura Black Marble).

## Cita recomendada para este dataset
Leyva-Vázquez, M.Y., Batista-Hernández, N., Cevallos-Torres, L.,
Guijarro-Rodríguez, A.A., Iturburu-Salvador, D., & Smarandache, F. (2026).
Neutro-Safe: Neutrosophic Urban Digital Twin for Structural Violence Diagnosis
in Guayaquil — Dataset v1.0. Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX

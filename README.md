# Neutro-Safe — Guayaquil Urban Digital Twin

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://guayaquil-neutrosafe.streamlit.app)

A five-layer neutrosophic urban digital twin for structural violence diagnosis in Guayaquil, Ecuador. Implements the **Camino B** ethical framework — community diagnosis, not predictive policing.

## Key Empirical Findings

- **Corruption** is the strongest structural vulnerability driver (r = 0.852 with IPVE)
- **8 formally illuminated central sectors** (Centro Histórico, Urdesa, Centro Bancario) show higher structural vulnerability than periferias — a paraconsistency between physical infrastructure quality and governance failure invisible to scalar indices
- **Local media silences** weapons trafficking (Δ = −0.444) and extortion (Δ = −0.345) relative to survey-based structural baseline (N-fsQCA, 31 sources, 4 LLMs)

## Data Layers

| Layer | Source | n | Status |
|-------|--------|---|--------|
| L1 — Structural survey | Original survey Guayaquil 2023-24 | 151 obs | Real |
| L2 — Media N-fsQCA | 31 articles, 4 LLMs (OpenRouter) | 31 | Real |
| L3 — Gender violence | INEC ENVIGMU 2019 + Fiscalía 2022-23 | 28 sectors | Real |
| L4 — Nightlight | NASA VIIRS VNP46A3 2023 (EOG Colorado) | 28 sectors | Real |
| L5 — Community | Participatory registration | open | Active |

## Run Locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Ethical Framework (Camino B)

This platform **prohibits**: insurance/credit scoring, real estate segmentation, tactical policing, commercial data resale.

All actions are logged in an immutable audit trail.

## Citation

Leyva-Vázquez, M.Y. et al. (2026). *Neutro-Safe: A Neutrosophic Digital Twin for Structural Urban Violence Diagnosis in Guayaquil, Ecuador*. IEEE ETCM 2026.

## License

Code: MIT | Data: CC BY 4.0

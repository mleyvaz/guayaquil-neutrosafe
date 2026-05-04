"""
Módulo de percepción comunitaria participativa — Guayaquil Neutro-Safe.

Permite a estudiantes, residentes y activistas registrar su percepción
(T, I, F) sobre 5 dimensiones de vulnerabilidad/resiliencia por sector.

El momento pedagógico central: T y F NO son complementos.
T + F > 1  →  paraconsistencia  →  el sector tiene evidencia simultánea
de riesgo Y de resiliencia activa. Eso es complejidad, no contradicción.
"""
from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path
import pandas as pd

HERE = Path(__file__).parent
PARTICIPATORY_PATH = HERE / "participatory_responses.csv"

DIMENSIONES = {
    "seguridad_general": {
        "label": "🔒 Seguridad general",
        "descripcion": "Violencia, robos, presencia de pandillas en el sector.",
        "T_pregunta": "El riesgo de violencia en este sector ES REAL y frecuente",
        "I_pregunta": "Tengo INCERTIDUMBRE — no tengo suficiente información para juzgar",
        "F_pregunta": "Hay factores de PROTECCIÓN activos (vecinos organizados, etc.)",
    },
    "violencia_genero": {
        "label": "🚺 Violencia de género",
        "descripcion": "Situación de mujeres y diversidades en el sector.",
        "T_pregunta": "El riesgo de violencia de género / feminicidio es ALTO aquí",
        "I_pregunta": "No tengo datos suficientes para evaluar esta dimensión",
        "F_pregunta": "Hay programas, redes de apoyo o casas de acogida activas",
    },
    "infraestructura": {
        "label": "🏗️ Infraestructura pública",
        "descripcion": "Iluminación, vías, espacios públicos, servicios básicos.",
        "T_pregunta": "La infraestructura DEFICIENTE contribuye a la inseguridad",
        "I_pregunta": "No conozco bien el estado de la infraestructura aquí",
        "F_pregunta": "La infraestructura es ADECUADA y promueve seguridad",
    },
    "gobernanza": {
        "label": "🏛️ Gobernanza e instituciones",
        "descripcion": "Funcionamiento del Estado, municipio, policía comunitaria.",
        "T_pregunta": "Las instituciones son INEFICACES o corruptas en este sector",
        "I_pregunta": "No sé qué tan bien funcionan las instituciones aquí",
        "F_pregunta": "Hay presencia estatal efectiva y respuesta institucional",
    },
    "cohesion_social": {
        "label": "🤝 Cohesión social comunitaria",
        "descripcion": "Redes de apoyo, organización barrial, confianza vecinal.",
        "T_pregunta": "La desintegración social / falta de redes es un problema serio",
        "I_pregunta": "Desconozco el estado de las redes comunitarias aquí",
        "F_pregunta": "Hay organizaciones comunitarias activas y confianza vecinal",
    },
}

ROLES = [
    "Estudiante universitario/a",
    "Docente / investigador/a",
    "Residente del sector evaluado",
    "Activista / organizador/a comunitario/a",
    "Periodista / comunicador/a",
    "Funcionario/a municipal",
    "Otro",
]

CSV_COLUMNS = [
    "timestamp", "session_id", "sector", "rol", "contexto_relacion",
    "seg_T", "seg_I", "seg_F",
    "vg_T", "vg_I", "vg_F",
    "infra_T", "infra_I", "infra_F",
    "gob_T", "gob_I", "gob_F",
    "cohesion_T", "cohesion_I", "cohesion_F",
    "notas_libres",
]

DIM_COLS = {
    "seguridad_general": ("seg_T", "seg_I", "seg_F"),
    "violencia_genero":  ("vg_T",  "vg_I",  "vg_F"),
    "infraestructura":   ("infra_T","infra_I","infra_F"),
    "gobernanza":        ("gob_T", "gob_I", "gob_F"),
    "cohesion_social":   ("cohesion_T","cohesion_I","cohesion_F"),
}


def save_response(
    session_id: str,
    sector: str,
    rol: str,
    contexto: str,
    percepciones: dict[str, dict[str, float]],
    notas: str = "",
) -> bool:
    row: dict = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": session_id,
        "sector": sector,
        "rol": rol,
        "contexto_relacion": contexto,
        "notas_libres": notas,
    }
    for dim, (tc, ic, fc) in DIM_COLS.items():
        p = percepciones.get(dim, {"T": 0.5, "I": 0.5, "F": 0.5})
        row[tc] = round(p["T"], 2)
        row[ic] = round(p["I"], 2)
        row[fc] = round(p["F"], 2)

    file_exists = PARTICIPATORY_PATH.exists()
    with open(PARTICIPATORY_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    return True


def load_responses() -> pd.DataFrame:
    if not PARTICIPATORY_PATH.exists():
        return pd.DataFrame(columns=CSV_COLUMNS)
    return pd.read_csv(PARTICIPATORY_PATH)


def aggregate_by_sector(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    numeric = [c for c in CSV_COLUMNS
               if c not in ("timestamp","session_id","sector","rol",
                            "contexto_relacion","notas_libres")]
    agg = df.groupby("sector")[numeric].mean().round(3).reset_index()
    T_cols = ["seg_T","vg_T","infra_T","gob_T","cohesion_T"]
    I_cols = ["seg_I","vg_I","infra_I","gob_I","cohesion_I"]
    F_cols = ["seg_F","vg_F","infra_F","gob_F","cohesion_F"]
    agg["T_part"] = agg[T_cols].mean(axis=1).round(3)
    agg["I_part"] = agg[I_cols].mean(axis=1).round(3)
    agg["F_part"] = agg[F_cols].mean(axis=1).round(3)
    counts = df.groupby("sector").size().rename("n_respuestas")
    agg = agg.merge(counts, on="sector")
    agg["paraconsistente"] = (agg["T_part"] + agg["F_part"]) > 1.0
    return agg


def regime_label(T: float, F: float, I: float) -> str:
    if T + F > 1.0:
        return "C5 — PARACONSISTENTE (T+F>1): riesgo Y resiliencia coexisten"
    if T >= 0.6 and F <= 0.3 and I <= 0.3:
        return "C1 — Evidencia alta de riesgo"
    if F >= 0.6 and T <= 0.3 and I <= 0.3:
        return "C2 — Evidencia alta de resiliencia"
    if T <= 0.3 and F <= 0.3 and I >= 0.6:
        return "C3 — Indeterminación admitida (no hay datos suficientes)"
    if 0.3 < T < 0.6 and 0.3 < F < 0.6 and I >= 0.6:
        return "C4 — Indeterminación estructural (señales mixtas)"
    return "Mixto"

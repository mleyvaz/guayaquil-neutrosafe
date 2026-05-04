"""
Salvaguardas eticas operativas para Guayaquil Neutro-Safe (Camino B).

Implementa controles tecnicos que materializan las reglas de
500_GOBERNANZA_ETICA_CAMINO_B.md:

  1. Granularidad minima: ningun output por debajo de sector / parroquia.
  2. Prohibicion explicita de uso comercial discriminatorio (aseguradoras,
     inmobiliarias, empleadores).
  3. Audit log de descargas y consultas significativas.
  4. Disclaimer obligatorio en cualquier export.
  5. Bloqueo de ranking publico simple sin (T, I, F) acompañante.
"""
from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
AUDIT_LOG = HERE / "audit_log.jsonl"

# Limite minimo de granularidad: 1 sector = mínimo 5,000 hab. en Guayaquil promedio.
MIN_GRANULARITY = "sector"

DISCLAIMER = """
---
AVISO ÉTICO Y LEGAL:

Esta plataforma produce diagnósticos estructurales orientados a INTERVENCIÓN
SOCIAL NO POLICIAL. Su uso para los siguientes fines está expresamente
PROHIBIDO por los términos de uso (acordados al ingresar):

  • Discriminación de residentes en evaluación crediticia o de seguros
  • Segmentación inmobiliaria por barrio para fijar precios
  • Discriminación laboral basada en lugar de residencia
  • Despliegue policial táctico sin consulta comunitaria previa
  • Reventa o redistribución comercial de los datos

Las cifras NO predicen eventos individuales. Representan condiciones
estructurales agregadas con incertidumbre explícita (T, I, F).

Auditoría: Comité de Ética UBE | Defensoría del Pueblo Guayas |
3 representantes barriales rotativos.

Marco legal: LOPDP (2021) Art. 50 + Código de la Niñez Art. 26 +
Recomendación UNESCO 2021 sobre Ética de la IA.
---
"""

PROHIBITED_USES = [
    "asegurador", "seguros", "tarifa", "prima", "scoring", "credito",
    "inmobiliari", "real estate", "valuaci", "tasaci",
    "background check", "contratacion", "contratación",
    "policia", "policía", "patrullaje", "despliegue",
    "reventa", "comercializaci",
]


def log_audit(action: str, user_purpose: str = "no_specified",
              sector: str | None = None, payload: dict | None = None):
    """
    Append an audit-log entry. JSONL format.
    Public file: anyone can verify what queries were made when.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "purpose_declared": user_purpose,
        "sector": sector,
        "payload_summary": (str(payload)[:200] if payload else None),
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def check_purpose(purpose_text: str) -> tuple[bool, str]:
    """
    Returns (allowed, message). Blocks queries whose declared purpose
    matches prohibited use.
    """
    if not purpose_text:
        return False, "Debe declarar el propósito de uso para acceder."
    p = purpose_text.lower()
    for forbidden in PROHIBITED_USES:
        if forbidden in p:
            return False, (f"Uso BLOQUEADO: el propósito declarado contiene "
                           f"el término '{forbidden}', vetado por términos de uso. "
                           "Ver Aviso Ético al pie.")
    return True, "Propósito aceptado."


def get_disclaimer() -> str:
    return DISCLAIMER


def read_audit_log(last_n: int = 50) -> list[dict]:
    """Return last N audit entries (public for transparency)."""
    if not AUDIT_LOG.exists():
        return []
    with open(AUDIT_LOG, "r", encoding="utf-8") as f:
        lines = f.readlines()
    entries = [json.loads(l) for l in lines if l.strip()]
    return entries[-last_n:]


def block_simple_ranking(rank_dict: dict) -> bool:
    """
    Returns True if the ranking output is incomplete (lacks T, I, F per item).
    Used to enforce that NO sector ranking is published without its triplet.
    """
    if not isinstance(rank_dict, list):
        return True
    for item in rank_dict:
        if not all(k in item for k in ("T", "I", "F")):
            return True
    return False


if __name__ == "__main__":
    print("=== Test salvaguardas eticas ===\n")

    print("1. Test check_purpose:")
    for txt in ["investigacion academica",
                 "necesito esto para una aseguradora",
                 "evaluacion de riesgo inmobiliario",
                 "diagnostico estructural municipal"]:
        ok, msg = check_purpose(txt)
        marca = "OK" if ok else "BLOQUEADO"
        print(f"   [{marca}] '{txt}' -> {msg}")

    print("\n2. Test log_audit:")
    log_audit("query_sector", "investigacion academica", "Tarqui — Mucho Lote",
              {"endpoint": "ipve_table"})
    log_audit("download_csv", "presupuesto participativo", None,
              {"records": 28})
    print(f"   Audit log: {AUDIT_LOG}")
    print(f"   Entradas: {len(read_audit_log())}")

    print("\n3. Test disclaimer:")
    print(get_disclaimer()[:200] + "...")

    print("\n4. Test block_simple_ranking:")
    rank_bad = [{"sector": "X", "score": 0.85}]
    rank_good = [{"sector": "X", "T": 0.85, "I": 0.30, "F": 0.10}]
    print(f"   Ranking sin TIF: bloqueado={block_simple_ranking(rank_bad)}")
    print(f"   Ranking con TIF: bloqueado={block_simple_ranking(rank_good)}")

"""
Gemelo Digital Urbano Pluriversal — Guayaquil Neutro-Safe

Núcleo del Digital Twin que integra todas las capas del proyecto:

  Capa 1 — Estado estructural:    14 indicadores x 28 sectores  (data_loader)
  Capa 2 — Estado triádico:       (T, I, F) por sector          (ipve_engine)
  Capa 3 — Estado narrativo:      N-fsQCA mediático             (narrativa_mediatica)
  Capa 4 — Catálogo intervención: 8 intervenciones no-policiales (interventions_db)
  Capa 5 — Estado persistente:    historial de snapshots + intervenciones aplicadas

Cumple las 4 propiedades operativas de un gemelo digital legítimo
(Stolfi & de Figueiredo 1993; Tao 2019; Singapore Virtual; Helsinki 3D+):

  1. SINCRONIZACIÓN: ingesta periódica de datos (timestamp por snapshot).
  2. SIMULACIÓN CONTRAFACTUAL: aplicar intervención X virtualmente y ver delta.
  3. FEEDBACK BIDIRECCIONAL: las intervenciones reales se registran y actualizan
     el twin; el twin recomienda intervenciones que el comité comunitario aprueba.
  4. GRANULARIDAD: sector (≥ 5 000 hab.) + snapshots temporales mensuales.

Salvaguardas Camino B integradas: cualquier intervención simulada o aplicada
debe estar en el catálogo NO-POLICIAL (interventions_db.CATALOGO).
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import pandas as pd

from neutrosophic_core import TIFTriplet, svnwa
from interventions_db import CATALOGO, Intervencion
from data_loader import load_and_prepare, DRIVER_COLS, OUTCOME_COLS
from ipve_engine import ipve_table, aggregate_sector
from narrativa_mediatica import (load_demo_claims, n_fsqca_table,
                                  contrast_with_structural, NARRATIVE_TO_STRUCTURAL,
                                  COND_KEYS as MEDIA_CONDITIONS)
from ethical_safeguards import log_audit


HERE = Path(__file__).parent
TWIN_STATE_PATH = HERE / "twin_state.json"
INTERVENTIONS_LOG = HERE / "interventions_applied.jsonl"


# ===================================================================
# ESTADO DEL TWIN — un snapshot
# ===================================================================
@dataclass
class TwinSnapshot:
    """
    Snapshot del estado del gemelo digital en un momento dado.
    Inmutable: un snapshot capturado nunca se modifica.
    """
    timestamp: str
    label: str  # "baseline_2026-04" | "post_intervencion_alumbrado" | etc
    structural_ipve: list[dict]  # IPVE por sector con T, I, F
    media_nfsqca: list[dict]  # N-fsQCA por condición mediática
    n_interventions_applied: int  # nro de intervenciones aplicadas hasta este snapshot
    notes: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


# ===================================================================
# REGISTRO DE INTERVENCIÓN APLICADA
# ===================================================================
@dataclass
class InterventionApplied:
    """Registro de una intervención REAL aplicada en un sector."""
    timestamp: str
    sector: str
    intervencion_nombre: str
    estado_aplicacion: str  # "planificada" | "en_curso" | "completada"
    aprobacion_comunitaria: bool
    presupuesto_real_usd: int
    notas: str = ""

    def to_dict(self):
        return asdict(self)


# ===================================================================
# GEMELO DIGITAL URBANO — clase principal
# ===================================================================
class UrbanTwin:
    """
    Gemelo digital del estado de seguridad estructural y narrativa de Guayaquil.

    NO es un simulador de eventos delictivos.
    NO es un planificador de despliegues policiales.
    SÍ es un instrumento de deliberación comunitaria + diseño de política social.
    """

    def __init__(self):
        self.snapshots: list[TwinSnapshot] = []
        self.interventions_applied: list[InterventionApplied] = []
        # Cargar estado base
        raw, agg, tif = load_and_prepare()
        self.structural_data_raw = raw
        self.structural_data_agg = agg
        self.tif_matrix = tif
        self.media_claims = load_demo_claims()
        # Crear snapshot baseline si no existe
        self._ensure_baseline()
        # Cargar estado persistente
        self._load_state()

    # ------- snapshot management ----------
    def _ensure_baseline(self):
        if not self.snapshots:
            ipve = ipve_table(self.tif_matrix)
            nfs = n_fsqca_table(self.media_claims)
            baseline = TwinSnapshot(
                timestamp=datetime.now().isoformat(),
                label="baseline_inicial",
                structural_ipve=ipve.to_dict("records"),
                media_nfsqca=nfs.to_dict("records"),
                n_interventions_applied=0,
                notes="Snapshot inicial del gemelo. Datos de encuesta + medios sintéticos.",
            )
            self.snapshots.append(baseline)

    def take_snapshot(self, label: str, notes: str = "") -> TwinSnapshot:
        """Captura el estado actual del twin (después de aplicar intervenciones)."""
        # Re-compute estado actual incorporando intervenciones aplicadas
        modified_tif = self._apply_interventions_to_tif()
        ipve = ipve_table(modified_tif)
        # Para narrativa, asumimos que las intervenciones también afectan I mediática
        # (mejor data → menos disagreement)
        nfs = n_fsqca_table(self.media_claims)
        snap = TwinSnapshot(
            timestamp=datetime.now().isoformat(),
            label=label,
            structural_ipve=ipve.to_dict("records"),
            media_nfsqca=nfs.to_dict("records"),
            n_interventions_applied=len(self.interventions_applied),
            notes=notes,
        )
        self.snapshots.append(snap)
        self._save_state()
        log_audit("snapshot_taken", "twin_evolution", payload={"label": label})
        return snap

    def get_baseline(self) -> TwinSnapshot:
        return self.snapshots[0]

    def get_latest(self) -> TwinSnapshot:
        return self.snapshots[-1]

    # ------- interventions ----------
    def find_intervention(self, name: str) -> Optional[Intervencion]:
        for iv in CATALOGO:
            if iv.nombre == name:
                return iv
        return None

    def apply_intervention(self, sector: str, intervencion_nombre: str,
                            estado: str = "planificada",
                            aprobacion_comunitaria: bool = False,
                            presupuesto_real_usd: int = 0,
                            notas: str = "") -> InterventionApplied:
        """
        Registra una intervención real (o planificada) en un sector.

        Si aprobacion_comunitaria=False, se planifica pero no se ejecuta
        ni modifica los snapshots.
        """
        iv = self.find_intervention(intervencion_nombre)
        if iv is None:
            raise ValueError(f"Intervención no encontrada: {intervencion_nombre}")

        record = InterventionApplied(
            timestamp=datetime.now().isoformat(),
            sector=sector,
            intervencion_nombre=intervencion_nombre,
            estado_aplicacion=estado,
            aprobacion_comunitaria=aprobacion_comunitaria,
            presupuesto_real_usd=presupuesto_real_usd or iv.costo_usd_aprox,
            notas=notas,
        )
        self.interventions_applied.append(record)
        self._save_state()
        log_audit("intervention_applied", "twin_intervention",
                  sector=sector, payload=record.to_dict())
        return record

    def _apply_interventions_to_tif(self) -> pd.DataFrame:
        """Aplica las reducciones T/I/F al TIF matrix según intervenciones aprobadas."""
        modified = self.tif_matrix.copy()
        for ia in self.interventions_applied:
            if not ia.aprobacion_comunitaria:
                continue
            iv = self.find_intervention(ia.intervencion_nombre)
            if iv is None:
                continue
            mask = (modified["sector"] == ia.sector) & \
                   (modified["indicador"].isin(iv.indicadores_objetivo))
            modified.loc[mask, "T"] = (modified.loc[mask, "T"] -
                                        iv.reduccion_T_esperada).clip(lower=0)
            modified.loc[mask, "I"] = (modified.loc[mask, "I"] -
                                        iv.reduccion_I_esperada).clip(lower=0)
            modified.loc[mask, "F"] = (modified.loc[mask, "F"] +
                                        iv.reduccion_T_esperada * 0.5).clip(upper=1)
        return modified

    # ------- simulación contrafactual ----------
    def simulate_intervention(self, sector: str,
                              intervencion_nombre: str) -> dict:
        """
        Simula virtualmente el impacto de una intervención SIN aplicarla.
        Devuelve {antes, despues, delta} con tripletes (T, I, F).
        Esta es la propiedad #2 del digital twin: simulación contrafactual.
        """
        iv = self.find_intervention(intervencion_nombre)
        if iv is None:
            raise ValueError(f"Intervención no encontrada: {intervencion_nombre}")

        # Estado actual del sector (antes)
        before = aggregate_sector(self._apply_interventions_to_tif(), sector)

        # Simulamos aplicación virtual
        simulated_tif = self._apply_interventions_to_tif().copy()
        mask = (simulated_tif["sector"] == sector) & \
               (simulated_tif["indicador"].isin(iv.indicadores_objetivo))
        simulated_tif.loc[mask, "T"] = (simulated_tif.loc[mask, "T"] -
                                         iv.reduccion_T_esperada).clip(lower=0)
        simulated_tif.loc[mask, "I"] = (simulated_tif.loc[mask, "I"] -
                                         iv.reduccion_I_esperada).clip(lower=0)
        simulated_tif.loc[mask, "F"] = (simulated_tif.loc[mask, "F"] +
                                         iv.reduccion_T_esperada * 0.5).clip(upper=1)
        after = aggregate_sector(simulated_tif, sector)

        log_audit("simulation_run", "twin_simulation", sector=sector,
                  payload={"intervencion": intervencion_nombre})

        return {
            "sector": sector,
            "intervencion": intervencion_nombre,
            "intervencion_costo_usd": iv.costo_usd_aprox,
            "intervencion_meses": iv.tiempo_meses,
            "intervencion_evidencia": iv.evidencia_caso,
            "indicadores_afectados": iv.indicadores_objetivo,
            "antes": {"T": before.T, "I": before.I, "F": before.F,
                       "regimen": before.regime()},
            "despues": {"T": after.T, "I": after.I, "F": after.F,
                          "regimen": after.regime()},
            "delta": {"dT": after.T - before.T,
                       "dI": after.I - before.I,
                       "dF": after.F - before.F},
        }

    # ------- temporal evolution ----------
    def temporal_series(self) -> pd.DataFrame:
        """Serie temporal del estado del twin: agregado de IPVE T, I, F por snapshot."""
        rows = []
        for snap in self.snapshots:
            df = pd.DataFrame(snap.structural_ipve)
            rows.append({
                "timestamp": snap.timestamp,
                "label": snap.label,
                "T_promedio": float(df["T"].mean()),
                "I_promedio": float(df["I"].mean()),
                "F_promedio": float(df["F"].mean()),
                "n_paraconsistente": int(df["paraconsistente"].sum()),
                "n_intervenciones": snap.n_interventions_applied,
            })
        return pd.DataFrame(rows)

    # ------- persistencia ----------
    def _save_state(self):
        state = {
            "snapshots": [s.to_dict() for s in self.snapshots],
            "interventions_applied": [i.to_dict() for i in self.interventions_applied],
        }
        try:
            with open(TWIN_STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            if self.interventions_applied:
                with open(INTERVENTIONS_LOG, "w", encoding="utf-8") as f:
                    for ia in self.interventions_applied:
                        f.write(json.dumps(ia.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            pass  # ephemeral filesystem — state lives in memory for this session

    def _load_state(self):
        if not TWIN_STATE_PATH.exists():
            return
        try:
            with open(TWIN_STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
            # Reemplaza snapshots solo si el archivo tiene baseline + más
            loaded_snaps = [TwinSnapshot.from_dict(s) for s in state.get("snapshots", [])]
            if len(loaded_snaps) >= 1:
                self.snapshots = loaded_snaps
            self.interventions_applied = [
                InterventionApplied(**i) for i in state.get("interventions_applied", [])
            ]
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"[twin] error cargando estado: {e}; usando baseline limpio")

    def reset(self):
        """Borra historial y vuelve a baseline. Operación auditada."""
        self.snapshots = []
        self.interventions_applied = []
        if TWIN_STATE_PATH.exists():
            TWIN_STATE_PATH.unlink()
        if INTERVENTIONS_LOG.exists():
            INTERVENTIONS_LOG.unlink()
        self._ensure_baseline()
        log_audit("twin_reset", "twin_admin")


if __name__ == "__main__":
    print("=== Inicializando Gemelo Digital Urbano Pluriversal ===\n")
    twin = UrbanTwin()
    print(f"Snapshots existentes: {len(twin.snapshots)}")
    print(f"Intervenciones aplicadas: {len(twin.interventions_applied)}")
    print(f"Sectores en estado: {len(twin.structural_data_agg)}")
    print(f"Indicadores estructurales: {len(DRIVER_COLS) + len(OUTCOME_COLS)}")
    print(f"Condiciones mediaticas: {len(MEDIA_CONDITIONS)}")
    print(f"Intervenciones disponibles en catalogo: {len(CATALOGO)}")

    print("\n=== Simulacion contrafactual ===")
    sim = twin.simulate_intervention(
        "Tarqui — Mucho Lote",
        "Iluminacion publica focalizada"
    )
    print(f"\nIntervencion: {sim['intervencion']}")
    print(f"Costo estimado: USD {sim['intervencion_costo_usd']:,}")
    print(f"Tiempo: {sim['intervencion_meses']} meses")
    print(f"Sector: {sim['sector']}")
    print(f"\nAntes:    T={sim['antes']['T']:.3f}  I={sim['antes']['I']:.3f}  F={sim['antes']['F']:.3f}")
    print(f"Despues:  T={sim['despues']['T']:.3f}  I={sim['despues']['I']:.3f}  F={sim['despues']['F']:.3f}")
    print(f"Delta:    dT={sim['delta']['dT']:+.3f} dI={sim['delta']['dI']:+.3f} dF={sim['delta']['dF']:+.3f}")
    print(f"Regimen antes: {sim['antes']['regimen']}")
    print(f"Regimen despues: {sim['despues']['regimen']}")

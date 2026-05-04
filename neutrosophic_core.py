"""
Neutrosophic core — corrected (T, I, F) representation.

Replaces the erroneous IVN scalar collapse from 200_ANALISIS_DATOS_VULNERABILIDAD.md
   IVN = T*w1 + I*w2 - F*w3      ← INCORRECT: mixes ontological categories

with a true triadic representation that preserves T, I, F as independent
components, in line with Smarandache (1998), Wang et al. (2010), and the
empirical reframing in Leyva-Vázquez & Smarandache (2026).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class TIFTriplet:
    """
    Neutrosophic triplet (T, I, F) with T, I, F in [0, 1] independently.
    There is NO sum constraint: T + I + F may be < 1, = 1, or > 1.
    The case T + F > 1 (paraconsistent) is the unique discriminator of
    neutrosophic logic vs classical / fuzzy / intuitionistic-fuzzy.
    """
    T: float
    I: float
    F: float

    def __post_init__(self):
        for name, val in (("T", self.T), ("I", self.I), ("F", self.F)):
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"{name}={val} outside [0,1]")

    # ---------- regimes ----------
    def regime(self, lo: float = 0.3, hi: float = 0.6) -> str:
        """Five operational regimes (Leyva-Vázquez 2026)."""
        T, I, F = self.T, self.I, self.F
        if T + F > 1.0:
            return "C5_paraconsistente"
        if T >= hi and F <= lo and I <= lo:
            return "C1_evidencia_alta"
        if F >= hi and T <= lo and I <= lo:
            return "C2_riesgo_alto"
        if T <= lo and F <= lo and I >= hi:
            return "C3_indeterminacion_admitida"
        if lo < T < hi and lo < F < hi and I >= hi:
            return "C4_indeterminacion_estructural"
        return "mixto"

    # ---------- ranking helpers ----------
    def score_pessimistic(self) -> float:
        """
        Pessimistic ranking score for triage purposes ONLY.
        NOT used as IVN/IPVE scalar. Returns a number for ordering;
        the underlying (T,I,F) MUST be displayed alongside.
        """
        return self.T - self.F + 0.5 * self.I  # I treated as risk-augmenting bound

    def score_optimistic(self) -> float:
        return self.T - self.F - 0.5 * self.I  # I treated as resilience-augmenting bound

    def is_paraconsistent(self) -> bool:
        return self.T + self.F > 1.0

    def to_dict(self) -> dict:
        return {"T": self.T, "I": self.I, "F": self.F}

    def __repr__(self):
        return f"TIF(T={self.T:.3f}, I={self.I:.3f}, F={self.F:.3f})"


# ---------- aggregation operators ----------
def svnwa(triplets: Sequence[TIFTriplet], weights: Sequence[float]) -> TIFTriplet:
    """
    Single-Valued Neutrosophic Weighted Average (Wang et al., 2010).

    SVNWA = ( 1 - Π(1 - T_i)^w_i,   Π I_i^w_i,   Π F_i^w_i )

    Preserves the triadic structure; does NOT collapse to scalar.
    """
    if len(triplets) != len(weights):
        raise ValueError("triplets and weights must have same length")
    s = sum(weights)
    if s == 0:
        raise ValueError("weights sum to 0")
    w = [x / s for x in weights]

    one_minus_T_prod = 1.0
    I_prod = 1.0
    F_prod = 1.0
    for t, wi in zip(triplets, w):
        one_minus_T_prod *= (1.0 - t.T) ** wi
        I_prod *= t.I ** wi if t.I > 0 else 0.0
        F_prod *= t.F ** wi if t.F > 0 else 0.0
    return TIFTriplet(
        T=1.0 - one_minus_T_prod,
        I=I_prod,
        F=F_prod,
    )


def union(a: TIFTriplet, b: TIFTriplet) -> TIFTriplet:
    """Standard neutrosophic union (Smarandache 2003)."""
    return TIFTriplet(
        T=max(a.T, b.T),
        I=min(a.I, b.I),
        F=min(a.F, b.F),
    )


def intersection(a: TIFTriplet, b: TIFTriplet) -> TIFTriplet:
    """Standard neutrosophic intersection."""
    return TIFTriplet(
        T=min(a.T, b.T),
        I=max(a.I, b.I),
        F=max(a.F, b.F),
    )


def complement(a: TIFTriplet) -> TIFTriplet:
    """Neutrosophic complement: (T, I, F) → (F, 1-I, T)."""
    return TIFTriplet(T=a.F, I=1.0 - a.I, F=a.T)


# ---------- I as epistemic gap, NOT as state penetration ----------
def epistemic_gap_from_sources(
    source_values: Sequence[float],
    source_confidences: Sequence[float],
) -> float:
    """
    Compute I as DISAGREEMENT among independent sources (epistemic gap),
    NOT as 'absence of state' (which would securitize I incorrectly).

    Higher disagreement among reliable sources → higher I.
    Returns I in [0, 1].
    """
    if len(source_values) != len(source_confidences):
        raise ValueError("values and confidences must have same length")
    if len(source_values) < 2:
        return 0.0
    # Weighted variance, normalized
    s = sum(source_confidences)
    if s == 0:
        return 1.0
    w = [c / s for c in source_confidences]
    mean = sum(v * wi for v, wi in zip(source_values, w))
    var = sum(wi * (v - mean) ** 2 for v, wi in zip(source_values, w))
    # Map variance to [0,1]: 0 disagreement → 0; full opposite (var=0.25) → 1
    return min(var * 4.0, 1.0)


if __name__ == "__main__":
    # Self-test
    examples = [
        TIFTriplet(0.85, 0.10, 0.05),  # C1 — evidence high
        TIFTriplet(0.10, 0.10, 0.85),  # C2 — risk high
        TIFTriplet(0.10, 0.85, 0.10),  # C3 — admitted indeterminacy
        TIFTriplet(0.45, 0.65, 0.40),  # C4 — structural indeterminacy
        TIFTriplet(0.70, 0.20, 0.65),  # C5 — paraconsistent
        TIFTriplet(0.40, 0.30, 0.30),  # mixed
    ]
    print(f"{'Triplet':<35} {'Regime':<32} {'Score(pess)':>12}")
    print("-" * 80)
    for ex in examples:
        print(f"{str(ex):<35} {ex.regime():<32} {ex.score_pessimistic():>+12.3f}")

    # Aggregation test
    agg = svnwa(examples[:3], [0.5, 0.3, 0.2])
    print(f"\nSVNWA aggregation of first 3 with weights [0.5, 0.3, 0.2]:")
    print(f"  -> {agg}  (regime: {agg.regime()})")

    # Epistemic gap test
    print(f"\nEpistemic gap (3 sources agree): {epistemic_gap_from_sources([0.6, 0.61, 0.59], [1, 1, 1]):.3f}")
    print(f"Epistemic gap (3 sources disagree): {epistemic_gap_from_sources([0.2, 0.5, 0.9], [1, 1, 1]):.3f}")

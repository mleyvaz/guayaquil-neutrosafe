"""
nfsqca_auto.py — Automated N-fsQCA via OpenRouter
Scores scraped articles against 8 causal conditions using 4 LLMs.
Computes T, I (inter-LLM variance/0.25), F per condition.
Saves results to real_data/nfsqca_live.csv.

API key: read from env OPENROUTER_API_KEY or st.secrets
Cost estimate: ~USD 0.10-0.20 per daily run (10-15 articles × 4 LLMs)
"""
from __future__ import annotations
import os
import json
import time
import statistics
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent.parent
OUTPUT_CSV = HERE / "real_data" / "nfsqca_live.csv"

MODELS = [
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.1-8b-instruct",
    "microsoft/phi-4",
    "qwen/qwen-3-8b",
]

CONDITIONS = {
    "drug_routes":          "Rutas de tráfico de drogas y crimen transnacional",
    "territorial_war":      "Guerra territorial entre bandas o pandillas",
    "prison_link":          "Vínculos entre crimen organizado y sistema carcelario",
    "weapons_traffic":      "Tráfico de armas",
    "extorsion":            "Extorsión a negocios o comunidades",
    "economic_pressure":    "Presión económica y desigualdad como factor de violencia",
    "social_fragmentation": "Fragmentación social o comunitaria",
    "institutional_failure":"Fallas institucionales, corrupción o impunidad",
}

PROMPT_TEMPLATE = """Eres un analista experto en violencia urbana en Ecuador.
Lee el siguiente fragmento de noticia y evalúa qué tan presente está la condición indicada.

NOTICIA:
Título: {title}
Resumen: {summary}

CONDICIÓN A EVALUAR: {condition_label}
Descripción: {condition_desc}

Responde ÚNICAMENTE con un número decimal entre 0.0 y 1.0:
- 0.0 = la condición no aparece en absoluto
- 0.5 = aparece parcialmente o de forma implícita
- 1.0 = es el tema central del artículo

Número (solo el número, sin texto adicional):"""


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("OPENROUTER_API_KEY", "")
        except Exception:
            pass
    if not key:
        raise ValueError(
            "OPENROUTER_API_KEY no encontrada. "
            "Agregar en GitHub secrets o Streamlit secrets."
        )
    return key


def score_article_condition(
    api_key: str,
    model: str,
    title: str,
    summary: str,
    cond_key: str,
    cond_label: str,
    cond_desc: str,
    retries: int = 2,
) -> float:
    prompt = PROMPT_TEMPLATE.format(
        title=title, summary=summary[:600],
        condition_label=cond_label, condition_desc=cond_desc,
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/mleyvaz/guayaquil-neutrosafe",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 10,
    }
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload, timeout=30,
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()
            score = float(text.replace(",", ".").split()[0])
            return max(0.0, min(1.0, score))
        except Exception as e:
            if attempt == retries:
                print(f"    Error {model}/{cond_key}: {e} — usando 0.5")
                return 0.5
            time.sleep(2)
    return 0.5


def compute_nfsqca(
    articles: list[dict],
    api_key: str,
    max_articles: int = 15,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Runs N-fsQCA over articles with 4 LLMs.
    Returns DataFrame with T, I, F per condition.
    I = Var(scores_4LLMs) / 0.25  (max variance normalization)
    """
    articles = articles[:max_articles]
    results_per_cond: dict[str, list[float]] = {k: [] for k in CONDITIONS}
    variance_per_cond: dict[str, list[float]] = {k: [] for k in CONDITIONS}

    for idx, art in enumerate(articles):
        if verbose:
            print(f"  Artículo {idx+1}/{len(articles)}: {art['title'][:60]}...")
        for cond_key, cond_desc in CONDITIONS.items():
            scores_llm = []
            for model in MODELS:
                s = score_article_condition(
                    api_key=api_key,
                    model=model,
                    title=art["title"],
                    summary=art.get("summary", ""),
                    cond_key=cond_key,
                    cond_label=cond_key.replace("_", " ").title(),
                    cond_desc=cond_desc,
                )
                scores_llm.append(s)
                time.sleep(0.3)

            mean_score = statistics.mean(scores_llm)
            var_score  = statistics.variance(scores_llm) if len(scores_llm) > 1 else 0.0
            results_per_cond[cond_key].append(mean_score)
            variance_per_cond[cond_key].append(var_score)

    # Aggregate over all articles
    rows = []
    for cond_key in CONDITIONS:
        scores = results_per_cond[cond_key]
        variances = variance_per_cond[cond_key]
        T = statistics.mean(scores)
        F = 1 - T
        I = min(statistics.mean(variances) / 0.25, 1.0)  # N-fsQCA formula
        rows.append({
            "condicion": cond_key,
            "T": round(T, 4),
            "I": round(I, 4),
            "F": round(F, 4),
            "n_articulos": len(scores),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": "live_openrouter",
        })
    return pd.DataFrame(rows)


def run(articles: list[dict], verbose: bool = True) -> pd.DataFrame:
    api_key = get_api_key()
    if verbose:
        print(f"=== N-fsQCA automático: {len(articles)} artículos, 4 LLMs ===")
    df = compute_nfsqca(articles, api_key, verbose=verbose)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    if verbose:
        print(f"Guardado en {OUTPUT_CSV}")
        print(df[["condicion", "T", "I", "F"]].to_string(index=False))
    return df


if __name__ == "__main__":
    from scraper_noticias import run as scrape
    articles = scrape(verbose=True)
    if articles:
        run(articles, verbose=True)
    else:
        print("Sin artículos nuevos disponibles.")

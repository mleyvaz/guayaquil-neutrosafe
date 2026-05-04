"""
Guayaquil Neutro-Safe — Tablero Pluriversal de Diagnostico Estructural.

Implementa el Camino B (laboratorio comunitario, no predictive policing).
Usa lógica neutrosófica (T, I, F) sin colapso a escalar.

Lanzamiento:
    streamlit run streamlit_app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from data_loader import load_and_prepare, DRIVER_COLS, OUTCOME_COLS
from ipve_engine import ipve_table, top_indicators_for_sector, DEFAULT_WEIGHTS
from interventions_db import recomendar, todas_intervenciones_para_indicador, CATALOGO
from ethical_safeguards import (check_purpose, log_audit, get_disclaimer,
                                 read_audit_log, block_simple_ranking)
from neutrosophic_core import TIFTriplet
from narrativa_mediatica import (load_demo_claims, n_fsqca_table,
                                  contrast_with_structural, build_truth_table_fuzzy,
                                  CONDITIONS, COND_KEYS, OUTCOME_KEY,
                                  NARRATIVE_TO_STRUCTURAL)
from digital_twin import UrbanTwin
from datetime import datetime
from gender_violence import (synthetic_gender_data, gender_risk_score,
                              GENDER_INDICATORS)
from nightlight import (synthetic_nightlight, nightlight_to_tif,
                         NIGHTLIGHT_INDICATORS)
from paraconsistency_detector import (collect_all_sources_per_sector,
                                       detect_paraconsistency,
                                       disputed_sectors_summary)
from participatory import (
    DIMENSIONES, ROLES, save_response, load_responses,
    aggregate_by_sector, regime_label,
)


# =================================================================
# CONFIGURACION GLOBAL
# =================================================================
st.set_page_config(
    page_title="Guayaquil Neutro-Safe — Tablero Pluriversal",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Colores por regimen (consistentes en todas las paginas)
REGIME_COLORS = {
    "C1_evidencia_alta": "#2E7D32",
    "C2_riesgo_alto": "#C62828",
    "C3_indeterminacion_admitida": "#FFA000",
    "C4_indeterminacion_estructural": "#1976D2",
    "C5_paraconsistente": "#6A1B9A",
    "mixto": "#757575",
}


# =================================================================
# CARGA DE DATOS (cached)
# =================================================================
@st.cache_data
def get_data():
    raw, agg, tif = load_and_prepare()
    ipve = ipve_table(tif)
    return raw, agg, tif, ipve


raw_df, agg_df, tif_df, ipve_df = get_data()


@st.cache_resource
def get_twin():
    return UrbanTwin()


twin = get_twin()


# =================================================================
# SIDEBAR — autenticacion de proposito + navegacion
# =================================================================
with st.sidebar:
    st.markdown("## 🌐 Guayaquil Neutro-Safe")
    st.caption("Tablero Pluriversal · v1.0 · Camino B")

    st.markdown("---")
    st.markdown("### Acceso ético")

    if "purpose_validated" not in st.session_state:
        st.session_state.purpose_validated = False
        st.session_state.user_purpose = ""

    purpose_input = st.text_input(
        "¿Cuál es su propósito de consulta?",
        value=st.session_state.user_purpose,
        placeholder="Ej.: investigación académica, presupuesto participativo, política municipal social...",
        help="Las consultas con propósito comercial/policial están bloqueadas.",
    )
    if st.button("Validar acceso", type="primary"):
        ok, msg = check_purpose(purpose_input)
        st.session_state.purpose_validated = ok
        st.session_state.user_purpose = purpose_input
        if ok:
            st.success(msg)
            log_audit("session_start", purpose_input)
        else:
            st.error(msg)

    st.markdown("---")
    pagina = st.radio(
        "Navegación",
        [
            "🏠 Inicio y misión",
            "📊 Diagnóstico estructural por sector",
            "🔺 Mapa triádico (T, I, F)",
            "🛠 Recomendaciones de intervención",
            "📰 Análisis narrativo mediático (N-fsQCA)",
            "🔮 Gemelo Digital — Simulación contrafactual",
            "📡 Estado del Gemelo (sincronización)",
            "🔬 Capas extendidas: Género + Iluminación + Paraconsistencia",
            "🗣️ Percepción comunitaria (participativa)",
            "📋 Auditoría y salvaguardas",
            "📚 Marco teórico y citas",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("⚠️ Demo académico. Sectores con datos sintetizados a "
               "partir de encuesta pre-procesada. NO son atribuciones reales.")


# =================================================================
# GUARD CLAUSE: bloquear contenido si no validado
# =================================================================
if not st.session_state.purpose_validated and pagina != "🏠 Inicio y misión":
    st.warning("⚠️ Debe declarar y validar un propósito de consulta en el panel "
               "lateral antes de acceder al diagnóstico, mapa, recomendaciones o auditoría.")
    st.info("La página de **Inicio y misión** está disponible sin validación.")
    st.stop()


# =================================================================
# PAGINA 1 — INICIO Y MISION
# =================================================================
if pagina == "🏠 Inicio y misión":
    st.title("🌐 Guayaquil Neutro-Safe")
    st.markdown("### Tablero Pluriversal de Diagnóstico Estructural")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("Sectores analizados", f"{len(agg_df)}")
    col2.metric("Indicadores estructurales", f"{len(DRIVER_COLS)}")
    col3.metric("Indicadores de percepción", f"{len(OUTCOME_COLS)}")

    st.markdown("""
    ## ¿Qué es esta plataforma?

    Una herramienta de **diagnóstico estructural** —no de predicción policial—
    para apoyar **deliberación comunitaria, política social municipal e investigación
    académica** sobre las condiciones que enmarcan la violencia en Guayaquil.

    A diferencia del *predictive policing* tradicional, este tablero:

    - **NO predice quién cometerá un delito**.
    - **NO recomienda despliegues policiales**.
    - **NO produce rankings comerciales** ni segmentación de barrios para
      aseguradoras o inmobiliarias.

    En cambio:

    - **Diagnostica** las condiciones estructurales (empleo, educación,
      infraestructura, gobernanza) que aumentan o reducen la vulnerabilidad
      de cada sector.
    - **Modela explícitamente la indeterminación** (I) de la información
      disponible, sin colapsarla en un único número.
    - **Recomienda intervenciones no-policiales** con evidencia de impacto
      en LATAM.
    - **Audita** sus propios sesgos y limitaciones, y publica logs.

    ## El framework neutrosófico (T, I, F)

    Para cada sector e indicador, el tablero produce un **triplete**:

    - **T** — grado de evidencia que apoya el riesgo
    - **I** — grado de **gap epistémico irreducible** (datos faltantes,
      fuentes contradictorias)
    - **F** — grado de evidencia de resiliencia / factores protectores

    No se colapsan en un puntaje único. La indeterminación es información,
    no ruido a eliminar.

    ## Camino B vs Camino A

    Este tablero implementa explícitamente el **Camino B** documentado en
    `500_GOBERNANZA_ETICA_CAMINO_B.md`. La diferencia clave con la línea
    Camino A (predictive policing comercial) está documentada en el
    archivo del vault y en la página **Marco teórico**.
    """)

    st.markdown("### Salvaguardas activas en esta sesión")
    st.success("✅ Granularidad mínima: SECTOR (≥ 5 000 hab.) — nunca individuos")
    st.success("✅ Términos de uso comerciales bloqueados")
    st.success("✅ Audit log público de consultas")
    st.success("✅ Triplete (T, I, F) obligatorio en cualquier ranking")
    st.success("✅ Recomendaciones únicamente NO-policiales")

    with st.expander("Aviso ético y legal completo"):
        st.code(get_disclaimer())


# =================================================================
# PAGINA 2 — DIAGNOSTICO ESTRUCTURAL POR SECTOR
# =================================================================
elif pagina == "📊 Diagnóstico estructural por sector":
    st.title("📊 Diagnóstico estructural por sector")
    st.caption("Vector de 14 indicadores agregados por sector. Valores 0-1.")
    log_audit("page_diagnostico", st.session_state.user_purpose)

    # Selector de sector
    sectores = sorted(agg_df["sector_demo"].unique())
    sector_sel = st.selectbox("Seleccione sector:", sectores, index=0)

    sect = agg_df[agg_df["sector_demo"] == sector_sel].iloc[0]

    # Triplete agregado del sector
    sect_ipve = ipve_df[ipve_df["sector"] == sector_sel].iloc[0]

    st.markdown(f"### {sector_sel}")
    cols = st.columns(4)
    cols[0].metric("T (riesgo evidente)", f"{sect_ipve['T']:.3f}")
    cols[1].metric("I (indeterminación)", f"{sect_ipve['I']:.3f}")
    cols[2].metric("F (resiliencia evidente)", f"{sect_ipve['F']:.3f}")
    cols[3].metric("Régimen", sect_ipve["regimen"].split("_")[0].upper())

    st.markdown("#### Indicadores estructurales (drivers)")
    drivers_data = pd.DataFrame({
        "Indicador": DRIVER_COLS,
        "Valor (0-1)": [sect[c] for c in DRIVER_COLS],
    }).sort_values("Valor (0-1)", ascending=True)

    fig = px.bar(
        drivers_data, x="Valor (0-1)", y="Indicador",
        orientation="h", color="Valor (0-1)",
        color_continuous_scale="RdYlGn_r",
        range_color=[0, 1], height=420,
    )
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Indicadores de percepción (outcomes)")
    outcomes_data = pd.DataFrame({
        "Indicador": OUTCOME_COLS,
        "Valor (0-1)": [sect[c] for c in OUTCOME_COLS],
    })
    fig2 = px.bar(
        outcomes_data, x="Indicador", y="Valor (0-1)",
        color="Valor (0-1)", color_continuous_scale="RdYlGn_r",
        range_color=[0, 1], height=300,
    )
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)


# =================================================================
# PAGINA 3 — MAPA TRIADICO (T, I, F)
# =================================================================
elif pagina == "🔺 Mapa triádico (T, I, F)":
    st.title("🔺 Mapa triádico (T, I, F) por sector")
    st.caption("Cada punto es un sector. NO se colapsa en escalar único.")
    log_audit("page_mapa_triadico", st.session_state.user_purpose)

    # 3D scatter
    fig = px.scatter_3d(
        ipve_df, x="T", y="I", z="F", color="regimen",
        color_discrete_map=REGIME_COLORS,
        hover_data=["sector", "score_triage_pess"],
        height=600,
    )
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="T (riesgo)", range=[0, 1]),
            yaxis=dict(title="I (indeterm.)", range=[0, 1]),
            zaxis=dict(title="F (resiliencia)", range=[0, 1]),
        ),
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Distribución de regímenes")
    regime_counts = ipve_df["regimen"].value_counts().reset_index()
    regime_counts.columns = ["regimen", "n_sectores"]
    fig_pie = px.pie(regime_counts, values="n_sectores", names="regimen",
                     color="regimen", color_discrete_map=REGIME_COLORS,
                     height=350)
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("### Tabla detallada (T, I, F obligatorios)")
    if block_simple_ranking(ipve_df.to_dict("records")):
        st.error("BLOQUEADO: ranking sin (T, I, F) detectado.")
    else:
        st.dataframe(
            ipve_df.style.background_gradient(subset=["T"], cmap="Reds")
                          .background_gradient(subset=["I"], cmap="Blues")
                          .background_gradient(subset=["F"], cmap="Greens"),
            use_container_width=True, height=420,
        )

    st.info("""
    💡 **Cómo leer este mapa:**
    - **T alto, I bajo, F bajo** → evidencia clara de tensión estructural (rojo).
    - **T bajo, I alto** → no se sabe lo suficiente; **prioridad de levantamiento de datos**.
    - **T bajo, F alto** → resiliencia comunitaria evidente (verde).
    - **T y F simultáneamente altos (T+F > 1)** → régimen paraconsistente:
      el sector tiene tanto evidencia de riesgo como de resiliencia activa.
      No es contradicción; es **complejidad**.
    """)


# =================================================================
# PAGINA 4 — RECOMENDACIONES DE INTERVENCION
# =================================================================
elif pagina == "🛠 Recomendaciones de intervención":
    st.title("🛠 Recomendaciones de intervención no-policial")
    st.caption("Catálogo curado con evidencia LATAM. Solo intervenciones sociales/estructurales.")
    log_audit("page_recomendaciones", st.session_state.user_purpose)

    sector_sel = st.selectbox(
        "Seleccione sector para recomendaciones:",
        sorted(ipve_df["sector"].unique()),
    )

    top_t = top_indicators_for_sector(tif_df, sector_sel, by="T", n=5)
    indicadores_top = top_t["indicador"].tolist()

    st.markdown(f"### Top 5 indicadores con mayor T (riesgo) en **{sector_sel}**")
    st.dataframe(
        top_t.style.background_gradient(subset=["T"], cmap="Reds"),
        use_container_width=True, hide_index=True,
    )

    st.markdown("### Intervenciones recomendadas")
    recs = recomendar(indicadores_top, n=5)
    if not recs:
        st.warning("No hay intervenciones en el catálogo para los indicadores top de este sector.")
    else:
        for iv in recs:
            with st.expander(f"🔧 {iv.nombre}  ({iv.tipo})"):
                col1, col2 = st.columns(2)
                col1.markdown(f"**Costo aproximado:** USD {iv.costo_usd_aprox:,}")
                col1.markdown(f"**Tiempo:** {iv.tiempo_meses} meses")
                col1.markdown(f"**Reducción T esperada:** {iv.reduccion_T_esperada:.2f}")
                col1.markdown(f"**Reducción I esperada:** {iv.reduccion_I_esperada:.2f}")
                col2.markdown(f"**Indicadores objetivo:** {', '.join(iv.indicadores_objetivo)}")
                col2.markdown(f"**Evidencia caso LATAM:**")
                col2.caption(iv.evidencia_caso)
                st.markdown(f"**Descripción:** {iv.descripcion}")

    st.markdown("---")
    st.caption(f"Catálogo completo: {len(CATALOGO)} intervenciones documentadas. "
               "Todas con evidencia publicada en LATAM. Ninguna policial.")


# =================================================================
# PAGINA 5 — ANALISIS NARRATIVO MEDIATICO (N-fsQCA)
# =================================================================
elif pagina == "📰 Análisis narrativo mediático (N-fsQCA)":
    st.title("📰 Análisis narrativo mediático sobre violencia")
    st.caption("Extensión neutrosófica de fsQCA aplicada a noticias. "
               "MVP original: Gemini CLI (2026). Mejoras: fuzzy + N-fsQCA + contraste con encuesta.")
    log_audit("page_narrativa_mediatica", st.session_state.user_purpose)

    st.warning("⚠️ **Datos demostrativos sintéticos** basados en patrones de los 16 medios "
               "del MVP. Para datos reales, ejecutar `MVP_fsQCA_original.ipynb` con OpenAI API key.")

    claims_df = load_demo_claims()

    # ---- Vista 1: claims raw ----
    st.markdown("### Claims extraídos por LLM (16 noticias, 8 condiciones causales)")
    st.dataframe(
        claims_df.style.background_gradient(subset=COND_KEYS, cmap="Reds"),
        use_container_width=True, height=300, hide_index=True,
    )

    # ---- Vista 2: N-fsQCA per condition ----
    st.markdown("### N-fsQCA: triplete (T, I, F) por condición causal")
    st.caption("T = consenso mediático que afirma | F = consenso que omite/desestima | "
               "I = disagreement entre fuentes (paraconsistencia mediática)")
    nfs_df = n_fsqca_table(claims_df)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.dataframe(
            nfs_df.style.background_gradient(subset=["T"], cmap="Reds")
                         .background_gradient(subset=["I"], cmap="Blues")
                         .background_gradient(subset=["F"], cmap="Greens"),
            use_container_width=True, hide_index=True,
        )
    with col2:
        st.metric("Condiciones paraconsistentes (T+F>1)",
                  int(nfs_df["paraconsistente"].sum()))
        st.metric("Condición con mayor T (más mediatizada)",
                  nfs_df.iloc[0]["condicion"].replace("_", " "))
        st.metric("Condición con mayor I (más contestada)",
                  nfs_df.sort_values("I", ascending=False).iloc[0]["condicion"].replace("_", " "))

    # ---- Vista 3: 3D scatter triadic ----
    st.markdown("### Mapa triádico (T, I, F) de las condiciones causales")
    fig = px.scatter_3d(
        nfs_df, x="T", y="I", z="F", color="condicion",
        size=[40] * len(nfs_df), hover_data=["descripcion", "regimen"],
        height=500,
    )
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="T (consenso afirmativo)", range=[0, 1]),
            yaxis=dict(title="I (disagreement)", range=[0, 1]),
            zaxis=dict(title="F (omisión/desestima)", range=[0, 1]),
        ),
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---- Vista 4: contraste con encuesta ----
    st.markdown("### Contraste prensa vs encuesta estructural")
    st.caption("¿Qué silencia la prensa? ¿Qué amplifica? Mapeo curado en `narrativa_mediatica.py`.")

    # Calcular promedios estructurales del dataset
    struct_means = {col: float(agg_df[col].mean()) for col in DRIVER_COLS + OUTCOME_COLS}
    contrast_df = contrast_with_structural(nfs_df, struct_means)

    # Color rows by interpretation
    def color_interp(val):
        if "AMPLIFICADA" in str(val):
            return "background-color: #FFCDD2"
        if "SILENCIADA" in str(val):
            return "background-color: #C5CAE9"
        if "Alineada" in str(val):
            return "background-color: #C8E6C9"
        return ""

    st.dataframe(
        contrast_df.style.applymap(color_interp, subset=["interpretacion"]),
        use_container_width=True, hide_index=True,
    )

    st.info("""
    💡 **Interpretación pluriversal del contraste:**

    - **AMPLIFICADA** (gap > +0.3): la prensa enfatiza esta causa MÁS que la
      evidencia estructural lo justifica. Posible sesgo de **espectacularización**
      o cobertura sensacionalista.
    - **SILENCIADA** (gap < −0.3): la prensa subreporta una causa que aparece
      fuerte en la encuesta. Posible sesgo de **invisibilización** estructural
      (drivers económicos, gobernanza débil, exclusión social).
    - **Alineada**: la narrativa mediática coincide con la evidencia estructural.

    Este análisis es la base operativa para el argumento decolonial: ¿qué causas
    son hegemónicas en la prensa y cuáles son sistemáticamente subreportadas?
    """)

    with st.expander("📖 Sobre el método N-fsQCA"):
        st.markdown("""
        El **fsQCA tradicional** (Ragin 2008) usa membership fuzzy en [0,1] para clasificar
        casos en configuraciones causales y calcular consistency/coverage.

        Este módulo extiende fsQCA a **N-fsQCA** (Neutrosophic fsQCA): cada condición
        produce un triplete `(T, I, F)` donde:

        - **T** se calcula como el consenso ponderado de fuentes que afirman la causa
          (peso = `confidence_textual` del LLM extractor).
        - **F** captura el consenso de fuentes que omiten o desestiman la causa.
        - **I** mide la **varianza** entre fuentes — alta cuando diferentes medios
          enfatizan la misma causa con intensidades muy distintas.

        El régimen `C5_paraconsistente` (T+F>1) aparece cuando un grupo de fuentes
        afirma una causa con fuerza Y otro grupo la niega activamente. Es información
        estructural sobre la disputa narrativa, no ruido a eliminar.

        **Diferencia con MVP de Gemini CLI**: el MVP usaba crisp (0/1) y solo polaridad +.
        Este módulo lleva el análisis al espacio fuzzy + neutrosófico.
        """)


# =================================================================
# PAGINA 6 — GEMELO DIGITAL: SIMULACIÓN CONTRAFACTUAL
# =================================================================
elif pagina == "🔮 Gemelo Digital — Simulación contrafactual":
    st.title("🔮 Gemelo Digital Urbano — Simulación contrafactual")
    st.caption("Aplique virtualmente intervenciones del catálogo no-policial y vea el impacto "
               "esperado en (T, I, F) del sector. NO modifica el estado real del twin.")
    log_audit("page_simulacion_twin", st.session_state.user_purpose)

    # Selector sector + intervención
    col1, col2 = st.columns(2)
    sectores = sorted(agg_df["sector_demo"].unique())
    sector_sel = col1.selectbox("Sector:", sectores, index=20)

    nombres_iv = [iv.nombre for iv in CATALOGO]
    iv_sel = col2.selectbox("Intervención (catálogo no-policial):", nombres_iv)

    # Botón simular
    if st.button("▶️ Simular impacto", type="primary"):
        sim = twin.simulate_intervention(sector_sel, iv_sel)
        st.session_state["last_sim"] = sim
        st.success(f"Simulación completada para **{sector_sel}** con **{iv_sel}**.")

    # Mostrar resultados de la última simulación
    if "last_sim" in st.session_state:
        sim = st.session_state["last_sim"]
        st.markdown("---")
        st.markdown(f"### Resultado: {sim['intervencion']} en {sim['sector']}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Costo USD", f"${sim['intervencion_costo_usd']:,}")
        col2.metric("Tiempo (meses)", sim['intervencion_meses'])
        col3.metric("Indicadores afectados", len(sim['indicadores_afectados']))

        st.caption(f"**Indicadores afectados:** {', '.join(sim['indicadores_afectados'])}")
        st.caption(f"**Evidencia comparativa:** {sim['intervencion_evidencia']}")

        # Comparación antes/después
        st.markdown("#### Estado antes vs después (triplete agregado del sector)")
        comp_df = pd.DataFrame({
            "Componente": ["T (riesgo)", "I (indeterminación)", "F (resiliencia)"],
            "Antes": [sim["antes"]["T"], sim["antes"]["I"], sim["antes"]["F"]],
            "Después": [sim["despues"]["T"], sim["despues"]["I"], sim["despues"]["F"]],
            "Δ": [sim["delta"]["dT"], sim["delta"]["dI"], sim["delta"]["dF"]],
        })

        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.dataframe(
                comp_df.style.format({"Antes": "{:.3f}", "Después": "{:.3f}", "Δ": "{:+.3f}"})
                              .background_gradient(subset=["Antes", "Después"], cmap="RdYlGn_r"),
                use_container_width=True, hide_index=True,
            )
        with col_b:
            # Bar chart antes/después
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Antes",
                                  x=["T", "I", "F"],
                                  y=[sim["antes"]["T"], sim["antes"]["I"], sim["antes"]["F"]],
                                  marker_color="#C62828"))
            fig.add_trace(go.Bar(name="Después",
                                  x=["T", "I", "F"],
                                  y=[sim["despues"]["T"], sim["despues"]["I"], sim["despues"]["F"]],
                                  marker_color="#2E7D32"))
            fig.update_layout(barmode="group", height=300, yaxis=dict(range=[0, 1]),
                              margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

        # Régimen
        col_r1, col_r2 = st.columns(2)
        col_r1.info(f"**Régimen antes:** {sim['antes']['regimen']}")
        col_r2.success(f"**Régimen después:** {sim['despues']['regimen']}")

        # Bloque para REGISTRAR aplicación real (feedback bidireccional)
        st.markdown("---")
        st.markdown("### 📝 Registrar como intervención real (feedback bidireccional)")
        st.caption("Solo si la intervención fue formalmente aprobada por el comité comunitario.")

        with st.form("registrar_iv"):
            estado = st.radio("Estado de aplicación:",
                              ["planificada", "en_curso", "completada"],
                              horizontal=True)
            aprobado = st.checkbox("✅ Aprobación comunitaria firmada")
            presup = st.number_input("Presupuesto real (USD):",
                                      min_value=0,
                                      value=sim['intervencion_costo_usd'])
            notas = st.text_area("Notas / actor responsable:",
                                  placeholder="Ej.: GAD Guayaquil — Acción Social — partnership UBE")
            submit = st.form_submit_button("💾 Registrar en historial del twin")

            if submit:
                if not aprobado and estado != "planificada":
                    st.error("❌ Solo se permiten registros 'planificada' sin aprobación comunitaria firmada.")
                else:
                    record = twin.apply_intervention(
                        sector=sim["sector"],
                        intervencion_nombre=sim["intervencion"],
                        estado=estado,
                        aprobacion_comunitaria=aprobado,
                        presupuesto_real_usd=presup,
                        notas=notas,
                    )
                    twin.take_snapshot(
                        label=f"post_{sim['intervencion'][:20]}_{record.timestamp[:10]}",
                        notes=f"{notas} (registro humano)",
                    )
                    st.success(f"✅ Registrado. Snapshot capturado. Total intervenciones: {len(twin.interventions_applied)}")
                    st.info("El twin actualizó su estado. Vaya a la página 'Estado del Gemelo' para ver la evolución.")


# =================================================================
# PAGINA 7 — ESTADO DEL GEMELO (sincronización + historial)
# =================================================================
elif pagina == "📡 Estado del Gemelo (sincronización)":
    st.title("📡 Estado del Gemelo Digital")
    st.caption("Snapshots históricos, intervenciones aplicadas, evolución temporal.")
    log_audit("page_estado_twin", st.session_state.user_purpose)

    # Métricas del estado actual
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Snapshots almacenados", len(twin.snapshots))
    col2.metric("Intervenciones aplicadas", len(twin.interventions_applied))
    col3.metric("Sectores monitoreados", len(twin.structural_data_agg))
    col4.metric("Última actualización",
                twin.snapshots[-1].timestamp[:16].replace("T", " "))

    st.markdown("---")

    # Evolución temporal
    st.markdown("### Evolución temporal del estado del twin")
    series = twin.temporal_series()
    if len(series) > 1:
        fig = px.line(series, x="label", y=["T_promedio", "I_promedio", "F_promedio"],
                      markers=True, height=380,
                      title="Promedio agregado de T, I, F por snapshot")
        fig.update_layout(yaxis=dict(range=[0, 1]),
                          xaxis=dict(title="Snapshot"),
                          yaxis_title="Valor agregado")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Solo existe el snapshot baseline. Aplique intervenciones desde la página "
                "**Simulación contrafactual** para generar nuevos snapshots y ver evolución.")

    # Tabla de snapshots
    st.markdown("### Tabla de snapshots")
    snap_data = []
    for s in twin.snapshots:
        snap_data.append({
            "timestamp": s.timestamp[:16].replace("T", " "),
            "label": s.label,
            "n_intervenciones": s.n_interventions_applied,
            "notas": s.notes[:80] + ("..." if len(s.notes) > 80 else ""),
        })
    st.dataframe(pd.DataFrame(snap_data), use_container_width=True, hide_index=True)

    # Tabla de intervenciones aplicadas
    st.markdown("### Intervenciones registradas")
    if twin.interventions_applied:
        ia_data = []
        for ia in twin.interventions_applied:
            ia_data.append({
                "timestamp": ia.timestamp[:16].replace("T", " "),
                "sector": ia.sector,
                "intervencion": ia.intervencion_nombre,
                "estado": ia.estado_aplicacion,
                "aprobacion_comunitaria": "✅" if ia.aprobacion_comunitaria else "❌",
                "presupuesto_usd": f"${ia.presupuesto_real_usd:,}",
                "notas": ia.notas[:60] + ("..." if len(ia.notas) > 60 else ""),
            })
        st.dataframe(pd.DataFrame(ia_data), use_container_width=True, hide_index=True)
    else:
        st.info("No se han registrado intervenciones todavía.")

    st.markdown("---")
    st.markdown("### Las 4 propiedades del Gemelo Digital legítimo")
    propiedades = pd.DataFrame([
        {"Propiedad": "Sincronización temporal",
         "Implementación actual": "Snapshots con timestamp + estado persistente JSON",
         "Estado": "✅ Operativo (mock; falta ingesta en vivo)"},
        {"Propiedad": "Simulación contrafactual",
         "Implementación actual": "Método simulate_intervention() en digital_twin.py",
         "Estado": "✅ Operativo"},
        {"Propiedad": "Feedback bidireccional",
         "Implementación actual": "apply_intervention() + take_snapshot() + persistencia JSONL",
         "Estado": "✅ Operativo"},
        {"Propiedad": "Granularidad espacio-temporal",
         "Implementación actual": "Sector (28 unidades, ≥5K hab.) + snapshots manuales",
         "Estado": "🟡 Parcial (snapshots a demanda; falta cron mensual)"},
    ])
    st.dataframe(propiedades, use_container_width=True, hide_index=True)

    # Botón admin: reset
    st.markdown("---")
    with st.expander("⚠️ Administración (solo committee approval)"):
        st.warning("Reset borra todos los snapshots e intervenciones registradas.")
        if st.button("🗑️ Reset twin (con auditoría)"):
            twin.reset()
            st.success("Twin reset al estado baseline. Operación auditada.")
            st.rerun()


# =================================================================
# PAGINA 8 — CAPAS EXTENDIDAS: GENERO + ILUMINACION + PARACONSISTENCIA
# =================================================================
elif pagina == "🔬 Capas extendidas: Género + Iluminación + Paraconsistencia":
    st.title("🔬 Capas extendidas del Gemelo Digital")
    st.caption("Tres extensiones del programa: violencia de género, iluminación nocturna satelital, "
               "y detector automático de paraconsistencia entre fuentes.")
    log_audit("page_capas_extendidas", st.session_state.user_purpose)

    st.warning("⚠️ Datos demostrativos sintéticos. Para datos reales: convenios con Defensoría del "
               "Pueblo Guayas (VG), NASA Earthdata (iluminación), MSP / MINEDUC (resto).")

    tab1, tab2, tab3 = st.tabs([
        "🚺 Violencia de Género",
        "💡 Iluminación nocturna",
        "🔍 Detector de paraconsistencia"
    ])

    # ------- TAB 1: VG -------
    with tab1:
        st.markdown("### Capa de violencia de género y feminicidio")
        st.caption("Indicadores: tasa feminicidio · denuncias VG · casas acogida · DECE · DEVIF · "
                   "programas prevención · femicidios pendientes · víctimas protegidas.")

        vg_raw = synthetic_gender_data()
        vg_risk = gender_risk_score(vg_raw)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Sectores VG paraconsistentes",
                    f"{int(vg_risk['paraconsistente_VG'].sum())}/{len(vg_risk)}")
        col2.metric("Tasa media feminicidios/100K",
                    f"{vg_raw['tasa_feminicidio_100k'].mean():.2f}")
        col3.metric("Casas de acogida totales",
                    int(vg_raw['casas_acogida_disponibles'].sum()))
        col4.metric("Víctimas con medidas de protección",
                    int(vg_raw['victimas_protegidas_activas'].sum()))

        st.markdown("#### Indicadores VG por sector")
        st.dataframe(
            vg_raw[["sector"] + GENDER_INDICATORS].style
                  .background_gradient(subset=["tasa_feminicidio_100k", "denuncias_vg_100hog"],
                                        cmap="Reds")
                  .background_gradient(subset=["centros_dece_activos_pct", "cobertura_devif"],
                                        cmap="Greens"),
            use_container_width=True, hide_index=True, height=320,
        )

        st.markdown("#### Triplete (T, I, F) por sector — riesgo VG")
        fig_vg = px.scatter_3d(
            vg_risk, x="T_riesgo_VG", y="I_indeterminacion_VG", z="F_proteccion_VG",
            color="regimen_VG", hover_data=["sector"],
            height=480,
        )
        fig_vg.update_layout(
            scene=dict(
                xaxis=dict(title="T (riesgo VG)", range=[0, 1]),
                yaxis=dict(title="I (indeterm.)", range=[0, 1]),
                zaxis=dict(title="F (protección)", range=[0, 1]),
            ),
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig_vg, use_container_width=True)

        st.info("""
        💡 **Hallazgo típico**: la mayoría de sectores muestran régimen paraconsistente VG.
        Esto refleja una realidad estructural: **coexisten** evidencias de riesgo (denuncias,
        feminicidios) y evidencias de protección (programas, casas de acogida) en los mismos sectores.
        El framework neutrosófico permite verlo sin colapsar uno en el otro.

        **Funders potenciales**: ONU Mujeres, Open Society Women's Rights, Plan Internacional Ecuador,
        CEPAM, Casa Trans Guayaquil, María Guare.
        """)

    # ------- TAB 2: ILUMINACION -------
    with tab2:
        st.markdown("### Capa de iluminación nocturna satelital")
        st.caption("Indicadores: radiance promedio · coef. variación · áreas blackout · postes funcionales · "
                   "cobertura iluminación. Fuente conceptual: NASA Black Marble VIIRS DNB.")

        nl_raw = synthetic_nightlight()
        nl_tif = nightlight_to_tif(nl_raw)

        col1, col2, col3 = st.columns(3)
        col1.metric("Radiance media",
                    f"{nl_raw['radiance_promedio_nW'].mean():.1f} nW/cm²/sr")
        col2.metric("Blackouts totales",
                    f"{int(nl_raw['blackout_areas_m2'].sum()):,} m²")
        col3.metric("Cobertura iluminación media",
                    f"{nl_raw['cobertura_iluminacion_pct'].mean():.0f}%")

        st.markdown("#### Indicadores por sector con tipo de zona")
        st.dataframe(
            nl_raw.style
                .background_gradient(subset=["radiance_promedio_nW", "cobertura_iluminacion_pct",
                                              "postes_funcionales_km"], cmap="YlGn")
                .background_gradient(subset=["coef_variacion_lum", "blackout_areas_m2"], cmap="Reds"),
            use_container_width=True, hide_index=True, height=320,
        )

        st.markdown("#### Distribución de regímenes por iluminación")
        reg_count = nl_tif["regimen_LUZ"].value_counts().reset_index()
        reg_count.columns = ["regimen", "n_sectores"]
        fig_pie_luz = px.pie(reg_count, values="n_sectores", names="regimen", height=350)
        st.plotly_chart(fig_pie_luz, use_container_width=True)

        st.info("""
        💡 **Cómo se usa**: el módulo permite **validar empíricamente** la intervención #1 del
        catálogo (iluminación pública focalizada). Sectores con `T_LUZ` alto + `F_LUZ` bajo son
        candidatos prioritarios. Sectores rurales/insulares (Tenguel, Posorja, Puná) muestran
        sistemáticamente mayor riesgo lumínico estructural.

        **Datos reales disponibles vía**: NASA Earthdata Worldview, Colorado School of Mines EOG,
        World Bank Light Every Night dataset (gratuitos, requieren registro).
        """)

    # ------- TAB 3: DETECTOR DE PARACONSISTENCIA -------
    with tab3:
        st.markdown("### Detector automático de paraconsistencia entre fuentes")
        st.caption("Cierra el círculo entre Third Answer + Trichotomy refactorizado + N-fsQCA + IPVE. "
                   "Cruza 4 fuentes independientes (estructural, narrativa, género, iluminación).")

        with st.spinner("Recolectando 4 fuentes y aplicando SVNWA..."):
            merged = collect_all_sources_per_sector()
            detection = detect_paraconsistency(merged)

        col1, col2, col3 = st.columns(3)
        col1.metric("Sectores paraconsistentes (agregado)",
                    f"{int(detection['paraconsistente_agregado'].sum())}/{len(detection)}")
        col2.metric("Sectores paraconsistentes cross-source",
                    f"{int(detection['paraconsistente_cross_source'].sum())}/{len(detection)}")
        col3.metric("Disputa epistémica media",
                    f"{detection['indice_disputa_epistemica'].mean():.3f}")

        st.markdown("#### Tabla de detección por sector")
        st.dataframe(
            detection.style
                .background_gradient(subset=["T_agregado"], cmap="Reds")
                .background_gradient(subset=["I_agregado"], cmap="Blues")
                .background_gradient(subset=["F_agregado"], cmap="Greens")
                .background_gradient(subset=["indice_disputa_epistemica"], cmap="Purples"),
            use_container_width=True, hide_index=True, height=350,
        )

        st.markdown("#### Top 10 sectores en disputa epistémica")
        st.caption("Donde la deliberación comunitaria tiene mayor valor: las fuentes contradicen.")
        top = disputed_sectors_summary(detection)
        st.dataframe(
            top[["sector", "indice_disputa_epistemica", "fuente_max_riesgo",
                  "fuente_max_proteccion", "regimen_agregado"]],
            use_container_width=True, hide_index=True,
        )

        st.markdown("#### Visualización: ¿qué fuente domina el riesgo y la protección por sector?")
        cross = pd.DataFrame({
            "sector": detection["sector"],
            "fuente_riesgo_dominante": detection["fuente_max_riesgo"],
            "fuente_proteccion_dominante": detection["fuente_max_proteccion"],
            "es_paraconsistente_cross": detection["paraconsistente_cross_source"],
        })
        riesgo_count = cross["fuente_riesgo_dominante"].value_counts().reset_index()
        riesgo_count.columns = ["fuente", "n_sectores"]
        proteccion_count = cross["fuente_proteccion_dominante"].value_counts().reset_index()
        proteccion_count.columns = ["fuente", "n_sectores"]

        col_a, col_b = st.columns(2)
        with col_a:
            fig_r = px.bar(riesgo_count, x="fuente", y="n_sectores",
                           title="Fuente que más reporta riesgo (T)",
                           color="fuente", color_discrete_sequence=["#C62828", "#FF9800",
                                                                       "#9C27B0", "#FFC107"])
            st.plotly_chart(fig_r, use_container_width=True)
        with col_b:
            fig_p = px.bar(proteccion_count, x="fuente", y="n_sectores",
                           title="Fuente que más reporta protección (F)",
                           color="fuente", color_discrete_sequence=["#2E7D32", "#4CAF50",
                                                                       "#8BC34A", "#CDDC39"])
            st.plotly_chart(fig_p, use_container_width=True)

        st.success("""
        ✅ **Esto es el aporte del programa Pluriversal Alignment funcionando en producción**:

        Si **estructura** dice un sector está bien pero **género** dice mal Y **luz** dice bien Y
        **narrativa** dice mal — el sector NO es coherente. La paraconsistencia (T+F>1) es
        información estructural sobre la disputa, no error a eliminar.

        Esto es exactamente lo que The Third Answer (Leyva-Vázquez & Smarandache, 2026)
        argumenta filosóficamente y este módulo demuestra empíricamente.
        """)


# =================================================================
# PAGINA 9 — PERCEPCION COMUNITARIA PARTICIPATIVA
# =================================================================
elif pagina == "🗣️ Percepción comunitaria (participativa)":
    st.title("🗣️ Percepción comunitaria participativa")
    st.markdown(
        "Registra tu percepción **(T, I, F)** sobre la seguridad y vulnerabilidad "
        "de un sector. **T** y **F** NO son complementos — pueden ser ambos altos "
        "si el sector tiene evidencia simultánea de riesgo y de resiliencia."
    )
    log_audit("page_participativa", st.session_state.user_purpose)

    # ── session_id único por pestaña de navegador ──────────────────
    import hashlib, time
    if "part_session_id" not in st.session_state:
        st.session_state.part_session_id = hashlib.md5(
            str(time.time_ns()).encode()
        ).hexdigest()[:8]
    if "part_submitted" not in st.session_state:
        st.session_state.part_submitted = False

    tab_form, tab_resultados = st.tabs(["📝 Registrar mi percepción", "📊 Ver respuestas del grupo"])

    # ─────────────── TAB FORMULARIO ───────────────────────────────
    with tab_form:
        if st.session_state.part_submitted:
            st.success("✅ Tu percepción fue registrada. Revisa la pestaña **Ver respuestas del grupo**.")
            if st.button("Registrar otra respuesta (sector diferente)"):
                st.session_state.part_submitted = False
                st.rerun()
        else:
            with st.form("form_participativo", clear_on_submit=False):
                st.markdown("### 1. Identifícate")
                col_r, col_s = st.columns(2)
                rol_sel = col_r.selectbox("Tu rol:", ROLES)
                sectores_lista = sorted(agg_df["sector_demo"].unique())
                sector_sel_p = col_s.selectbox(
                    "Sector que evalúas:",
                    sectores_lista,
                    help="Elige el sector que mejor conoces o del que quieres opinar.",
                )
                contexto = st.text_input(
                    "¿Por qué conoces este sector? (opcional)",
                    placeholder="Ej: vivo ahí, hice trabajo de campo, soy de la zona...",
                    max_chars=120,
                )

                st.markdown("---")
                st.markdown("### 2. Evalúa cada dimensión con tres deslizadores")
                st.info(
                    "**T** = convicción de que el RIESGO es real  ·  "
                    "**I** = tu INCERTIDUMBRE al responder  ·  "
                    "**F** = convicción de que hay RESILIENCIA activa\n\n"
                    "🔑 **Clave**: T + F > 1 es posible y significa paraconsistencia "
                    "(riesgo real Y resiliencia real al mismo tiempo)."
                )

                percepciones: dict[str, dict[str, float]] = {}
                for dim_key, dim_info in DIMENSIONES.items():
                    st.markdown(f"#### {dim_info['label']}")
                    st.caption(dim_info["descripcion"])
                    c1, c2, c3 = st.columns(3)
                    T_val = c1.slider(
                        f"T — {dim_info['T_pregunta'][:40]}…",
                        0.0, 1.0, 0.5, 0.05,
                        key=f"{dim_key}_T",
                        help=dim_info["T_pregunta"],
                    )
                    I_val = c2.slider(
                        f"I — {dim_info['I_pregunta'][:40]}…",
                        0.0, 1.0, 0.3, 0.05,
                        key=f"{dim_key}_I",
                        help=dim_info["I_pregunta"],
                    )
                    F_val = c3.slider(
                        f"F — {dim_info['F_pregunta'][:40]}…",
                        0.0, 1.0, 0.4, 0.05,
                        key=f"{dim_key}_F",
                        help=dim_info["F_pregunta"],
                    )
                    regime = regime_label(T_val, F_val, I_val)
                    color = (
                        "#6A1B9A" if "PARACONSISTENTE" in regime else
                        "#C62828" if "C1" in regime else
                        "#2E7D32" if "C2" in regime else
                        "#FFA000" if "C3" in regime else
                        "#1976D2"
                    )
                    st.markdown(
                        f"<span style='color:{color};font-size:0.85em'>"
                        f"→ Régimen: <b>{regime}</b></span>",
                        unsafe_allow_html=True,
                    )
                    percepciones[dim_key] = {"T": T_val, "I": I_val, "F": F_val}

                st.markdown("---")
                notas = st.text_area(
                    "Notas libres (opcional) — contexto cualitativo que los números no capturan:",
                    placeholder="Ej: 'El sector tiene murales comunitarios activos pero los fines de semana hay balaceras...'",
                    max_chars=400,
                )

                submitted = st.form_submit_button("💾 Registrar mi percepción", type="primary")
                if submitted:
                    ok = save_response(
                        session_id=st.session_state.part_session_id,
                        sector=sector_sel_p,
                        rol=rol_sel,
                        contexto=contexto,
                        percepciones=percepciones,
                        notas=notas,
                    )
                    if ok:
                        st.session_state.part_submitted = True
                        st.rerun()

    # ─────────────── TAB RESULTADOS ───────────────────────────────
    with tab_resultados:
        df_part = load_responses()
        if df_part.empty:
            st.info("Aún no hay respuestas registradas. Sé el primero en contribuir.")
        else:
            st.markdown(f"### {len(df_part)} respuesta(s) registradas en esta sesión")

            # Métricas globales
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total respuestas", len(df_part))
            col2.metric("Sectores cubiertos", df_part["sector"].nunique())
            col3.metric("Roles distintos", df_part["rol"].nunique())
            para_pct = 0
            if len(df_part) > 0:
                t_mean = df_part[["seg_T","vg_T","infra_T","gob_T","cohesion_T"]].mean(axis=1).mean()
                f_mean = df_part[["seg_F","vg_F","infra_F","gob_F","cohesion_F"]].mean(axis=1).mean()
                para_pct = round(100 * (t_mean + f_mean > 1.0), 0)
            col4.metric("Respuestas paraconsistentes", f"{int((df_part[['seg_T','vg_T','infra_T','gob_T','cohesion_T']].mean(axis=1) + df_part[['seg_F','vg_F','infra_F','gob_F','cohesion_F']].mean(axis=1) > 1.0).sum())}")

            # Agregado por sector
            agg_part = aggregate_by_sector(df_part)
            if not agg_part.empty:
                st.markdown("### Triplete participativo por sector")
                st.dataframe(
                    agg_part[["sector","n_respuestas","T_part","I_part","F_part","paraconsistente"]]
                    .rename(columns={"T_part":"T","I_part":"I","F_part":"F","paraconsistente":"Paracons."})
                    .style.background_gradient(subset=["T"], cmap="Reds")
                          .background_gradient(subset=["I"], cmap="Blues")
                          .background_gradient(subset=["F"], cmap="Greens"),
                    use_container_width=True, hide_index=True,
                )

                # Mapa 3D participativo
                st.markdown("### Mapa triádico de percepciones comunitarias")
                fig_p = px.scatter_3d(
                    agg_part,
                    x="T_part", y="I_part", z="F_part",
                    color="paraconsistente",
                    color_discrete_map={True: "#6A1B9A", False: "#1976D2"},
                    size="n_respuestas",
                    hover_data=["sector", "n_respuestas"],
                    height=480,
                )
                fig_p.update_layout(
                    scene=dict(
                        xaxis=dict(title="T (riesgo percibido)", range=[0, 1]),
                        yaxis=dict(title="I (incertidumbre)", range=[0, 1]),
                        zaxis=dict(title="F (resiliencia percibida)", range=[0, 1]),
                    ),
                    margin=dict(l=0, r=0, t=20, b=0),
                )
                st.plotly_chart(fig_p, use_container_width=True)

            # Dimensión más disputada
            st.markdown("### Dimensión con mayor incertidumbre promedio")
            i_means = {
                "Seguridad general": df_part["seg_I"].mean(),
                "Violencia de género": df_part["vg_I"].mean(),
                "Infraestructura": df_part["infra_I"].mean(),
                "Gobernanza": df_part["gob_I"].mean(),
                "Cohesión social": df_part["cohesion_I"].mean(),
            }
            dim_max_I = max(i_means, key=i_means.get)
            st.warning(
                f"📌 La dimensión con **mayor incertidumbre** entre los participantes es "
                f"**{dim_max_I}** (I promedio = {i_means[dim_max_I]:.2f}). "
                f"Esto señala una prioridad de **levantamiento de datos comunitario**."
            )

            # Tabla raw
            with st.expander("Ver respuestas individuales (anonimizadas)"):
                st.dataframe(
                    df_part.drop(columns=["session_id","contexto_relacion","notas_libres"],
                                  errors="ignore"),
                    use_container_width=True, height=280,
                )

            # Botón descarga
            csv_export = df_part.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Descargar respuestas (CSV)",
                data=csv_export,
                file_name=f"percepcion_comunitaria_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )

            st.info("""
            💡 **Hallazgos típicos esperados en clase:**

            - Estudiantes de un mismo sector suelen dar **T y F ambos altos** →
              paraconsistencia real: ellos mismos viven tanto el riesgo como la resiliencia.
            - La dimensión **gobernanza** suele tener **I alto**: nadie sabe bien qué tan
              funcionales son las instituciones en su sector.
            - Los regímenes divergen por **rol**: residentes dan T más alto que estudiantes
              que solo conocen el sector por datos.
            """)


# =================================================================
# PAGINA 10 — AUDITORIA Y SALVAGUARDAS
# =================================================================
elif pagina == "📋 Auditoría y salvaguardas":
    st.title("📋 Auditoría y salvaguardas éticas")
    log_audit("page_auditoria", st.session_state.user_purpose)

    st.markdown("### Audit log público (últimas 50 consultas)")
    log_data = read_audit_log(50)
    if log_data:
        log_df = pd.DataFrame(log_data)
        st.dataframe(log_df, use_container_width=True, height=300)
    else:
        st.info("No hay entradas en el audit log todavía.")

    st.markdown("### Salvaguardas activas")
    st.markdown("""
    | Salvaguarda | Estado | Cómo se aplica |
    |---|---|---|
    | Granularidad mínima: sector | ✅ activa | `MIN_GRANULARITY = sector` en `ethical_safeguards.py` |
    | Bloqueo de propósito comercial | ✅ activa | función `check_purpose()` valida 17 términos prohibidos |
    | Audit log público | ✅ activa | archivo `audit_log.jsonl` lee/escribe por sesión |
    | Disclaimer obligatorio en exports | ✅ activa | función `get_disclaimer()` |
    | Bloqueo ranking sin (T,I,F) | ✅ activa | función `block_simple_ranking()` |
    | Solo intervenciones no-policiales | ✅ activa | catálogo `CATALOGO` excluye despliegue policial |
    """)

    st.markdown("### Aviso ético completo")
    st.code(get_disclaimer())


# =================================================================
# PAGINA 6 — MARCO TEORICO
# =================================================================
elif pagina == "📚 Marco teórico y citas":
    st.title("📚 Marco teórico y referencias")
    log_audit("page_marco_teorico", st.session_state.user_purpose)

    st.markdown("""
    ### Fundamento neutrosófico

    El tablero opera bajo lógica neutrosófica refinada (Smarandache, 1998;
    Wang, Smarandache, Zhang & Sunderraman, 2010), donde cada proposición
    se representa como triplete `(T, I, F) ∈ [0, 1]³` **sin restricción de suma**.

    La elección de no colapsar `(T, I, F)` en un escalar como
    `IVN = T·w₁ + I·w₂ − F·w₃` (que era la fórmula propuesta originalmente
    en el archivo `200_ANALISIS_DATOS_VULNERABILIDAD.md`) es deliberada.
    Sumar `T` (evidencia direccional positiva) con `I` (gap epistémico
    no direccional) y restar `F` (evidencia direccional negativa) **mezcla
    categorías ontológicamente heterogéneas** y reproduce exactamente el
    error que la neutrosofía formal busca evitar.

    El reemplazo correcto, IPVE (Índice Pluriversal de Vulnerabilidad
    Estructural), preserva el vector triádico y solo produce escalares
    para triage, siempre acompañados del triplete subyacente.

    ### Posicionamiento decolonial / pluriversal

    Esta plataforma se inscribe en el programa Pluriversal Alignment
    descrito en:

    - Smarandache, F. & Leyva-Vázquez, M. Y. (2026). **Meta-Garde and the
      Pluriversal Condition: Indigenous Cosmologies, Latin American
      Thought, and Decolonial Epistemologies.** NSIA Publishing House.
      ISBN 978-1-59973-885-7.

    - Leyva-Vázquez, M. Y. & Smarandache, F. (2026, en preparación).
      **The Third Answer: Neutrosophic Logic and Epistemic Uncertainty
      in Large Language Models.** NSIA Publishing House.

    - Mhlambi, S. (2020). **From rationality to relationality: Ubuntu
      as an ethical and human rights framework for AI governance.**
      Carr Center Discussion Paper 2020-009.

    - Birhane, A. (2021). **Algorithmic injustice: a relational ethics
      approach.** Patterns, 2(2), 100205.

    ### Crítica al predictive policing (que esta plataforma evita)

    - Lum, K. & Isaac, W. (2016). **To predict and serve?** Significance,
      13(5), 14–19. (Documenta cómo PredPol amplifica el sesgo racial.)

    - Richardson, R., Schultz, J. M. & Crawford, K. (2019). **Dirty data,
      bad predictions.** NYU Law Review Online, 94, 192–233.

    ### Catálogo de intervenciones (evidencia LATAM)

    Cada intervención del catálogo cita un caso documentado en LATAM con
    métrica de reducción atribuible. Ver `interventions_db.py` para
    detalle de cada referencia.
    """)


# =================================================================
# FOOTER GLOBAL
# =================================================================
st.markdown("---")
st.caption(
    "Guayaquil Neutro-Safe v1.0 · Tablero Pluriversal · Camino B  ·  "
    "Universidad Bolivariana del Ecuador  ·  Lic. MIT  ·  "
    "Comité ético: UBE + Defensoría del Pueblo Guayas + 3 representantes barriales rotativos"
)

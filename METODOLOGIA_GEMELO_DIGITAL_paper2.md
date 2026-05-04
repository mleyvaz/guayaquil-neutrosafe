# Metodología — Gemelo Digital Neutro-Safe como artefacto empírico
## Sección Methods para Inter-Narrative LLM + N-fsQCA paper

---

### 3. Metodología

#### 3.1 Diseño general

Se adoptó un diseño de múltiples fuentes con detección de paraconsistencia
(Smarandache, 1998; Leyva-Vázquez & Smarandache, 2026) implementado como
un gemelo digital urbano operativo (Tao et al., 2019). El sistema integra
cuatro capas independientes de información sobre los 28 sectores urbanos del
cantón Guayaquil, Ecuador, y aplica la Weighted Average Neutrosófica
(Wang et al., 2010) para detectar conflictos epistémicos entre fuentes.

#### 3.2 El gemelo digital como instrumento de diagnóstico

Un gemelo digital legítimo requiere cuatro propiedades operativas
(Grieves & Vickers, 2017): sincronización temporal, simulación contrafactual,
retroalimentación bidireccional y granularidad espacio-temporal.
La plataforma implementa las cuatro:

| Propiedad              | Implementación                                                |
|------------------------|---------------------------------------------------------------|
| Sincronización         | Snapshots con timestamp; ingesta de fuentes abiertas         |
| Simulación             | `simulate_intervention()` con catálogo de 8 acciones no-policiales |
| Retroalimentación      | `apply_intervention()` + registro de aprobación comunitaria   |
| Granularidad           | Sector (≥5,000 hab.) + percepción comunitaria participativa   |

La granularidad mínima de sector —nunca de individuo o manzana— es una
decisión de diseño ética documentada en la Gobernanza Camino B
(archivo 500_GOBERNANZA_ETICA_CAMINO_B.md), que diferencia esta
plataforma del predictive policing (Lum & Isaac, 2016).

#### 3.3 Capa 1 — Estado estructural (IPVE)

Se utilizó la Encuesta de Percepción de Violencia Urbana (n=151
observaciones, Guayaquil 2023-2024) con 14 indicadores: 11 conductores
estructurales (desempleo, pobreza, brecha de ingresos, desintegración
familiar, presencia de pandillas, falta de espacios públicos, infraestructura
deficiente, insuficiencia policial, políticas ineficaces, corrupción,
legislación deficiente) y 3 indicadores de percepción de resultado
(percepción de violencia, violencia frecuente, sentimiento de inseguridad).

Para cada sector *s* e indicador *k* se calculó un triplete neutrosófico
$(T_{sk}, I_{sk}, F_{sk})$ mediante:

$$T_{sk} = \frac{1}{n_s}\sum_{j=1}^{n_s} x_{jk}, \quad
I_{sk} = 4 \cdot \frac{1}{n_s}\sum_{j=1}^{n_s}(x_{jk}-T_{sk})^2, \quad
F_{sk} = 1 - T_{sk}$$

donde $x_{jk}\in[0,1]$ es el valor normalizado de la observación *j*
en el indicador *k* dentro del sector *s*, e $I_{sk}$ captura la
varianza intra-sector como gap epistémico (Leyva-Vázquez et al., 2025).

El Índice Pluriversal de Vulnerabilidad Estructural (IPVE) agrega los 14
tripletes mediante SVNWA con pesos iguales:

$$\text{IPVE}(s) = \text{SVNWA}_{k=1}^{14}(T_{sk}, I_{sk}, F_{sk})$$

No se colapsa el IPVE en un escalar. Los rankings de triage se producen
únicamente con el score pesimista $T - F + 0.5\cdot I$, acompañado
obligatoriamente del triplete subyacente (salvaguarda anti-ranking
escalar, función `block_simple_ranking()` del módulo `ethical_safeguards.py`).

#### 3.4 Capa 2 — Análisis narrativo mediático (N-fsQCA)

Se aplicó la extensión neutrosófica del Qualitative Comparative Analysis
fuzzy (Ragin, 2008) —denominada N-fsQCA— a 16 noticias de medios de
comunicación de Guayaquil (2022-2024) sobre violencia urbana.

Para cada condición causal $c_i$ se extrajo, mediante LLM (GPT-4o con
prompt estandarizado), una puntuación de relevancia $r_{ij}\in[0,1]$
para la noticia $j$. El triplete N-fsQCA de la condición $c_i$ es:

$$T_i = \frac{\sum_j w_j \cdot r_{ij}}{\sum_j w_j}, \quad
F_i = \frac{\sum_j w_j \cdot (1-r_{ij})}{\sum_j w_j}, \quad
I_i = 4 \cdot \sigma^2(r_{i\cdot})$$

donde $w_j$ es la confianza del extractor LLM para la noticia $j$.

El hallazgo central (ver Resultados §4.2) es que los drivers estructurales
de alta prevalencia en Capa 1 (corrupción, brechaingresos, politicasineficaces)
son sistemáticamente subrepresentados en la narrativa mediática (gap > −0.30),
mientras que drivers de alta visibilidad (pandillas, violenciafrecuente)
son sobrerepresentados (gap > +0.30). Esta asimetría configura lo que el
programa Pluriversal Alignment denomina *silenciamiento estructural mediático*
(Leyva-Vázquez & Smarandache, 2026).

#### 3.5 Capa 3 — Violencia de género e iluminación

Se integraron dos capas adicionales usando indicadores de fuentes abiertas.
La capa de violencia de género incluye: tasa de feminicidio por 100,000
habitantes, denuncias de violencia de género por 100 hogares, cobertura
DEVIF, presencia de centros DECE activos, y número de casas de acogida.
La capa de iluminación nocturna usa el índice de radiancia NASA Black Marble
VIIRS DNB (VNP46A3 mensual) como proxy de déficit de infraestructura pública.

Ambas capas producen tripletes $(T, I, F)$ mediante el mismo procedimiento
de normalización de la Capa 1. La presencia de datos sintéticos en la
versión de demostración se declara explícitamente en la interfaz de usuario
(función `get_disclaimer()`).

#### 3.6 Capa 4 — Percepción comunitaria participativa

Se implementó un módulo de registro participativo donde estudiantes,
residentes y activistas registran su percepción $(T, I, F)$ sobre cinco
dimensiones (seguridad general, violencia de género, infraestructura,
gobernanza, cohesión social) para el sector de su elección.

Este diseño implementa la propuesta de *pluriversal data sovereignty*:
los datos de comunidades sobre sus propias condiciones no deben ser
sustituidos unilateralmente por datos institucionales, sino integrados
mediante el detector de paraconsistencia como fuente adicional con peso
propio (Mhlambi, 2020; Birhane, 2021).

#### 3.7 Detector de paraconsistencia cross-source

El detector (módulo `paraconsistency_detector.py`) aplica SVNWA a los
cuatro tripletes de sector $(T_\ell^s, I_\ell^s, F_\ell^s)$ con $\ell\in\{1,2,3,4\}$
para producir un triplete agregado y un *índice de disputa epistémica*:

$$\delta_s = \max_{\ell,\ell'} |T_\ell^s - T_{\ell'}^s| + |F_\ell^s - F_{\ell'}^s|$$

Valores altos de $\delta_s$ señalan sectores donde diferentes fuentes
contradicen su evaluación. Estos sectores —no los de T más alto— son
los candidatos prioritarios para deliberación comunitaria.

El hallazgo empírico clave: los centros formales de Guayaquil
(Roca/Urdesa, Bolívar/Sagrario, Carbo/Centro Bancario) presentan
simultáneamente alta iluminación (F alto en capa lumínica) y alta
incidencia de violencia de género (T alto en capa VG). Este régimen
paraconsistente —inaccesible a un índice escalar que sumaría ambas
señales— refuta la noción de "barrio seguro" construida únicamente
sobre infraestructura física, y conecta con la crítica feminista a los
modelos CPTED (Crime Prevention Through Environmental Design) que
sobreestiman el efecto de la iluminación en la seguridad de las mujeres
(Valentine, 1992; Whitzman et al., 2009).

---

### Referencias metodológicas clave

- Grieves, M., & Vickers, J. (2017). Digital twin: Mitigating unpredictable,
  undesirable emergent behavior in complex systems. In *Transdisciplinary
  perspectives on complex systems* (pp. 85-113). Springer.
- Lum, K., & Isaac, W. (2016). To predict and serve? *Significance*, 13(5), 14-19.
- Ragin, C. C. (2008). *Redesigning social inquiry*. University of Chicago Press.
- Smarandache, F. (1998). *Neutrosophy*. American Research Press.
- Tao, F., et al. (2019). Digital twin-driven product design, manufacturing and
  service with big data. *International Journal of Advanced Manufacturing Technology*.
- Wang, H., et al. (2010). Single valued neutrosophic sets. *Multispace & Multistructure*.
- Mhlambi, S. (2020). From rationality to relationality. *Carr Center Discussion Paper*.
- Birhane, A. (2021). Algorithmic injustice. *Patterns*, 2(2), 100205.

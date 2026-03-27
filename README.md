# Capstone_Project_Group 5

# EduYou RAG Data Pipeline

## Overview

This project prepares a **Retrieval‑Augmented Generation (RAG)**–ready dataset that connects **fields of study**, **related occupations**, and **labor market outcomes** using authoritative U.S. government data. The resulting dataset supports explainable, grounded responses to questions about education pathways and career outcomes.

---

## Data Sources

The pipeline integrates three primary sources:

1. **College Scorecard (U.S. Department of Education)**  
   Provides program‑level outcomes, including median earnings four years after completion, by field of study and degree level.

2. **CIP–SOC Crosswalk (NCES / BLS)**  
   Maps Classification of Instructional Programs (CIP) codes to Standard Occupational Classification (SOC) codes, enabling program‑to‑occupation linkage.

3. **BLS Occupational Employment and Wage Statistics (OEWS)**  
   Provides national employment counts and median wage estimates for detailed SOC occupations.

---

## Data Preparation Strategy

### 1. College Scorecard Cleaning

- Retained only program‑level variables relevant for downstream use:
  - CIP code  
  - Program title  
  - Degree level  
  - Median earnings (four years post‑completion)
- Ensured CIP codes were treated as strings to preserve leading zeros.
- Derived a **4‑digit CIP family (`cip4`)**, reflecting the natural granularity at which Scorecard outcomes are published.
- Limited scope to Bachelor’s and Master’s degrees for comparability.

**Rationale**  
College Scorecard outcomes are published at the field‑of‑study (CIP4) level; using finer granularity would introduce false precision.

---

### 2. CIP–SOC Crosswalk Cleaning

- Loaded the official **CIP 2020 → SOC 2018** crosswalk.
- Retained only the primary CIP–SOC mapping sheet.
- Standardized code formats:
  - CIP → `##.####`
  - SOC → `##-####`
- Removed aggregate SOC groups (e.g., `xx-0000`) and duplicate mappings.
- Derived `cip4` from 6‑digit CIP codes to align with College Scorecard.

**Rationale**  
The crosswalk operates at a finer CIP level than Scorecard; rolling up to `cip4` ensures consistent and defensible joins.

---

### 3. OEWS Cleaning and Diagnostics

- Extracted detailed SOC codes, occupation titles, employment counts, and annual median wages.
- Removed aggregate SOC groups.
- Converted wage and employment fields to numeric values.
- Explicitly diagnosed data coverage:
  - Identified SOC codes present in the crosswalk but missing from OEWS.
  - Identified SOC codes present in OEWS but lacking numeric wage estimates.

**Key Finding**  
Some occupations either do not appear in OEWS or do not have numeric annual wage estimates due to suppression, aggregation, or reporting conventions. These gaps reflect **data limitations**, not join errors.

---

## Joining Logic

1. **College Scorecard → CIP–SOC Crosswalk**  
   Joined on `cip4` to map fields of study to related occupations.

2. **CIP–SOC Crosswalk → OEWS**  
   Joined on `soc_code` to attach employment and wage outcomes.

This produced a comprehensive joined table linking:

- Program outcomes (education)
- Related occupations
- Labor market outcomes

---

## Final Outputs

Two joined datasets were saved:

### 1. Full Joined Dataset

- **File:** `cleaned/eduyou_joined_for_rag.csv`
- Contains all program–occupation links, including rows without wage data.
- Intended for transparency, diagnostics, and reproducibility.

### 2. RAG‑Ready Joined Dataset (Wage‑Only)

- **File:** `cleaned/eduyou_joined_for_rag_wage_only.csv`
- Retains only rows with valid annual median wages.
- Used as the foundation for RAG document construction.

**Rationale**  
Filtering to wage‑available rows prevents hallucination and ensures that retrieved answers are grounded in numeric evidence.

---

## RAG Document Construction

From the wage‑only dataset:

- Aggregated data to **one document per `cip4` and degree level**.
- Selected top occupations ranked by employment.
- Each document includes:
  - Median earnings four years after program completion
  - Related occupations with employment and wage estimates
  - A note when some related occupations lack wage data in OEWS

The resulting corpus is compact, interpretable, and suitable for embedding in a RAG system.

---

## Design Principles

- **Explainability over coverage:** No imputation or invented values
- **Granularity alignment:** Explicit handling of CIP4 vs. CIP6 differences
- **Transparency:** Clear distinction between missing data and join failures
- **RAG safety:** Only factual, numeric content is embedded

## Limitations & Ethical Use

### Data Coverage Limitations
- Not all occupations mapped in the CIP–SOC crosswalk appear in the BLS OEWS dataset, and not all SOC codes published by OEWS include numeric annual median wage estimates.
- Missing wage values arise from **documented OEWS reporting constraints** (e.g., suppression, aggregation, or non‑standard wage reporting), not from join or processing errors.
- To prevent misrepresentation, the RAG‑ready dataset used for embedding includes **only rows with valid numeric wage estimates**. Occupations without available wages are excluded from retrieval content but tracked separately for transparency.

### Granularity and Interpretation
- College Scorecard outcomes are published at the **4‑digit CIP (field‑of‑study) level**, while the CIP–SOC crosswalk operates at a more granular 6‑digit CIP level.
- The pipeline intentionally aligns these sources by joining on the **CIP4 family**, which supports consistency and interpretability but does not imply causal or deterministic relationships between specific programs and occupations.
- All education‑to‑occupation links should be interpreted as **associative mappings**, not guarantees of career outcomes.

### Appropriate Use of Wage Information
- Wage estimates reflect **national median values** and do not account for geographic variation, individual experience, employer type, or labor market dynamics.
- The data should be used for **informational and exploratory purposes only**, such as career exploration or academic analysis.
- The outputs are **not intended** for individual wage prediction, hiring decisions, admissions decisions, or policy evaluation without additional contextual analysis.

### RAG Safety and Responsible AI Use
- No wages or employment values are imputed, extrapolated, or inferred.
- The RAG corpus embeds **only factual, numeric information** sourced directly from authoritative datasets.
- When data are unavailable, the system is designed to acknowledge limitations explicitly rather than generate speculative responses.

### Ethical Considerations
- The pipeline relies exclusively on **publicly available, non‑personal data**.
- No individual‑level records or personally identifiable information are used.
- Users should avoid interpreting aggregated outcomes as prescriptive guidance for individual educational or career decisions.

---

## Citation & Attribution

This project relies exclusively on **publicly available U.S. government datasets**. All data are used in accordance with their respective terms of use and attribution guidelines.

### Data Sources

- **College Scorecard**  
  U.S. Department of Education. *College Scorecard – Most Recent Cohorts, Field of Study*.  
  https://collegescorecard.ed.gov/data/

- **CIP–SOC Crosswalk**  
  National Center for Education Statistics (NCES) and U.S. Bureau of Labor Statistics (BLS).  
  *CIP 2020 to SOC 2018 Crosswalk*.  
  https://nces.ed.gov/ipeds/cipcode/

- **Occupational Employment and Wage Statistics (OEWS)**  
  U.S. Bureau of Labor Statistics. *Occupational Employment and Wage Statistics*.  
  https://www.bls.gov/oes/

### Attribution Notes

- College Scorecard data are produced by the U.S. Department of Education and reflect program‑level outcomes aggregated at the field‑of‑study level.
- The CIP–SOC crosswalk is jointly maintained by NCES and BLS and provides associative mappings between instructional programs and occupations.
- OEWS data are produced by the U.S. Bureau of Labor Statistics and reflect national employment and wage estimates based on survey data.

### Disclaimer

The interpretations, data processing decisions, and derived datasets presented in this repository are the responsibility of the project author and **do not represent the views or endorsements** of the U.S. Department of Education, the National Center for Education Statistics, or the U.S. Bureau of Labor Statistics.
---

## Result

The pipeline produces a **defensible, RAG‑ready dataset** that supports accurate and explainable responses about education‑to‑career pathways while respecting known limitations of the underlying data sources.

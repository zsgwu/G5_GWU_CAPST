# Capstone_Project_Group 5

# EduYou RAG Data Pipeline

---

## Executive Summary

EduYou is a **retrieval‑augmented generation (RAG)–ready data pipeline** designed to support transparent, evidence‑based exploration of education‑to‑career pathways. Using publicly available U.S. government data, the system links **fields of study**, **related occupations**, and **labor market outcomes** into semantically coherent documents suitable for vector embedding and retrieval.

Rather than relying on opaque or speculative generation, the pipeline emphasizes **explainability, data provenance, and responsible use**. Retrieved documents provide grounded context for answering user questions about education pathways and career outcomes, while optional generation demonstrates how retrieved evidence can be translated into accessible, natural‑language responses. The design prioritizes analytical defensibility and alignment with standard RAG architectures.

---

## Overview

This project prepares a **Retrieval‑Augmented Generation (RAG)**–ready dataset that connects **fields of study**, **related occupations**, and **labor market outcomes** using authoritative U.S. government data. The resulting dataset supports explainable, grounded responses to questions about education pathways and career outcomes.

The pipeline separates **data engineering**, **document construction**, **embedding**, and **retrieval**, ensuring compatibility with standard RAG templates and avoiding semantic ambiguity.

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

### Analytical Join Outputs

These files support diagnostics, validation, and transparency but are **not used directly for RAG**.

- **Full Joined Dataset**  
  - File: `cleaned/eduyou_joined_for_rag.csv`
  - Contains all program–occupation links, including rows without wage data.

- **Wage‑Only Join (Filtered)**  
  - File: `cleaned/eduyou_joined_for_rag_wage_only.csv`
  - Retains only rows with valid annual median wages.

---

## RAG Document Construction

To support RAG, the pipeline **does not embed the raw joined tables**. Instead, it constructs a document‑level corpus:

- Aggregated data to **one document per `cip4` and degree level**
- Selected top related occupations ranked by national employment
- Each document includes:
  - National median earnings four years after completion
  - Related occupations with OEWS employment and wage estimates
  - Explicit notes where occupation‑level wages are unavailable

### RAG Document Output

- **File:** `cleaned/eduyou_cip_docs_for_embedding.csv`
- **Grain:** One row = one semantic document
- **Purpose:** Input to embedding and retrieval steps

This design ensures that each embedded unit represents a coherent, interpretable narrative rather than a relational join.

---

## Embedding & Retrieval (RAG Execution)

RAG is implemented using **Azure OpenAI embeddings**, following the professor‑provided template.

### Embedding Notebook

- **Notebook:** `get_embeddings_eduyou.ipynb`
- **Input:** `cleaned/eduyou_cip_docs_for_embedding.csv`
- **Output:** `embeddings/eduyou_embeddings_<MODEL>.csv`
- **Embedding models supported:**
  - `text-embedding-ada-002`
  - `text-embedding-3-small`
  - `text-embedding-3-large`

The deployment name matches the model name directly, as required by the Azure OpenAI setup.

### Retrieval & Query Notebook

- **Notebook:** `rag_ratrival.py`
- Loads precomputed embeddings
- Embeds user queries using the same model
- Retrieves Top‑K documents via cosine similarity

The answer‑generation step is included as a demonstration of how retrieved documents can support user‑facing responses. Evaluation focuses on document construction, embedding quality, and retrieval accuracy rather than on the generative model itself.

---

## Design Principles

- **Explainability over coverage:** No imputation or invented values
- **Granularity alignment:** Explicit handling of CIP4 vs. CIP6 differences
- **Transparency:** Clear distinction between analytical joins and RAG documents
- **Grounding & safety:** Only factual, numeric, and source‑verifiable content is embedded
- **Template compliance:** One row = one document, matching standard RAG workflows

---

## Limitations & Ethical Use

### Data Coverage Limitations
- Not all occupations mapped in the CIP–SOC crosswalk appear in the BLS OEWS dataset, and not all SOC codes published by OEWS include numeric annual median wage estimates.
- Missing wage values arise from **documented OEWS reporting constraints**, not from join or processing errors.
- Occupations without available wages are excluded from retrieval content to prevent misrepresentation.

### Granularity and Interpretation
- Education‑to‑occupation links are **associative**, not causal.
- National benchmarks should not be interpreted as institution‑specific outcomes.

### Appropriate Use of Wage Information
- Wage estimates are national medians and do not reflect individual circumstances.
- Outputs are intended for **informational and academic use only**.

### Responsible AI Use
- No personal or individual‑level data are used.
- The system explicitly acknowledges data limitations rather than generating speculative answers.

---

## Citation & Attribution

This project relies exclusively on **publicly available U.S. government datasets**.

### Data Sources

- **College Scorecard**  
  U.S. Department of Education.  
  https://collegescorecard.ed.gov/data/

- **CIP–SOC Crosswalk**  
  NCES & U.S. Bureau of Labor Statistics.  
  https://nces.ed.gov/ipeds/cipcode/

- **Occupational Employment and Wage Statistics (OEWS)**  
  U.S. Bureau of Labor Statistics.  
  https://www.bls.gov/oes/

### Citation Strategy

Generated responses reference the primary datasets (e.g., College Scorecard, IPEDS, BLS OEWS) rather than internal document identifiers. This choice improves transparency and interpretability for non‑technical users and avoids exposing implementation‑specific identifiers that lack standalone meaning.

### Disclaimer

The interpretations and derived datasets presented in this repository are the responsibility of the project authors and **do not represent official views** of the U.S. Department of Education, NCES, or the U.S. Bureau of Labor Statistics.

---

## Methodology

The EduYou pipeline follows a structured methodology designed to align with standard retrieval‑augmented generation practices while maintaining analytical integrity.

First, raw source datasets are cleaned and standardized independently to preserve the integrity of each data provider’s reporting conventions. Granularity decisions are driven by how outcomes are published rather than by desired model resolution, avoiding false precision. Diagnostic checks are explicitly performed to distinguish genuine data gaps from processing errors.

Second, relational joins are used strictly for **analytical validation**, not as direct model inputs. Rather than embedding joined tables, the pipeline constructs narrative‑level documents that aggregate education outcomes and related occupations into coherent semantic units. This ensures compatibility with embedding models and avoids semantic fragmentation during retrieval.

Third, documents are embedded using Azure OpenAI embedding models, with one vector per document. Query embeddings are generated using the same model to ensure vector space consistency. Retrieval is performed using cosine similarity, producing an ordered set of relevant documents.

Finally, retrieved documents may be passed to a generation model as contextual grounding to demonstrate how structured evidence can be translated into natural‑language responses. Citations refer to the underlying datasets rather than internal document IDs, prioritizing interpretability for end users. Throughout the pipeline, explainability, transparency, and responsible AI principles guide design decisions.

---

## Result

The EduYou pipeline produces a **defensible, RAG‑ready system** that enables accurate, explainable exploration of education‑to‑career pathways while respecting data limitations and responsible AI principles.

---
## Repository Structure

- `data/raw/` – Original source datasets (unchanged)
- `data/processed/` – Cleaned and harmonized datasets
- `data/embeddings/` – Chunked, RAG-ready documents
- `notebooks/` – Data preparation and RAG experiments
- `app/` – Demo application for querying the RAG system

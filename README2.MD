
## SQL Overview

The chatbot uses a structured SQL process for school-level questions such as admissions, tuition, debt, earnings, net price, and college comparisons.

1. **Trigger detection**  
   The app first decides whether a question should use SQL by checking for school names, school-level metrics, and comparison-style requests.

2. **SQLite retrieval**  
   If SQL is triggered, the app queries `most_recent_cohorts_institution.sqlite3` to retrieve institution-level data.  
   This database is built from `Most-Recent-Cohorts-Institution.csv` and supplemental net price history from `instate_tuition_cleaned.csv`.

## RAG Overview

The chatbot uses a two-step RAG process for major, career, and program-outcome questions.

1. **Trigger detection**  
   The app first decides whether a question should use RAG by checking for major/career-related phrases and known program titles.  
   This step uses `eduyou_cip_docs_for_embedding.csv`.

2. **Embedding-based retrieval**  
   If RAG is triggered, the app retrieves context using precomputed embeddings from `embeddings/eduyou_embeddings_text-embedding-3-small.csv`.  
   It embeds the user query, compares it to stored document embeddings with cosine similarity, and returns the top matches.

# EDU, Education Decision Intelligence Chatbot

EDU is A Streamlit-based college and career advising chatbot that combines SQL school data, RAG program context, and Azure OpenAI responses.

## Overview

This project helps students explore colleges, majors, and career outcomes in one interface.  
It is designed to answer both structured school questions and broader major or career questions, making college counceling accessable to all. 

The overall approach is to classify intent of users and direct each question to the most appropriate source:
- SQL for institution-level school data
- RAG for major, career, and program-outcome questions
- Azure OpenAI for explanation, synthesis, and student-facing guidance

## Features

Key capabilities include:
- school-level SQL querying
- RAG-based major and career responses
- college comparison workflows
- FAFSA-based net price history charts
- applicant-profile and resume-aware guidance
- concise, student-facing response generation

What makes this project unique is its hybrid routing design.  
Instead of treating every question the same way, the app decides whether to use SQL, RAG, or general LLM reasoning based on the user’s intent.

## Tech Stack

**Languages**  
Python, SQL

**Frameworks**  
Streamlit

**Tools**  
Azure OpenAI, SQLite, Pandas, NumPy, Altair, pdfplumber, python-docx

## Project Structure

A simplified view of the project structure is shown below.

```text
chatbot/
├── app.py
├── rag_retrival.py
├── most_recent_cohorts_institution.sqlite3
├── Most-Recent-Cohorts-Institution.csv
├── instate_tuition_cleaned.csv
├── eduyou_cip_docs_for_embedding.csv
├── embeddings/
│   └── eduyou_embeddings_text-embedding-3-small.csv
├──EDyoU.jpeg
├── requirements.txt
└── README.md
```

## How to Run the Project

Install dependencies, set the Azure OpenAI environment variables, and run:

```bash
streamlit run app.py
```

The user should expect:
- a chat interface for school, major, and career questions
- structured school data panels for SQL-supported prompts
- RAG-supported explanations for major and career prompts
- charts and filters for supplemental net price history

Example inputs:
- `Compare George Washington University, Howard University, and University of Maryland-College Park on earnings, debt, and admission rate.`
- `What can I do with an Industrial Engineering major?`
- `What majors fit a student interested in logistics, operations, and process improvement?`

## Methodology

### Data Sources

The project uses a mix of structured and unstructured data sources:

College Scorecard
U.S. Department of Education.
https://collegescorecard.ed.gov/data/

CIP–SOC Crosswalk
NCES & U.S. Bureau of Labor Statistics.
https://nces.ed.gov/ipeds/cipcode/

Occupational Employment and Wage Statistics (OEWS)
U.S. Bureau of Labor Statistics.
https://www.bls.gov/oes/

FAFSA Net Price Data
U.S. Department of Education
https://nces.ed.gov/ipeds


### Modeling Approach

The chatbot uses a routing-based design.  
Each user question is first classified by intent, then sent to the most appropriate source: SQL, RAG, or general Azure reasoning.

### RAG Overview

The chatbot uses a two-step RAG process for major, career, and program-outcome questions.

1. **Trigger detection**  
   The app first decides whether a question should use RAG by checking for major/career-related phrases and known program titles.  
   This step uses `eduyou_cip_docs_for_embedding.csv`.

2. **Embedding-based retrieval**  
   If RAG is triggered, the app retrieves context using precomputed embeddings from `embeddings/eduyou_embeddings_text-embedding-3-small.csv`.  
   It embeds the user query, compares it to stored document embeddings with cosine similarity, and returns the top matches.

### SQL Overview

The chatbot uses a structured SQL process for school-level questions such as admissions, tuition, debt, earnings, net price, and college comparisons.

1. **Trigger detection**  
   The app first decides whether a question should use SQL by checking for school names, school-level metrics, and comparison-style requests.

2. **SQLite retrieval**  
   If SQL is triggered, the app queries `most_recent_cohorts_institution.sqlite3` to retrieve institution-level data.  
   This database is built from `Most-Recent-Cohorts-Institution.csv` and supplemental net price history from `instate_tuition_cleaned.csv`.

### LLM Usage

Azure OpenAI is used to:
- explain retrieved SQL or RAG context in student-friendly language
- synthesize comparisons and recommendations
- personalize answers using transcript or resume context when available

The LLM is not the primary source for numeric claims when structured data is available.  
Instead, it acts as the explanation and decision-support layer on top of retrieved context.

## Evaluation

Performance is measured using two validation tracks:
- numeric accuracy for school and program statistics
- response quality for clarity, groundedness, concision, and usefulness

Core evaluation metrics include:
- Accuracy
- Clarity
- Concision
- Actionability

Current findings:
- SQL performs best for exact school-level questions and comparisons
- RAG performs best when the embeddings file has strong coverage for the queried field
- overall answer quality improves when routing selects the correct source cleanly

## Challenges & Improvements

Key challenges included:
- incorrect or overly broad school matching
- routing errors between SQL, RAG, and general reasoning
- irrelevant RAG citations caused by shallow text-based matching
- uneven coverage across majors in the embeddings file

## Future Work

Planned next steps include:
- expanding embedding coverage for more majors and career fields
- improving school and major alias handling
- adding stronger validation dashboards
- improving citation quality and transparency
- scaling the app to support larger data sources and more robust filtering

### Presentation Materials Overview

- **Capstone Group 5 Final Presentation**    The main slide deck summarizing the project, methodology, findings, and key insights.
- **Final_Poster.png**    Poster competition poster in PNG form.
- **Link For Backup Demo**    A backup video of the planned demo for the live case presentation.

## Contributors

Benjamin Cooper, Julia Milliet Sciorra, Tina Zhou, Zahra Sultani, Ryan Hu 

## Acknowledgments

We are grateful to our instructors and the DNSC 4289 faculty, especially Professor Ali Obaidi and Professor Patrick Hall, for their time, mentorship, and thoughtful guidance throughout this project. We also acknowledge the use of publicly available datasets, including College Scorecard, FAFSA, and the Bureau of Labor Statistics.

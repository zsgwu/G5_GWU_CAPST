# G5_GWU_CAPST
Capstone_Project_Group 5

# EduYou — RAG Data Pipeline (College Scorecard + CIP–SOC + BLS OEWS)

A reproducible data pipeline for the EduYou capstone that prepares **RAG-ready, explainable** joined datasets linking **fields of study (CIP)** → **occupations (SOC)** → **labor market outcomes (wages/employment)** and producing an embedding-friendly document corpus.

> **Key design choice:** We align granularities by joining on the **4-digit CIP family (`cip4`)**, because College Scorecard field-of-study outcomes are published at this level, while the CIP–SOC crosswalk is at 6-digit CIP. [1](https://worldbankgroup-my.sharepoint.com/personal/zsultani_worldbank_org/_layouts/15/Doc.aspx?sourcedoc=%7B2A9F8215-1C4D-4D0C-9997-D9347B888827%7D&file=Most-Recent-Cohorts-Field-of-Study.csv&action=default&mobileredirect=true)[2](https://worldbankgroup-my.sharepoint.com/personal/zsultani_worldbank_org/_layouts/15/Doc.aspx?sourcedoc=%7B01ECC239-0910-45F7-9A04-73FEDB5CFE72%7D&file=CIP2020_SOC2018_Crosswalk.xlsx&action=default&mobileredirect=true&DefaultItemOpen=1)

---

## Data Sources

- **College Scorecard (Field of Study / Most Recent Cohorts)** — program outcomes and earnings by field of study. [1](https://worldbankgroup-my.sharepoint.com/personal/zsultani_worldbank_org/_layouts/15/Doc.aspx?sourcedoc=%7B2A9F8215-1C4D-4D0C-9997-D9347B888827%7D&file=Most-Recent-Cohorts-Field-of-Study.csv&action=default&mobileredirect=true)[3](https://www.bls.gov/oes/oes_emp.htm)  
- **CIP 2020 ↔ SOC 2018 Crosswalk (NCES/BLS)** — maps programs (CIP) to occupations (SOC). [2](https://worldbankgroup-my.sharepoint.com/personal/zsultani_worldbank_org/_layouts/15/Doc.aspx?sourcedoc=%7B01ECC239-0910-45F7-9A04-73FEDB5CFE72%7D&file=CIP2020_SOC2018_Crosswalk.xlsx&action=default&mobileredirect=true&DefaultItemOpen=1)[4](https://www.bls.gov/oes/oes_ques.htm)  
- **BLS OEWS (National)** — employment and wage estimates by occupation (SOC). [4](https://worldbankgroup-my.sharepoint.com/personal/zsultani_worldbank_org/_layouts/15/Doc.aspx?sourcedoc=%7BF8585BA0-D81D-413B-8DF6-7678BE77C310%7D&file=OES_Report.xlsx&action=default&mobileredirect=true)[5](https://worldbankgroup.sharepoint.com/sites/myhr/Documents/Talent%20Acquisition/ST%20Information/ST%20Compliance_Twopager.pdf?web=1)  

---



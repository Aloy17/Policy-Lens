# Verified Retrieval Example — Beneficial Owner Identification

**Capture date:** 2026-11-08  
**Query:** How should the beneficial owner of a legal person be identified?  
**Strategy:** Structure-aware  
**Top K:** 5  
**Metadata filter:** `issuer=RBI` → `Reserve Bank of India`  
**Database:** `dist/PolicyLens/PolicyLens Data/chroma_db`  
**Collection:** `policylens_v1_structure`

## Live search results

| Rank | Similarity score | Document | Pages | Section |
|---:|---:|---|---:|---|
| 1 | 0.7235 | Master Direction - Know Your Customer (KYC) Direction | 38–38 | Part IV - Identification of Beneficial Owner |
| 2 | 0.4704 | Master Direction - Know Your Customer (KYC) Direction | 5–6 | PRELIMINARY |
| 3 | 0.4643 | Master Direction - Know Your Customer (KYC) Direction | 89–90 | Section 2(1) (sa) of Prevention of Money-Laundering Act, 2002 |
| 4 | 0.4532 | Master Direction - Know Your Customer (KYC) Direction | 6–7 | PRELIMINARY |
| 5 | 0.4421 | Master Direction - Know Your Customer (KYC) Direction | 88–88 | Section 2(1) (sa) of Prevention of Money-Laundering Act, 2002 |

## Verification

- Evaluation question: **q04**
- Gold document: `rbi_kyc_2024`
- Gold page range: **38–38**
- Live result at rank 1: **page 38**
- The rank-1 section title directly matches the query topic.
- The RBI issuer filter was applied and resolved to `Reserve Bank of India`.

**Outcome:** The live structure-aware search retrieved the expected gold page at rank 1. This is a verified example of passage-level retrieval for the demo.

## Rank-1 passage preview

> part iv - identification of beneficial owner 34. for opening an account of a legal person who is not a natural person, the beneficial owner(s) shall be identified and all reasonable steps in terms ...

## Evidence scope and limitation

This Markdown record documents the actual CLI output supplied for this run. It is **not a terminal screenshot**. The similarity score is the search system's returned score and should not be interpreted as a calibrated probability of correctness.

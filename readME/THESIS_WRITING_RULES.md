# Master's Thesis Writing Rules

**Thesis:** Generalized Methodology for Automated Mapping of Model Parameters between Generalized Digital Twins and Domain Models  
**Page limit:** 80 pages (distribution below)  
**Style reference:** Simil Shajan's thesis (numbered citations [N], concise; page budget modeled after his 89-page document)

---

## 1. Knowledge Constraint

- **Use ONLY** the provided sources in the thesis folder. No external or general knowledge.
- **If Source A cites Source B** and Source B is not in the folder: **stop and notify** so Source B can be downloaded and uploaded. Do not use information that originates only in an uncited source.
- **Current library:** Documents folder + readME thesis docs (markdown, HTML). PDFs may be added later; once added, they become part of the library. Until then, only Documents + readME are used.

---

## 2. Citation Style

- **Format:** Claim or sentence, then space, then `[Number]` before the period. Example: *The CO-insertion pathway is likely the primary mechanism for FTS, due to the lower activation barrier compared to the carbide mechanism [17].*
- **Number** = position in the **running reference list** (numbered [1], [2], [3], …).
- Place the citation at the end of the sentence, immediately before the period: `…across manufacturers [1].`
- Multiple sources: `[1], [2]` or `[1–3]` as appropriate.
- Every factual claim that comes from a source must have a `[Number]`; do not use uncited general knowledge.
- **End of each session:** When thesis text with citations is produced, append the **Bibliography** (reference list with numbers used in that session) so you can verify the numbers.

---

## 3. Conciseness (80-Page Limit)

- **Information-dense:** Prefer short, precise sentences. Avoid filler and repetition.
- **Technical focus:** Emphasize **why** (rationale, design choices) and **how** (mechanisms, algorithms, pipeline) rather than long general descriptions.
- **Avoid:** Long introductions to well-known concepts; redundant summaries; bullet lists that could be one sentence.
- **Prefer:** Definitions in one sentence; tables for comparisons; flow/equations for methodology; short paragraphs (3–5 sentences) with one main idea each.

---

## 4. Structure (6 Chapters) & Page Budget

**Total limit:** 80 pages. Distribution below is modeled after Simil Shajan's 89-page thesis, scaled to 80.

| Ch | Focus | Estimated pages |
|----|--------|------------------|
| **1** | Introduction & Problem Statement (Interoperability, motivation) | 5–8 |
| **2** | Technical Background (AAS, OPC UA, AutomationML) | 15–20 |
| **3** | State of the Art & Gaps | 10–12 |
| **4** | Your Developed Methodology | 15–20 |
| **5** | Prototypical Implementation & Validation | 15–18 |
| **6** | Conclusion & Future Work | 3–5 |

**Content focus by chapter:**

- **Ch 1:** Definition of interoperability, RAMI4.0, industrial challenges, duplicate standardization, complementary technologies, motivation for automated mapping.
- **Ch 2:** AAS, OPC UA, AutomationML: concept, structure, role; complementary relationship; implications for mapping.
- **Ch 3:** Schema matching, ontology alignment, semantic enrichment, similarity metrics; gaps the methodology addresses.
- **Ch 4:** Five-stage pipeline, semantic node model, extraction, normalization, multi-source enrichment, hybrid matching, validation.
- **Ch 5:** Modules, data structures, algorithms; application to industrial scenarios; evaluation; benefits and limitations.
- **Ch 6:** Summary of findings, achievement of objectives, future work, concluding remarks.

---

## 5. Reference List Conventions

- Keep one **running reference list** at the end of the thesis.
- Each entry: `[N] Author/s (Year). *Title*. …` (or standard for your program).
- When adding a new source, assign the next number and use that number in the text from then on.
- If a source is cited within an uploaded paper (Source A → Source B) and you use that content, add **Source B** to the reference list and cite it directly where the content appears.

### Bibliography at end of each session

Whenever thesis content with citations is produced in a reply, the reply must end with a **Bibliography** section listing every reference cited (by number), so you can verify that [1], [2], etc. match your master list. Example:

```
---
Bibliography (cited in this session)
[1] Author (Year). *Title*. ...
[2] ...
```

---

## Quick Checklist for Every Thesis Reply

- [ ] Only information from provided folder sources?
- [ ] If Source A cites B and B not uploaded → notify, do not use B.
- [ ] Citations: claim/sentence then `[Number]` before the period?
- [ ] Every factual claim has `[Number]`?
- [ ] Dense, technical “why/how”; no filler?
- [ ] Fits the 6-chapter structure where applicable?
- [ ] **Bibliography at end of reply** listing all [N] used, for number verification?

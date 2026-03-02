# Detailed Sub-Outline: Thesis Chapters with Sources

**Thesis title:** Generalized Methodology for Automated Mapping of Model Parameters between Generalized Digital Twins and Domain Models.

**Source key (for citation):**

| # | Source | Use for |
|---|--------|--------|
| [1] | Diskussionspapier (AutomationML e.V., IDTA, OPC Foundation, VDMA, 2023) | Interoperability, AAS/OPC UA/AML roles, complementary technologies |
| [2] | Thesis Task Description (OvGU, 2025) | Problem framing, objectives, automation of automation engineering |
| [3] | IEC PAS 63088 (RAMI4.0) | Reference Architecture Model Industry 4.0, hierarchy levels, layers |
| [4] | DIN SPEC 91345 (RAMI4.0) | Same as [3], German standard for RAMI4.0 |
| [5] | Thesis Report / Thesis Introduction and Chapters (readME) | Chapter narrative, state of the art, methodology description, conclusion |
| [6] | Thesis Description (readME) | Pipeline stages, algorithms, data structures, implementation details |
| [7] | Documents folder | Context-aware normalization, training data, unit inference, vector embeddings, value stream/simulation docs |

---

## Chapter 1: Conceptual Foundations

**Chapter title (from your docs):** Interoperability in Industry 4.0

### 1.1 The Concept of Interoperability

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 1.1.1 Definition of interoperability | Interoperability as ability of systems, devices, and applications to connect and communicate purposefully across manufacturers; OT and IT [1]. | [1] |
| 1.1.2 RAMI4.0 as interoperability framework | Three-dimensional model: Hierarchy Levels (product to connected world), Value Stream (lifecycle), Layers (business to functional to asset) [3], [4]. | [3], [4] |
| 1.1.3 Industry 4.0 vs consumer IT | Deep software integration required; industrial assets far from “Plug & Play”; contrast with Ethernet, USB, driver architectures [1], [5]. | [1], [5] |

### 1.2 The Challenge of Industrial Interoperability

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 1.2.1 Cross-cutting dimensions | Different manufacturers, lifecycle phases, domains (mechanical, electrical, automation, IT), and standards [1], [5]. | [1], [5] |
| 1.2.2 Requirements for interoperability | Standardized data models (AAS Submodel Templates, AutomationML, OPC UA Companion Specifications) and standardized interfaces (e.g. OPC UA); AAS as digital lifecycle file [1]. | [1] |
| 1.2.3 Stakeholder access | All authorized stakeholders—sales to service, across company boundaries—accessing AAS [1]. | [1] |

### 1.3 The Risk of Duplicate Standardization

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 1.3.1 Competing vs complementary standards | Risk of duplicate modeling, duplicate data storage, duplicate software development, hindered value chains when AAS, AutomationML, OPC UA compete [1], [5]. | [1], [5] |
| 1.3.2 Stance of key organizations | Proprietary/closed solutions not sustainable; standardized interoperability solutions prioritized (AutomationML e.V., IDTA, OPC Foundation, VDMA) [1]. | [1] |

### 1.4 The Vision: Complementary Technologies

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 1.4.1 Complementary roles | AAS, OPC UA, AutomationML complement each other; avoid duplicate work, reduce model overlaps, reduce development effort, enable cross-domain interoperability [1], [5]. | [1], [5] |
| 1.4.2 “Big Picture” interoperability | Interoperability through intelligent combination of standards and domain models, not a single world model [1], [5]. | [1], [5] |

### 1.5 Motivation for Automated Mapping

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 1.5.1 Automation of automation engineering | Efficiency and effectiveness in production system engineering; identification and utilization of data sources; mapping to internal data models of engineering automation algorithms [2], [5]. | [2], [5] |
| 1.5.2 Simulation-based engineering | Simulation-based decisions; tool-specific, proprietary data models; need to populate from standardized sources; research question: automatic mapping between generalized digital twins and domain-specific simulation models [2], [5]. | [2], [5] |
| 1.5.3 Limitations of manual mapping | Time-consuming, error-prone, not scalable, maintenance-intensive [5]. | [5] |
| 1.5.4 Benefits of automated mapping | Reduced manual effort, improved consistency, scalability, support for maintenance [5]. | [5] |

### 1.6 Thesis Objectives and Structure

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 1.6.1 Six-chapter structure | Ch1 Conceptual foundations; Ch2 Key technologies; Ch3 State of the art; Ch4 Methodology; Ch5 Implementation & validation; Ch6 Conclusion [5]. | [5] |
| 1.6.2 Three-part contribution | State-of-the-art analysis; novel hybrid semantic matching; prototypical implementation [5]. | [5] |

---

## Chapter 2: Technical Background / Standards

**Chapter title (from your docs):** Key Technologies for Industrial Interoperability

### 2.1 Asset Administration Shell (AAS)

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 2.1.1 Concept and purpose | Digital representation of asset; lifecycle-spanning information; standardized structure; cross-company access; reference to detailed models; “digital lifecycle file” [1], [5]. | [1], [5] |
| 2.1.2 AAS Submodel Templates | Standardized structures for information types; consistent data representation; interoperability; reusability; examples: technical data sheets, sales, CO2 footprint, maintenance [1], [5]. | [1], [5] |
| 2.1.3 AAS in RAMI4.0 | Type 2 AAS in Connected World, not in classical productive field devices; critical data not dependent on AAS; separation from operational data (OPC UA) [1], [5]. | [1], [5] |
| 2.1.4 AAS API and data access | REST API (as of April 2023); standardized access; lifecycle-spanning data; integration [1], [5]. | [1], [5] |

### 2.2 OPC UA and Companion Specifications

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 2.2.1 OPC UA overview | Platform-independent, service-oriented; secure, reliable information exchange; machine-to-machine and machine-to-IT; digital twin and metaverse integration [1], [5]. | [1], [5] |
| 2.2.2 Companion Specifications | Standardized information models per domain/device type; standardize semantics; interoperability; examples: energy, machine status, process parameters, safety [1], [5]. | [1], [5] |
| 2.2.3 Operational data access | OPC UA for operational data; communication between machines; dynamic data; metadata access; support for AAS use cases (e.g. CO2 footprint) [1], [5]. | [1], [5] |
| 2.2.4 OPC UA information models | Type definitions; object models; semantic annotations; extensibility [5]. | [5] |

### 2.3 AutomationML

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 2.3.1 Concept and purpose | Neutral, XML-based format; plant engineering exchange; tool interoperability; model reuse; lifecycle support [1], [5]. | [1], [5] |
| 2.3.2 Structure | Topology, geometry, behavior, kinematics models [1], [5]. | [1], [5] |
| 2.3.3 Libraries | Automation components, plant/hardware topologies, networked system models; standardization, reusability, interoperability [1], [5]. | [1], [5] |
| 2.3.4 Integration with other formats | References to external files/models; embedding; conversion; OPC UA Nodeset files, device descriptions [1], [5]. | [1], [5] |

### 2.4 Complementary Relationship of Technologies

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 2.4.1 Role separation | AAS: lifecycle-spanning product information, Connected World; OPC UA: operational data; AutomationML: engineering data exchange, tool interoperability [1], [5]. | [1], [5] |
| 2.4.2 Avoiding competence conflicts | Data defined by experts in the domain where it originates; AAS Submodels, OPC UA Companion Specs, AutomationML libraries each in their domain [1], [5]. | [1], [5] |
| 2.4.3 Reference and reuse | AAS references AutomationML and OPC UA; models reused across technologies; integration in applications [1], [5]. | [1], [5] |

### 2.5 Implications for Automated Mapping

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 2.5.1 Mapping challenges | Cross-technology mapping; standard-to-proprietary mapping; semantic alignment; lifecycle alignment [5]. | [5] |
| 2.5.2 Mapping requirements | Multi-format support (AAS, OPC UA, AML); preserve semantics; handle heterogeneity; enable enrichment; provide validation [5]. | [5] |
| 2.5.3 Foundation for methodology | Multi-format support; semantic understanding; context awareness; enrichment strategy (eCl@ss, IEC CDD); validation mechanisms [5], [6]. | [5], [6] |

### 2.6 Summary

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 2.6.1 Recap of three technologies | AAS, OPC UA, AutomationML as complementary; essential for methodology that bridges standards and proprietary simulation models [5]. | [5] |

---

## Chapter 3: State of the Art / Literature Review

**Chapter title (from your docs):** State of the Art in Data Mapping and Semantic Technologies

### 3.1 Schema Matching and Data Mapping

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 3.1.1 Schema matching approaches | Linguistic matching (names, labels; string/token similarity); structural matching (parent-child, keys); constraint-based (types, units, ranges); instance-based (sample data) [5]. | [5] |
| 3.1.2 Industrial schemas | AAS Submodels, OPC UA Information Models, AutomationML; combination of linguistic, structural, and technical constraints; need for hybrid methods [5]. | [5] |
| 3.1.3 Limitations for industrial data | Format heterogeneity (JSON, XML, AML, Nodesets); abbreviations and naming (e.g. max_V, Max_feed_force_Fx); physical correctness (units, types); motivation for hybrid matching [5]. | [5] |

### 3.2 Ontology Alignment and Semantic Interoperability

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 3.2.1 Ontology alignment techniques | String/lexical similarity; semantic similarity (WordNet, embeddings); graph/structure; logical reasoning [5]. | [5] |
| 3.2.2 Reference ontologies in Industry 4.0 | eCl@ss, IEC CDD as reference ontologies; mapping parameter names to standards as ontology alignment [5]. | [5] |
| 3.2.3 Gaps for parameter-level mapping | Parameter-level vs ontology-level; standard-to-proprietary; use of eCl@ss/IEC CDD for enrichment not always covered; positioning of proposed methodology [5]. | [5] |

### 3.3 Semantic Enrichment

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 3.3.1 Enrichment strategies | Structured knowledge bases (eCl@ss, IEC CDD, thesauri); document-based; LLM-based generation [5]. | [5] |
| 3.3.2 Gaps: single-source and context | Single-source dependency; priority-based cascade; context for disambiguation; collection context and LLM selection from Top-K [5], [6], [7]. | [5], [6], [7] |
| 3.3.3 Industrial abbreviations | Rule-based abbreviation expansion with LLM fallback; context-aware normalization (e.g. V as voltage vs velocity by path) [6], [7]. | [6], [7] |

### 3.4 Matching Algorithms and Similarity Metrics

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 3.4.1 Common metrics | Levenshtein; Jaccard; cosine (TF-IDF, embeddings); constraint checks as filters [5]. | [5] |
| 3.4.2 Vector embeddings (optional) | Vector embeddings as numerical representations for similarity; relevance to semantic search and ML models [7]. | [7] |
| 3.4.3 Gaps addressed by hybrid matching | Unit/type as weighted components (e.g. 25% each); fixed weighted combination; determinism and interpretability; text-based semantic similarity without heavy embedding dependency [5], [6]. | [5], [6] |

### 3.5 Summary of Gaps and Positioning

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 3.5.1 Gap table | Multi-format extraction; unit/type as first-class; enrichment strategy; parameter-level mapping; abbreviations and context; standard-to-proprietary [5]. | [5] |

---

## Chapter 4: Proposed Methodology

**Chapter title (from your docs):** Methodology for Automated Parameter Mapping

### 4.1 Overview of the Methodology

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 4.1.1 Five-stage pipeline | Extraction → Normalization → Enrichment → Mapping → Reporting [5], [6]. | [5], [6] |
| 4.1.2 Meta-models | Tool-independent; semantic node collections for both data sources and simulation models; minimal common node attributes [5], [6]. | [5], [6] |

### 4.2 Semantic Node Extraction

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 4.2.1 Semantic node model | name, conceptual_definition, usage_of_data, value, value_type, unit, source_description, source_file, enriched, enrichment_source, metadata [5], [6]. | [5], [6] |
| 4.2.2 Extraction by format | JSON (AAS): submodelElements, conceptDescriptions; XML (AAS 2.0/3.0): namespaces, idShort, description, value, valueType, unit; AutomationML: InterfaceClassLibrary; EXM as XML [5], [6]. | [5], [6] |
| 4.2.3 SemanticNodeCollection | Common output of extractors; input to normalization and enrichment [6]. | [6] |

### 4.3 Normalization

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 4.3.1 Purpose | Abbreviation expansion for matching and library lookup; multiple search variants [5], [6]. | [5], [6] |
| 4.3.2 Process | Lowercasing; splitting by separators; rule-based expansion (dictionary); single-letter and embedded abbreviations; search variants (normalized, expanded, space/underscore); optional LLM fallback [5], [6]. | [5], [6] |
| 4.3.3 Context-aware normalization | Path from metadata (source_asset, source_submodel) for disambiguation (e.g. V → voltage vs velocity) [7]. | [7] |

### 4.4 Multi-Source Enrichment Strategy

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 4.4.1 Priority-based cascade | 1) Support documents; 2) eCl@ss; 3) IEC CDD; 4) Local LLM (e.g. Llama); 5) Cloud LLM (e.g. Gemini); early exit on first valid enrichment [5], [6]. | [5], [6] |
| 4.4.2 Context gathering | Related node names, units, value types, optional domain/submodel; used in LLM prompts for disambiguation [5], [6]. | [5], [6] |
| 4.4.3 Top-K search and LLM selection | Top-K (e.g. K=10) with similarity threshold; Jaccard on tokens; if multiple candidates, context-aware LLM selects best match [5], [6]. | [5], [6] |

### 4.5 Hybrid Matching Algorithm

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 4.5.1 Design rationale | Hard constraints: unit and type compatibility; soft: lexical and semantic similarity; weighted score so physically wrong matches are penalized [5], [6]. | [5], [6] |
| 4.5.2 Weights | Unit 25%, Type 25%, Lexical 20%, Semantic 30% [5], [6]. | [5], [6] |
| 4.5.3 Component definitions | Unit: exact 1.0, same quantity 0.7, incompatible 0.0, missing 0.5; Type: exact 1.0, compatible 0.7, incompatible 0.0, missing 0.5; Lexical: Levenshtein + Jaccard; Semantic: enriched text, word overlap, optional TF-IDF-like, phrase matching [5], [6]. | [5], [6] |
| 4.5.4 Score aggregation and match decision | Weighted score; threshold (e.g. 0.25); match type (EXACT, FUZZY, SEMANTIC); confidence (HIGH, MEDIUM, LOW); SemanticMatch objects [5], [6]. | [5], [6] |

### 4.6 Validation Mechanisms

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 4.6.1 Unit/type in scoring | Enforced by algorithm; incompatible pairs get low unit/type scores [5], [6]. | [5], [6] |
| 4.6.2 Similarity matrices and reports | Full pairwise scores; per-component matrices; match types and confidence; pipeline reports (matched/unmatched, match type and confidence distribution) [5], [6]. | [5], [6] |

### 4.7 Summary

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 4.7.1 Recap | Unified semantic node model; multi-format extraction; normalization; multi-source enrichment; hybrid matching; validation [5], [6]. | [5], [6] |

---

## Chapter 5: Implementation & Results

**Chapter title (from your docs):** Prototypical Implementation and Validation

### 5.1 Implementation Overview

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 5.1.1 Module breakdown | Extraction (datamap.py): JSON, XML, AML, EXM → SemanticNodeCollection; Enrichment (enrichment_module.py): NameNormalizer, Enricher, Top-K, LLM selection; Mapping (mapping_module.py): hybrid algorithm, match type/confidence; Integrated pipeline (integrated_pipeline.py): orchestration [5], [6]. | [5], [6] |
| 5.1.2 Data structures | SemanticNode, SemanticMatch as dataclasses; attributes as in Ch4 [5], [6]. | [5], [6] |
| 5.1.3 Key algorithms | Levenshtein, Jaccard, unit/type normalization; complexity (e.g. extraction O(n×d), matching O(n×m×k)) [6]. | [6] |

### 5.2 Application to Industrial Scenarios

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 5.2.1 Source and target | Source: AAS (JSON/XML), AML, OPC UA–derived node sets; target: simulation/engineering tool data models, parameter lists [5]. | [5] |
| 5.2.2 Use cases | AAS submodel elements → simulation inputs; AutomationML attributes → target parameter schema; AAS ↔ OPC UA–like parameter sets [5]. | [5] |
| 5.2.3 Domain/simulation context | Value stream objects, process objects, product-related settings (e.g. SimVSM-style documentation) as examples of target domain models [7]. | [7] |

### 5.3 Evaluation and Results

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 5.3.1 Qualitative results | Successful extraction from JSON, XML, AML; enrichment via cascade; mappings with match types and confidence; similarity matrices and HTML visualization [5]. | [5] |
| 5.3.2 Correctness | Unit/type suppress wrong matches; semantic/lexical allow correct matches despite naming differences [5]. | [5] |
| 5.3.3 Performance | Extraction/normalization fast; enrichment cost depends on library vs LLM; matching O(n×m); optional prefiltering/indexing for scale [5], [6]. | [5], [6] |
| 5.3.4 Accuracy and ground truth | High accuracy where ground truth available; errors in domain-specific terminology or when definitions missing; pipeline reports and optional precision/recall/F1 [5]. | [5] |

### 5.4 Training and Fine-Tuning (Optional)

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 5.4.1 Unit inference training | Training data (e.g. unit_inference_training_data.jsonl); categories (geometry, linear/rotary motion, force, torque, pressure, electricity, etc.); fine-tuning Llama for unit inference [7]. | [7] |
| 5.4.2 Context-aware normalization | Path-based disambiguation; Llama used for expansion with path context [7]. | [7] |

### 5.5 Benefits and Limitations

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 5.5.1 Benefits | Automated mapping; multi-format/multi-standard support; physical correctness; semantic understanding; context-aware disambiguation; interpretability; scalability [5]. | [5] |
| 5.5.2 Limitations | Domain-specific terminology; LLM cost/latency; ground truth availability; library maintenance; batch vs real-time [5]. | [5] |

### 5.6 Summary

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 5.6.1 Recap | Prototype applicable to industrial data; physical correctness, multi-source enrichment, interpretable results; benefits and limitations as above [5]. | [5] |

---

## Chapter 6: Conclusion

**Chapter title (from your docs):** Conclusion and Future Work

### 6.1 Summary of Key Findings

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 6.1.1 Interoperability context | Multiple standards (AAS, OPC UA, AutomationML) combined; complementary use motivates multi-format, semantics-preserving mapping [5]. | [5] |
| 6.1.2 State of the art gaps | Units/types not first-class; no multi-source enrichment cascade with parameter-level mapping; not standard-to-proprietary; methodology fills these gaps [5]. | [5] |
| 6.1.3 Methodology | Five-stage pipeline; unified semantic node model; weighted hybrid matching (25%, 25%, 20%, 30%); context-aware LLM from Top-K [5]. | [5] |
| 6.1.4 Prototype and validation | End-to-end applicability; benefits and limitations as in Ch5 [5]. | [5] |

### 6.2 Achievement of Objectives

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 6.2.1 Three objectives | State-of-the-art analysis (Ch3); mapping approach development (Ch4); prototypical application (Ch5) [5]. | [5] |
| 6.2.2 Tool-independence and standard-awareness | Meta-models as semantic node collections; designed for AAS, OPC UA, AutomationML, eCl@ss, IEC CDD; supports automatic use of simulation methods in production system engineering [5]. | [5] |

### 6.3 Recommendations for Future Work

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 6.3.1 ML and adaptation | Train/fine-tune matchers or embedding models on domain-specific mapping corpora [5]. | [5] |
| 6.3.2 Algorithm and performance | Prefiltering by unit/type; indexing; caching LLM responses; real-time or incremental matching [5]. | [5] |
| 6.3.3 Standards and formats | More AAS submodel types; OPC UA Nodeset parsing; further product classifications [5]. | [5] |
| 6.3.4 Integration and UI | Integration with simulation platforms (APIs, plugins); human-in-the-loop (review low-confidence mappings, tune weights, maintain support docs) [5]. | [5] |
| 6.3.5 Benchmarking | Benchmark datasets with reference mappings; reproducible comparison of methodology variants [5]. | [5] |

### 6.4 Concluding Remarks

| Section | Key technical concepts | Source(s) |
|--------|------------------------|-----------|
| 6.4.1 Contribution | Generalized methodology for automated parameter mapping; pipeline, multi-source enrichment, hybrid matching, prototype; contribution to industrial interoperability [5]. | [5] |

---

## References (from your thesis)

[1] AutomationML e.V., IDTA, OPC Foundation, VDMA (2023). *Diskussionspapier – Interoperabilität mit der Verwaltungsschale, OPC UA und AutomationML*. Version 5.3, 11.04.2023.

[2] Otto von Guericke Universität Magdeburg (2025). *Topic for Master Thesis: Generalized Methodology for Automated Mapping of Model Parameters between generalized digital twins and domain models*. Magdeburg.

[3] IEC PAS 63088:2017: *Smart manufacturing - Reference architecture model industry 4.0 (RAMI4.0)*.

[4] DIN SPEC 91345: 2016-04: *Referenzarchitekturmodell Industrie 4.0 (RAMI4.0)*.

**Note:** Sources [5]–[7] are your thesis documents and Documents folder. Add them to your reference list with full citations if you cite them in the thesis (e.g. “Technical Description of Semantic Node Data Mapping System”, “Context-Aware Normalization and Unit Inference”, “Training Data Summary for Unit Inference”, “What is Vector Embedding? | IBM”, etc.).

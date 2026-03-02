# Abstract

## Generalized Methodology for Automated Mapping of Model Parameters between Generalized Digital Twins and Domain Models

**Author:** Jithinkumar Nandanan  
**Program:** Master Systems Engineering for Manufacturing  
**Institution:** Otto von Guericke Universität Magdeburg, Faculty of Mechanical Engineering  
**Institute:** Institut für Engineering von Produkten und Systemen

---

### Abstract

The automation of automation engineering has emerged as a critical research area for enhancing efficiency and effectiveness in production system engineering. A fundamental challenge in this domain is the automated identification and mapping of appropriate data sources to tool-specific data models, particularly for simulation-based engineering decisions. As industrial data sources increasingly adopt standardized structures through initiatives such as the Industrial Digital Twin Association (IDTA), OPC Foundation, and AutomationML Association, the need for automated mapping methodologies becomes paramount.

This master's thesis presents a generalized methodology for automated mapping of model parameters between generalized digital twins and domain-specific simulation models. The work addresses the core problem of bridging standardized data sources (e.g., Asset Administration Shell formats) with proprietary simulation tool data models, enabling seamless data exchange and automated engineering decision support.

The developed methodology encompasses three main contributions: First, a comprehensive state-of-the-art analysis evaluates current simulation systems, standardized production system-related data sources, and existing data mapping technologies. Second, a novel mapping approach is introduced that employs a hybrid semantic matching algorithm combining unit compatibility, type compatibility, lexical similarity, and semantic similarity metrics. The approach incorporates a multi-source enrichment strategy utilizing eCl@ss and IEC CDD standards, support documents, and context-aware Large Language Models (LLMs) to enhance semantic node definitions. Third, a prototypical implementation demonstrates the methodology's applicability through a complete pipeline that extracts semantic nodes from heterogeneous file formats (JSON, XML, AML, EXM), enriches them with standardized definitions, and performs intelligent mapping between source and target data models.

The methodology is implemented as a modular system supporting multiple industrial standards including IDTA, OPC UA, AutomationML, eCl@ss, and IEC CDD. The system employs a priority-based enrichment cascade, Top-K similarity search with LLM-based candidate selection, and generates comprehensive similarity matrices and mapping reports. Key innovations include the hybrid matching algorithm with weighted components ensuring physical correctness through unit and type compatibility checks, while semantic similarity handles conceptual matches and abbreviations.

The prototypical application demonstrates the methodology's effectiveness in real-world industrial scenarios, achieving high accuracy through physical correctness validation, semantic understanding, and context-aware matching. Benefits include automated data mapping, reduced manual engineering effort, improved consistency, and enhanced interoperability between standardized data sources and simulation tools. Limitations are identified in handling highly domain-specific terminology and the computational overhead of LLM-based matching for large datasets. Recommendations for further development include integration of machine learning models for domain-specific adaptation, optimization of the matching algorithm for real-time applications, and extension to additional industrial standards and simulation platforms.

**Keywords:** Automated mapping, Digital twins, Domain models, Semantic matching, Asset Administration Shell, Production system engineering, Simulation systems, Industry 4.0

---

## Alternative Shorter Abstract (200-250 words)

### Abstract

The automation of automation engineering requires efficient mapping of standardized data sources to tool-specific simulation models. This master's thesis presents a generalized methodology for automated mapping of model parameters between generalized digital twins and domain-specific simulation models.

The work addresses the challenge of bridging standardized data sources (e.g., Asset Administration Shell formats from IDTA, OPC UA, AutomationML) with proprietary simulation tool data models. A three-part methodology is developed: (1) state-of-the-art analysis of simulation systems, standardized data sources, and mapping technologies; (2) a novel hybrid semantic matching approach combining unit compatibility, type compatibility, lexical similarity, and semantic similarity; (3) a prototypical implementation demonstrating the methodology through a complete pipeline.

The implementation extracts semantic nodes from heterogeneous file formats (JSON, XML, AML, EXM), enriches them using eCl@ss, IEC CDD standards, and context-aware LLMs, and performs intelligent mapping between source and target models. The hybrid matching algorithm ensures physical correctness through unit/type compatibility while semantic similarity handles conceptual matches. A priority-based enrichment cascade and Top-K search with LLM selection enable accurate mapping even with abbreviations and domain-specific terminology.

The prototypical application demonstrates effectiveness in industrial scenarios with high accuracy and automated data mapping capabilities. Benefits include reduced manual effort and improved interoperability. Limitations in domain-specific terminology handling and computational overhead are identified, with recommendations for machine learning integration and real-time optimization.

**Keywords:** Automated mapping, Digital twins, Semantic matching, Asset Administration Shell, Production system engineering

---

## German Abstract (Deutsche Zusammenfassung)

### Zusammenfassung

Die Automatisierung der Automatisierungstechnik erfordert eine effiziente Zuordnung standardisierter Datenquellen zu werkzeugspezifischen Simulationsmodellen. Diese Masterarbeit stellt eine verallgemeinerte Methodik zur automatisierten Zuordnung von Modellparametern zwischen verallgemeinerten digitalen Zwillingen und domänenspezifischen Simulationsmodellen vor.

Die Arbeit adressiert die Herausforderung der Verbindung standardisierter Datenquellen (z.B. Asset Administration Shell Formate von IDTA, OPC UA, AutomationML) mit proprietären Simulationswerkzeug-Datenmodellen. Eine dreiteilige Methodik wird entwickelt: (1) State-of-the-Art-Analyse von Simulationssystemen, standardisierten Datenquellen und Mapping-Technologien; (2) ein neuartiger hybrider semantischer Matching-Ansatz, der Einheitenkompatibilität, Typkompatibilität, lexikalische Ähnlichkeit und semantische Ähnlichkeit kombiniert; (3) eine prototypische Implementierung, die die Methodik durch eine vollständige Pipeline demonstriert.

Die Implementierung extrahiert semantische Knoten aus heterogenen Dateiformaten (JSON, XML, AML, EXM), reichert sie mit eCl@ss, IEC CDD Standards und kontextbewussten LLMs an und führt intelligente Zuordnungen zwischen Quell- und Zielmodellen durch. Der hybride Matching-Algorithmus gewährleistet physikalische Korrektheit durch Einheiten-/Typkompatibilität, während semantische Ähnlichkeit konzeptuelle Übereinstimmungen behandelt. Eine prioritätsbasierte Anreicherungskaskade und Top-K-Suche mit LLM-Auswahl ermöglichen genaue Zuordnungen auch bei Abkürzungen und domänenspezifischer Terminologie.

Die prototypische Anwendung demonstriert Wirksamkeit in industriellen Szenarien mit hoher Genauigkeit und automatisierten Datenzuordnungsfähigkeiten. Vorteile umfassen reduzierten manuellen Aufwand und verbesserte Interoperabilität. Einschränkungen bei der Behandlung domänenspezifischer Terminologie und Rechenaufwand werden identifiziert, mit Empfehlungen für Machine-Learning-Integration und Echtzeitoptimierung.

**Schlüsselwörter:** Automatisierte Zuordnung, Digitale Zwillinge, Semantisches Matching, Asset Administration Shell, Produktionssystemtechnik

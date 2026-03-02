#!/usr/bin/env python3
"""
Streamlit Interface for Semantic Node Mapping Pipeline

This interface provides a step-by-step workflow:
1. Extract nodes and show details
2. User-triggered enrichment
3. Show enriched nodes (editable)
4. One-by-one matching with user selection and reasoning
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Import pipeline components
from semantic_node_enhanced import SemanticNode, SemanticNodeCollection, create_semantic_node_from_extraction
from enrichment_module import SemanticNodeEnricher, normalize_collection
from mapping_module import SemanticMatcher, SemanticMatch
import datamap

# Page configuration
st.set_page_config(
    page_title="Semantic Node Mapping",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Workflow states
WORKFLOW_STATES = {
    "EXTRACTION": "extraction",
    "NORMALIZATION": "normalization",
    "ENRICHMENT": "enrichment",
    "EDIT_NODES": "edit_nodes",
    "MATCHING": "matching",
    "COMPLETE": "complete"
}

# Initialize session state
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = WORKFLOW_STATES["EXTRACTION"]
if 'source_nodes' not in st.session_state:
    st.session_state.source_nodes = []
if 'target_nodes' not in st.session_state:
    st.session_state.target_nodes = []
if 'source_nodes_collection' not in st.session_state:
    st.session_state.source_nodes_collection = None
if 'target_nodes_collection' not in st.session_state:
    st.session_state.target_nodes_collection = None
if 'source_files' not in st.session_state:
    st.session_state.source_files = []
if 'target_files' not in st.session_state:
    st.session_state.target_files = []
if 'support_files' not in st.session_state:
    st.session_state.support_files = []
if 'support_urls' not in st.session_state:
    st.session_state.support_urls = []
if 'enricher' not in st.session_state:
    st.session_state.enricher = None
if 'enricher_initialized' not in st.session_state:
    st.session_state.enricher_initialized = False
if 'enrichment_complete' not in st.session_state:
    st.session_state.enrichment_complete = False
if 'normalization_complete' not in st.session_state:
    st.session_state.normalization_complete = False
if 'current_matching_index' not in st.session_state:
    st.session_state.current_matching_index = 0
if 'user_matches' not in st.session_state:
    st.session_state.user_matches = []  # List of {source_node, target_node, reasoning}
if 'all_possible_matches' not in st.session_state:
    st.session_state.all_possible_matches = {}  # Cache for each source node


def save_uploaded_files(uploaded_files, folder_name: str) -> str:
    """Save uploaded files to a temporary folder."""
    temp_dir = Path(tempfile.mkdtemp())
    target_folder = temp_dir / folder_name
    target_folder.mkdir(parents=True, exist_ok=True)
    
    for uploaded_file in uploaded_files:
        file_path = target_folder / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    
    return str(target_folder)


def extract_nodes_from_files(files_folder: str) -> List[Dict]:
    """Extract semantic nodes from files in a folder."""
    if not os.path.exists(files_folder):
        return []
    
    extractor = datamap.SemanticNodeExtractor(data_folder=files_folder)
    extractor.process_all_files()
    
    nodes = []
    for node_dict in extractor.semantic_nodes:
        d = {
            "Name": node_dict.get("Name", ""),
            "Conceptual definition": node_dict.get("Conceptual definition", ""),
            "Usage of data (Affordance)": node_dict.get("Usage of data", ""),
            "Value": str(node_dict.get("Value", "")),
            "Value type": node_dict.get("Value type", "String"),
            "Unit": node_dict.get("Unit", ""),
            "Source description": node_dict.get("Source description", ""),
            "Source file": node_dict.get("Source file", ""),
            "Enriched": False,
            "Enrichment source": ""
        }
        if node_dict.get("Source asset"):
            d["Source asset"] = node_dict["Source asset"]
        if node_dict.get("Source submodel"):
            d["Source submodel"] = node_dict["Source submodel"]
        if node_dict.get("_metadata"):
            d["_metadata"] = node_dict["_metadata"]
        nodes.append(d)
    
    return nodes


def nodes_to_dataframe(nodes: List[Dict]) -> pd.DataFrame:
    """Convert nodes list to DataFrame."""
    if not nodes:
        return pd.DataFrame()
    return pd.DataFrame(nodes)


def dataframe_to_nodes(df: pd.DataFrame, drop_deleted: bool = True) -> List[Dict]:
    """Convert DataFrame back to nodes list. If drop_deleted=True, rows with Delete?=True are removed and Delete? column is dropped."""
    if df.empty:
        return []
    if drop_deleted and "Delete?" in df.columns:
        df = df[df["Delete?"] != True].drop(columns=["Delete?"], errors="ignore")
    return df.to_dict('records')


def dict_to_semantic_node(node_dict: Dict) -> SemanticNode:
    """Convert dictionary to SemanticNode."""
    # Safely extract _metadata (may be dict, string, None, or missing)
    metadata_raw = node_dict.get("_metadata")
    if isinstance(metadata_raw, dict):
        meta = dict(metadata_raw)
    elif isinstance(metadata_raw, str):
        # Try to parse JSON string
        try:
            import json
            meta = json.loads(metadata_raw) if metadata_raw else {}
        except:
            meta = {}
    elif metadata_raw is None:
        meta = {}
    else:
        # Fallback: try to convert, but default to empty dict
        try:
            meta = dict(metadata_raw) if metadata_raw else {}
        except:
            meta = {}
    # Persist source asset/submodel for enrichment context (from AAS extraction or prior round-trip)
    if node_dict.get("Source asset"):
        meta["source_asset"] = node_dict.get("Source asset", "")
    if node_dict.get("Source submodel"):
        meta["source_submodel"] = node_dict.get("Source submodel", "")
    return create_semantic_node_from_extraction(
        name=node_dict.get("Name", ""),
        description=node_dict.get("Conceptual definition", ""),
        value=node_dict.get("Value", ""),
        value_type=node_dict.get("Value type", "String"),
        unit=node_dict.get("Unit", ""),
        source_file=node_dict.get("Source file", ""),
        metadata=meta
    )


def semantic_node_to_dict(node: SemanticNode) -> Dict:
    """Convert SemanticNode to dictionary."""
    d = {
        "Name": node.name,
        "Conceptual definition": node.conceptual_definition,
        "Usage of data (Affordance)": node.usage_of_data,
        "Value": str(node.value) if node.value else "",
        "Value type": node.value_type,
        "Unit": node.unit,
        "Source description": node.source_description,
        "Source file": node.source_file,
        "Enriched": node.enriched,
        "Enrichment source": node.enrichment_source or ""
    }
    if node.metadata:
        if node.metadata.get("source_asset"):
            d["Source asset"] = node.metadata["source_asset"]
        if node.metadata.get("source_submodel"):
            d["Source submodel"] = node.metadata["source_submodel"]
        d["_metadata"] = node.metadata
    return d


def get_or_create_enricher(support_folder: str = None, support_urls: List[str] = None):
    """Get or create enricher, caching it in session state for performance."""
    if st.session_state.enricher_initialized and st.session_state.enricher:
        return st.session_state.enricher
    
    # Initialize enricher with progress indicator
    with st.spinner("Initializing enrichment engine (loading eClass library - first time may take a minute)..."):
        enricher = SemanticNodeEnricher(
            support_folder=support_folder if support_folder and os.path.exists(support_folder) else None,
            support_urls=support_urls or [],
            use_llama=True,
            use_gemini=False,
            use_openai=False  # Only use Llama for AI-generated descriptions
        )
        st.session_state.enricher = enricher
        st.session_state.enricher_initialized = True
    
    return enricher


def get_all_possible_matches(source_node: SemanticNode, target_collection: SemanticNodeCollection, matcher: SemanticMatcher) -> List[SemanticMatch]:
    """Get all possible matches for a source node, sorted by confidence score."""
    candidates = []
    
    for target_node in target_collection.nodes:
        match_result = matcher._calculate_match(source_node, target_node)
        if match_result and match_result.score > 0.25:  # Minimum threshold
            candidates.append(match_result)
    
    # Sort by score (highest first)
    candidates.sort(key=lambda m: m.score, reverse=True)
    return candidates


def enrich_nodes_collection(collection: SemanticNodeCollection, enricher: SemanticNodeEnricher, node_type: str) -> Dict:
    """Enrich a collection of nodes."""
    enricher.collection = collection
    stats = enricher.enrich_collection(collection)
    return stats


# Main UI
st.title("🔗 Semantic Node Mapping Pipeline")
st.markdown("Step-by-step workflow for semantic node extraction, enrichment, and matching.")

# Sidebar for file uploads and workflow control
with st.sidebar:
    st.header("📁 File Upload")
    
    # Source files upload
    st.subheader("Source Files")
    source_files = st.file_uploader(
        "Upload source files (XML, JSON, AML, EXM, SIMVSM)",
        type=['xml', 'json', 'aml', 'exm', 'simvsm'],
        accept_multiple_files=True,
        key="source_uploader"
    )
    
    # Target files upload
    st.subheader("Target Files")
    target_files = st.file_uploader(
        "Upload target files (XML, JSON, AML, EXM, SIMVSM)",
        type=['xml', 'json', 'aml', 'exm', 'simvsm'],
        accept_multiple_files=True,
        key="target_uploader"
    )
    
    # Support files upload
    st.subheader("Support Files")
    support_files = st.file_uploader(
        "Upload support files (TXT, HTML, PDF, DOCX, JSON, MD, YAML, CSV)",
        type=['txt', 'html', 'htm', 'pdf', 'docx', 'json', 'md', 'yaml', 'yml', 'csv'],
        accept_multiple_files=True,
        key="support_uploader"
    )
    
    # Support URLs input
    st.subheader("Support URLs (Optional)")
    support_urls_text = st.text_area(
        "Enter HTML URLs (one per line)",
        help="Paste HTML help/documentation URLs here. Each URL should be on a separate line. Example: https://example.com/help.html",
        key="support_urls_input",
        height=100,
        value="\n".join(st.session_state.support_urls) if st.session_state.support_urls else ""
    )
    
    # Parse URLs from text area
    if support_urls_text:
        urls = [url.strip() for url in support_urls_text.split('\n') if url.strip() and (url.strip().startswith('http://') or url.strip().startswith('https://'))]
        if urls:
            st.session_state.support_urls = urls
            st.info(f"📎 {len(urls)} URL(s) will be loaded")
        else:
            st.session_state.support_urls = []
    else:
        st.session_state.support_urls = []
    
    st.divider()
    st.header("🔄 Workflow Control")
    
    # Show current workflow state
    state_labels = {
        WORKFLOW_STATES["EXTRACTION"]: "1️⃣ Extraction",
        WORKFLOW_STATES["NORMALIZATION"]: "2️⃣ Normalize",
        WORKFLOW_STATES["ENRICHMENT"]: "3️⃣ Enrichment",
        WORKFLOW_STATES["EDIT_NODES"]: "4️⃣ Edit Nodes",
        WORKFLOW_STATES["MATCHING"]: "5️⃣ Matching",
        WORKFLOW_STATES["COMPLETE"]: "✅ Complete"
    }
    st.info(f"**Current Step:** {state_labels.get(st.session_state.workflow_state, 'Unknown')}")
    
    # Reset button
    if st.button("🔄 Reset Workflow", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.workflow_state = WORKFLOW_STATES["EXTRACTION"]
        st.rerun()

# STEP 1: EXTRACTION
if st.session_state.workflow_state == WORKFLOW_STATES["EXTRACTION"]:
    st.header("Step 1: Extract Nodes")
    st.markdown("Upload files and extract semantic nodes from them.")
    
    if st.button("🔍 Extract Nodes", type="primary", use_container_width=True):
        if source_files or target_files:
            with st.spinner("Extracting semantic nodes..."):
                # Save and extract source files
                if source_files:
                    source_folder = save_uploaded_files(source_files, "source")
                    st.session_state.source_files = source_files
                    st.session_state.source_nodes = extract_nodes_from_files(source_folder)
                    st.success(f"✅ Extracted {len(st.session_state.source_nodes)} source nodes")
                
                # Save and extract target files
                if target_files:
                    target_folder = save_uploaded_files(target_files, "target")
                    st.session_state.target_files = target_files
                    st.session_state.target_nodes = extract_nodes_from_files(target_folder)
                    st.success(f"✅ Extracted {len(st.session_state.target_nodes)} target nodes")
                
                # Save support files
                if support_files:
                    support_folder = save_uploaded_files(support_files, "support")
                    st.session_state.support_files = support_files
                    st.session_state.support_folder = support_folder
                    st.success(f"✅ Saved {len(support_files)} support files")
                
                # Do not auto-advance: stay on Step 1 so user can remove nodes
                # if st.session_state.source_nodes or st.session_state.target_nodes:
                #     st.session_state.workflow_state = WORKFLOW_STATES["NORMALIZATION"]
                #     st.rerun()
                st.rerun()
        else:
            st.warning("⚠️ Please upload at least source or target files")
    
    # Show extracted nodes with editable table and Delete? option
    if st.session_state.source_nodes or st.session_state.target_nodes:
        st.subheader("Review & remove nodes (optional)")
        st.markdown("Check **Delete?** to remove nodes you don't want to include. Then click **Apply removals & continue**.")
        
        col1, col2 = st.columns(2)
        edited_source_df = None
        edited_target_df = None
        
        with col1:
            if st.session_state.source_nodes:
                st.write(f"**Source Nodes:** {len(st.session_state.source_nodes)}")
                source_df = nodes_to_dataframe(st.session_state.source_nodes)
                if "Delete?" not in source_df.columns:
                    source_df["Delete?"] = False
                source_df["_idx"] = range(len(source_df))
                display_cols = [c for c in source_df.columns if c != "_metadata"]
                edited_source_df = st.data_editor(
                    source_df[display_cols],
                    use_container_width=True,
                    hide_index=True,
                    key="extraction_source_editor",
                    column_config={
                        "Delete?": st.column_config.CheckboxColumn("🗑️ Delete?", default=False, help="Check to remove this node"),
                        "_idx": st.column_config.NumberColumn("#", width="small"),
                    },
                    disabled=[c for c in display_cols if c not in ("Delete?",)],
                )
        
        with col2:
            if st.session_state.target_nodes:
                st.write(f"**Target Nodes:** {len(st.session_state.target_nodes)}")
                target_df = nodes_to_dataframe(st.session_state.target_nodes)
                if "Delete?" not in target_df.columns:
                    target_df["Delete?"] = False
                target_df["_idx"] = range(len(target_df))
                display_cols = [c for c in target_df.columns if c != "_metadata"]
                edited_target_df = st.data_editor(
                    target_df[display_cols],
                    use_container_width=True,
                    hide_index=True,
                    key="extraction_target_editor",
                    column_config={
                        "Delete?": st.column_config.CheckboxColumn("🗑️ Delete?", default=False, help="Check to remove this node"),
                        "_idx": st.column_config.NumberColumn("#", width="small"),
                    },
                    disabled=[c for c in display_cols if c not in ("Delete?",)],
                )
        
        if st.button("➡️ Apply removals & continue to Normalization", type="primary", use_container_width=True):
            if edited_source_df is not None:
                keep = edited_source_df[edited_source_df["Delete?"] != True]
                st.session_state.source_nodes = [
                    st.session_state.source_nodes[int(idx)]
                    for idx in keep["_idx"]
                ]
            if edited_target_df is not None:
                keep = edited_target_df[edited_target_df["Delete?"] != True]
                st.session_state.target_nodes = [
                    st.session_state.target_nodes[int(idx)]
                    for idx in keep["_idx"]
                ]
            st.session_state.workflow_state = WORKFLOW_STATES["NORMALIZATION"]
            st.rerun()

# STEP 2: NORMALIZATION (Llama)
elif st.session_state.workflow_state == WORKFLOW_STATES["NORMALIZATION"]:
    st.header("Step 2: Normalize Nodes")
    st.markdown("Normalize node names using local Llama AI (expand abbreviations). Results are shown by metadata (Source asset / Submodel).")
    
    if not st.session_state.source_nodes and not st.session_state.target_nodes:
        st.warning("⚠️ No nodes extracted. Please go back to extraction step.")
        if st.button("⬅️ Back to Extraction"):
            st.session_state.workflow_state = WORKFLOW_STATES["EXTRACTION"]
            st.rerun()
    else:
        if st.button("⬅️ Back to Extraction"):
            st.session_state.workflow_state = WORKFLOW_STATES["EXTRACTION"]
            st.rerun()
        if st.button("🦙 Normalize with Llama", type="primary", use_container_width=True):
            with st.spinner("Normalizing node names with local Llama..."):
                source_collection = SemanticNodeCollection()
                target_collection = SemanticNodeCollection()
                for node_dict in st.session_state.source_nodes:
                    node = dict_to_semantic_node(node_dict)
                    if node_dict.get("Usage of data (Affordance)"):
                        node.usage_of_data = node_dict.get("Usage of data (Affordance)", "")
                    source_collection.add_node(node)
                for node_dict in st.session_state.target_nodes:
                    node = dict_to_semantic_node(node_dict)
                    if node_dict.get("Usage of data (Affordance)"):
                        node.usage_of_data = node_dict.get("Usage of data (Affordance)", "")
                    target_collection.add_node(node)
                normalize_collection(source_collection)
                normalize_collection(target_collection)
                st.session_state.source_nodes = [semantic_node_to_dict(n) for n in source_collection.nodes]
                st.session_state.target_nodes = [semantic_node_to_dict(n) for n in target_collection.nodes]
                st.session_state.source_nodes_collection = source_collection
                st.session_state.target_nodes_collection = target_collection
                st.session_state.normalization_complete = True
                st.rerun()
        
        def _show_normalized_by_metadata(nodes_list, title):
            if not nodes_list:
                return
            st.subheader(title)
            meta_raw = lambda d: d.get("_metadata")
            meta_dict = lambda d: meta_raw(d) if isinstance(meta_raw(d), dict) else {}
            groups = {}
            for node_dict in nodes_list:
                meta = meta_dict(node_dict)
                asset = node_dict.get("Source asset") or meta.get("source_asset", "—")
                submodel = node_dict.get("Source submodel") or meta.get("source_submodel", "—")
                key = (str(asset), str(submodel))
                if key not in groups:
                    groups[key] = []
                norm = meta.get("normalized_name", "") or "—"
                groups[key].append({
                    "Name": node_dict.get("Name", ""),
                    "Normalized name": norm,
                    "Conceptual definition": node_dict.get("Conceptual definition", "—"),
                    "Value type": node_dict.get("Value type", "—"),
                    "Unit": node_dict.get("Unit", "—"),
                    "Value": node_dict.get("Value", "—"),
                    "Source asset": asset,
                    "Source submodel": submodel
                })
            for (asset, submodel), rows in sorted(groups.items()):
                label = f"Asset: {asset}  |  Submodel: {submodel}"
                with st.expander(label, expanded=True):
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        
        if st.session_state.normalization_complete and (st.session_state.source_nodes or st.session_state.target_nodes):
            st.success("✅ Normalization complete. Review normalized names below (by metadata).")
        if st.session_state.source_nodes or st.session_state.target_nodes:
            _show_normalized_by_metadata(st.session_state.source_nodes, "Source nodes (by metadata)")
            _show_normalized_by_metadata(st.session_state.target_nodes, "Target nodes (by metadata)")
        
        if st.button("➡️ Continue to Enrichment", type="primary", use_container_width=True):
            st.session_state.workflow_state = WORKFLOW_STATES["ENRICHMENT"]
            st.rerun()

# STEP 3: ENRICHMENT
elif st.session_state.workflow_state == WORKFLOW_STATES["ENRICHMENT"]:
    st.header("Step 3: Enrich Nodes")
    st.markdown("Enrich extracted nodes with additional information from eCl@ss, IEC CDD, and support documents.")
    
    if not st.session_state.source_nodes and not st.session_state.target_nodes:
        st.warning("⚠️ No nodes extracted. Please go back to extraction step.")
        if st.button("⬅️ Back to Extraction"):
            st.session_state.workflow_state = WORKFLOW_STATES["EXTRACTION"]
            st.rerun()
    else:
        if st.button("⬅️ Back to Normalization"):
            st.session_state.workflow_state = WORKFLOW_STATES["NORMALIZATION"]
            st.rerun()
        # Get support folder
        support_folder = getattr(st.session_state, 'support_folder', None)
        if not support_folder and st.session_state.support_files:
            support_folder = save_uploaded_files(st.session_state.support_files, "support")
            st.session_state.support_folder = support_folder
        
        # Get support URLs
        support_urls = st.session_state.get('support_urls', [])
        if support_urls:
            st.info(f"📎 Will fetch content from {len(support_urls)} URL(s)")
        
        if st.button("🔍 Start Enrichment", type="primary", use_container_width=True):
            with st.spinner("Enriching nodes... This may take a few minutes."):
                # Initialize enricher
                enricher = get_or_create_enricher(support_folder, support_urls=support_urls)
                
                # Convert to SemanticNodeCollections
                source_collection = SemanticNodeCollection()
                target_collection = SemanticNodeCollection()
                
                # Add source nodes
                for node_dict in st.session_state.source_nodes:
                    node = dict_to_semantic_node(node_dict)
                    if node_dict.get("Usage of data (Affordance)"):
                        node.usage_of_data = node_dict.get("Usage of data (Affordance)")
                    source_collection.add_node(node)
                
                # Add target nodes
                for node_dict in st.session_state.target_nodes:
                    node = dict_to_semantic_node(node_dict)
                    if node_dict.get("Usage of data (Affordance)"):
                        node.usage_of_data = node_dict.get("Usage of data (Affordance)")
                    target_collection.add_node(node)
                
                # Enrich source nodes only (target is not enriched – used as-is for mapping)
                if source_collection.nodes:
                    st.write("Enriching source nodes...")
                    source_stats = enrich_nodes_collection(source_collection, enricher, "source")
                    st.success(f"✅ Enriched {source_stats.get('enriched_from_eclass', 0) + source_stats.get('enriched_from_ieccdd', 0) + source_stats.get('enriched_from_documents', 0) + source_stats.get('enriched_from_llama', 0) + source_stats.get('enriched_from_gemini', 0) + source_stats.get('enriched_from_openai', 0)} source nodes")
                if target_collection.nodes:
                    st.info(f"ℹ️ Target nodes ({len(target_collection.nodes)}) kept as extracted (no enrichment).")
                
                # Update session state with enriched source nodes and unchanged target nodes
                st.session_state.source_nodes = [semantic_node_to_dict(node) for node in source_collection.nodes]
                st.session_state.target_nodes = [semantic_node_to_dict(node) for node in target_collection.nodes]
                st.session_state.source_nodes_collection = source_collection
                st.session_state.target_nodes_collection = target_collection
                st.session_state.enrichment_complete = True
                st.session_state.workflow_state = WORKFLOW_STATES["EDIT_NODES"]
                st.rerun()
        
        # Show enrichment preview
        if st.session_state.enrichment_complete:
            st.success("✅ Enrichment completed!")
            if st.button("➡️ Continue to Edit Nodes", type="primary", use_container_width=True):
                st.session_state.workflow_state = WORKFLOW_STATES["EDIT_NODES"]
                st.rerun()

# STEP 3: EDIT NODES
elif st.session_state.workflow_state == WORKFLOW_STATES["EDIT_NODES"]:
    st.header("Step 3: Review and Edit Enriched Nodes")
    st.markdown("Review the enriched nodes and make any necessary edits to both source and target nodes.")
    
    if not st.session_state.enrichment_complete:
        st.warning("⚠️ Please complete enrichment first.")
        if st.button("⬅️ Back to Enrichment"):
            st.session_state.workflow_state = WORKFLOW_STATES["ENRICHMENT"]
            st.rerun()
    else:
        # Tabs for editing source and target nodes
        tab1, tab2 = st.tabs(["📊 Source Nodes", "📊 Target Nodes"])
        
        with tab1:
            st.subheader("Source Semantic Nodes")
            if st.session_state.source_nodes:
                source_df = nodes_to_dataframe(st.session_state.source_nodes)
                if "Delete?" not in source_df.columns:
                    source_df["Delete?"] = False
                edited_source_df = st.data_editor(
                    source_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "Name": st.column_config.TextColumn("Name", required=True),
                        "Conceptual definition": st.column_config.TextColumn("Conceptual Definition", width="large"),
                        "Usage of data (Affordance)": st.column_config.TextColumn("Usage of Data", width="large"),
                        "Value": st.column_config.TextColumn("Value"),
                        "Value type": st.column_config.TextColumn("Value Type"),
                        "Unit": st.column_config.TextColumn("Unit"),
                        "Source description": st.column_config.TextColumn("Source Description", width="large"),
                        "Enriched": st.column_config.CheckboxColumn("Enriched"),
                        "Enrichment source": st.column_config.TextColumn("Enrichment Source"),
                        "Delete?": st.column_config.CheckboxColumn("🗑️ Delete?", default=False, help="Check to remove this node"),
                    },
                    key="source_editor"
                )
                st.session_state.source_nodes = dataframe_to_nodes(edited_source_df)
                st.info(f"📝 Total source nodes: {len(st.session_state.source_nodes)} (check **Delete?** to remove unwanted nodes, then rerun or go to next step)")
            else:
                st.info("No source nodes available.")
        
        with tab2:
            st.subheader("Target Semantic Nodes")
            if st.session_state.target_nodes:
                target_df = nodes_to_dataframe(st.session_state.target_nodes)
                if "Delete?" not in target_df.columns:
                    target_df["Delete?"] = False
                edited_target_df = st.data_editor(
                    target_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "Name": st.column_config.TextColumn("Name", required=True),
                        "Conceptual definition": st.column_config.TextColumn("Conceptual Definition", width="large"),
                        "Usage of data (Affordance)": st.column_config.TextColumn("Usage of Data", width="large"),
                        "Value": st.column_config.TextColumn("Value"),
                        "Value type": st.column_config.TextColumn("Value Type"),
                        "Unit": st.column_config.TextColumn("Unit"),
                        "Source description": st.column_config.TextColumn("Source Description", width="large"),
                        "Enriched": st.column_config.CheckboxColumn("Enriched"),
                        "Enrichment source": st.column_config.TextColumn("Enrichment Source"),
                        "Delete?": st.column_config.CheckboxColumn("🗑️ Delete?", default=False, help="Check to remove this node"),
                    },
                    key="target_editor"
                )
                st.session_state.target_nodes = dataframe_to_nodes(edited_target_df)
                st.info(f"📝 Total target nodes: {len(st.session_state.target_nodes)} (check **Delete?** to remove unwanted nodes, then rerun or go to next step)")
            else:
                st.info("No target nodes available.")
        
        # Update collections from edited data
        if st.session_state.source_nodes:
            source_collection = SemanticNodeCollection()
            for node_dict in st.session_state.source_nodes:
                node = dict_to_semantic_node(node_dict)
                if node_dict.get("Usage of data (Affordance)"):
                    node.usage_of_data = node_dict.get("Usage of data (Affordance)")
                source_collection.add_node(node)
            st.session_state.source_nodes_collection = source_collection
        
        if st.session_state.target_nodes:
            target_collection = SemanticNodeCollection()
            for node_dict in st.session_state.target_nodes:
                node = dict_to_semantic_node(node_dict)
                if node_dict.get("Usage of data (Affordance)"):
                    node.usage_of_data = node_dict.get("Usage of data (Affordance)")
                target_collection.add_node(node)
            st.session_state.target_nodes_collection = target_collection
        
        st.divider()
        if st.button("➡️ Continue to Matching", type="primary", use_container_width=True):
            if st.session_state.source_nodes and st.session_state.target_nodes:
                st.session_state.workflow_state = WORKFLOW_STATES["MATCHING"]
                st.session_state.current_matching_index = 0
                st.session_state.user_matches = []
                st.rerun()
            else:
                st.warning("⚠️ Both source and target nodes are required for matching.")

# STEP 4: MATCHING (One-by-one)
elif st.session_state.workflow_state == WORKFLOW_STATES["MATCHING"]:
    st.header("Step 4: Match Nodes")
    st.markdown("Match source nodes with target nodes one by one. Review each match and provide your reasoning.")
    
    if not st.session_state.source_nodes_collection or not st.session_state.target_nodes_collection:
        st.warning("⚠️ Please complete previous steps first.")
        if st.button("⬅️ Back to Edit Nodes"):
            st.session_state.workflow_state = WORKFLOW_STATES["EDIT_NODES"]
            st.rerun()
    else:
        source_collection = st.session_state.source_nodes_collection
        target_collection = st.session_state.target_nodes_collection
        total_source_nodes = len(source_collection.nodes)
        current_index = st.session_state.current_matching_index
        
        if current_index >= total_source_nodes:
            # All nodes matched, move to complete
            st.session_state.workflow_state = WORKFLOW_STATES["COMPLETE"]
            st.rerun()
        else:
            # Get current source node
            current_source_node = source_collection.nodes[current_index]
            
            # Progress indicator
            progress = (current_index + 1) / total_source_nodes
            st.progress(progress, text=f"Matching node {current_index + 1} of {total_source_nodes}")
            
            # Display current source node
            st.subheader(f"Source Node {current_index + 1}: {current_source_node.name}")
            
            # Display source node in table format
            source_node_data = pd.DataFrame([{
                "Name": current_source_node.name,
                "Conceptual Definition": current_source_node.conceptual_definition or "N/A",
                "Usage of Data": current_source_node.usage_of_data or "N/A",
                "Value": str(current_source_node.value) if current_source_node.value else "N/A",
                "Value Type": current_source_node.value_type,
                "Unit": current_source_node.unit or "N/A",
                "Source Description": current_source_node.source_description or "N/A",
                "Source File": current_source_node.source_file or "N/A"
            }])
            st.dataframe(source_node_data, use_container_width=True, hide_index=True)
            
            # Get possible matches
            if current_source_node.name not in st.session_state.all_possible_matches:
                with st.spinner("Finding possible matches..."):
                    matcher = SemanticMatcher()
                    matches = get_all_possible_matches(current_source_node, target_collection, matcher)
                    st.session_state.all_possible_matches[current_source_node.name] = matches
            
            matches = st.session_state.all_possible_matches[current_source_node.name]
            
            # Limit to top 3 candidates
            top_matches = matches[:3] if len(matches) > 3 else matches
            
            if top_matches:
                st.markdown(f"**Top 3 candidate matches** — select one to expand and see full details. Only the selected match is expanded to avoid confusion.**")
                
                # Selection first (so we know which expander to open)
                selected_match_index = st.radio(
                    "Select the best match:",
                    range(len(top_matches)),
                    format_func=lambda i: f"Rank {i+1}: {top_matches[i].target_node.name} (Score: {top_matches[i].score:.3f}, Confidence: {top_matches[i].confidence.value})",
                    key=f"match_selection_{current_index}"
                )
                
                selected_match = top_matches[selected_match_index]
                
                # One expander per candidate: only the selected one is expanded
                for idx, match in enumerate(top_matches):
                    is_selected = (idx == selected_match_index)
                    label = f"Rank {idx+1}: {match.target_node.name} — Score: {match.score:.3f} ({match.confidence.value})"
                    with st.expander(label, expanded=is_selected):
                        st.markdown("**Target node details**")
                        target_node_data = pd.DataFrame([{
                            "Name": match.target_node.name,
                            "Conceptual Definition": match.target_node.conceptual_definition or "N/A",
                            "Usage of Data": match.target_node.usage_of_data or "N/A",
                            "Value": str(match.target_node.value) if match.target_node.value else "N/A",
                            "Value Type": match.target_node.value_type,
                            "Unit": match.target_node.unit or "N/A",
                            "Source Description": match.target_node.source_description or "N/A",
                            "Source File": match.target_node.source_file or "N/A"
                        }])
                        st.dataframe(target_node_data, use_container_width=True, hide_index=True)
                        comp = match.details.get("component_scores", {})
                        st.markdown("**Match details**")
                        match_details_data = pd.DataFrame([{
                            "Overall Score": f"{match.score:.3f}",
                            "Confidence": match.confidence.value,
                            "Match Type": match.match_type.value,
                            "Unit Compatibility": f"{comp.get('unit_compatibility', 0):.3f}",
                            "Type Compatibility": f"{comp.get('type_compatibility', 0):.3f}",
                            "Lexical Similarity": f"{comp.get('lexical_similarity', 0):.3f}",
                            "Semantic Similarity": f"{comp.get('semantic_similarity', 0):.3f}"
                        }])
                        st.dataframe(match_details_data, use_container_width=True, hide_index=True)
                
                # Optional reasoning input
                reasoning = st.text_area(
                    "Reasoning (Optional):",
                    key=f"reasoning_{current_index}",
                    height=100,
                    placeholder="Optionally explain your reasoning for selecting this match... (You can skip this)"
                )
                
                # Navigation buttons
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                with col_btn1:
                    if current_index > 0:
                        if st.button("⬅️ Previous", use_container_width=True):
                            st.session_state.current_matching_index = current_index - 1
                            st.rerun()
                
                with col_btn2:
                    if st.button("⏭️ Skip (No Match)", use_container_width=True):
                        # Save skip
                        st.session_state.user_matches.append({
                            "source_node": current_source_node.name,
                            "target_node": None,
                            "reasoning": reasoning.strip() if reasoning.strip() else "Skipped - No suitable match found",
                            "match_score": 0,
                            "confidence": "none"
                        })
                        st.session_state.current_matching_index = current_index + 1
                        st.rerun()
                
                with col_btn3:
                    if st.button("✅ Confirm Match", type="primary", use_container_width=True):
                        # Save match (reasoning is optional)
                        st.session_state.user_matches.append({
                            "source_node": current_source_node.name,
                            "target_node": selected_match.target_node.name,
                            "reasoning": reasoning.strip() if reasoning.strip() else "No reasoning provided",
                            "match_score": round(selected_match.score, 3),
                            "confidence": selected_match.confidence.value,
                            "match_type": selected_match.match_type.value
                        })
                        st.session_state.current_matching_index = current_index + 1
                        st.rerun()
            else:
                st.warning("⚠️ No matches found for this source node.")
                
                # Navigation buttons for no matches
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    if current_index > 0:
                        if st.button("⬅️ Previous", use_container_width=True):
                            st.session_state.current_matching_index = current_index - 1
                            st.rerun()
                
                with col_btn2:
                    if st.button("⏭️ Skip", type="primary", use_container_width=True):
                        st.session_state.user_matches.append({
                            "source_node": current_source_node.name,
                            "target_node": None,
                            "reasoning": "No matches found",
                            "match_score": 0,
                            "confidence": "none"
                        })
                        st.session_state.current_matching_index = current_index + 1
                        st.rerun()

# STEP 5: COMPLETE
elif st.session_state.workflow_state == WORKFLOW_STATES["COMPLETE"]:
    st.header("✅ Matching Complete")
    st.success("All source nodes have been processed!")
    
    # Show summary
    total_matches = len([m for m in st.session_state.user_matches if m.get("target_node")])
    total_skipped = len([m for m in st.session_state.user_matches if not m.get("target_node")])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Processed", len(st.session_state.user_matches))
    with col2:
        st.metric("Successful Matches", total_matches)
    with col3:
        st.metric("Skipped/No Match", total_skipped)
    
    # Show all matches
    st.subheader("All Matches")
    if st.session_state.user_matches:
        matches_data = []
        for match in st.session_state.user_matches:
            matches_data.append({
                "Source Node": match.get("source_node", ""),
                "Target Node": match.get("target_node", "No Match"),
                "Match Score": match.get("match_score", 0),
                "Confidence": match.get("confidence", "none"),
                "Match Type": match.get("match_type", "none"),
                "Reasoning": match.get("reasoning", "")
            })
        
        matches_df = pd.DataFrame(matches_data)
        st.dataframe(matches_df, use_container_width=True)
        
        # Download button
        csv = matches_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"mapping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No matches recorded.")
    
    # Reset button
    if st.button("🔄 Start New Mapping", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.workflow_state = WORKFLOW_STATES["EXTRACTION"]
        st.rerun()

# Initial state - show instructions
else:
    st.info("""
    👋 **Welcome to the Semantic Node Mapping Pipeline!**
    
    **Workflow Steps:**
    1. 📁 **Extraction**: Upload files and extract semantic nodes
    2. 🔍 **Enrichment**: Enrich nodes with additional information
    3. ✏️ **Edit Nodes**: Review and edit enriched nodes
    4. 🔗 **Matching**: Match source nodes with target nodes one by one
    5. ✅ **Complete**: Review and download results
    
    **Getting Started:**
    - Upload your source and target files in the sidebar
    - Click "Extract Nodes" to begin
    - Follow the step-by-step workflow
    
    **Features:**
    - ✅ Step-by-step guided workflow
    - ✅ Editable node tables
    - ✅ Context-aware LLM enrichment
    - ✅ One-by-one matching with user reasoning
    - ✅ Comprehensive match details and confidence scores
    """)

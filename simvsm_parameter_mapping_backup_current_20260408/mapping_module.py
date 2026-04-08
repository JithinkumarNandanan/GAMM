#!/usr/bin/env python3
"""
Semantic Mapping Module

This module compares semantic nodes from source and target files to find matches.
It supports mapping between different standard data models:
- IDTA (Industrial Digital Twin Association)
- OPC UA Information Models
- AutomationML (AML)
- And other AAS-based formats

The module uses multiple matching strategies:
1. Exact name matching
2. Fuzzy name matching
3. Unit-based matching
4. Type-based matching
5. Semantic similarity matching
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
import json
import re
import csv
from enum import Enum
from semantic_node_enhanced import SemanticNode, SemanticNodeCollection

# Vector embeddings for semantic similarity (optional enhancement)
EMBEDDING_MODEL = None
EMBEDDINGS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    
    # Try to load a powerful semantic model
    # BAAI/bge-base-en-v1.5 is the current state-of-the-art for embedding similarity
    try:
        EMBEDDING_MODEL = SentenceTransformer('BAAI/bge-base-en-v1.5')
        EMBEDDINGS_AVAILABLE = True
        print("Vector embeddings enabled: Using sentence-transformers (BAAI/bge-base-en-v1.5)")
    except Exception as e:
        print(f"Warning: Could not load sentence transformer model: {e}")
        print("Falling back to text-based semantic similarity")
except ImportError:
    print("Info: sentence-transformers not installed. Using text-based semantic similarity.")
    print("To enable vector embeddings, install: pip install sentence-transformers scikit-learn")
except Exception as e:
    print(f"Warning: Could not initialize embeddings: {e}")


class MatchType(Enum):
    """Types of matches between semantic nodes."""
    EXACT = "exact"  # Exact name match
    FUZZY = "fuzzy"  # Similar names
    UNIT_BASED = "unit_based"  # Same unit and type
    TYPE_BASED = "type_based"  # Same type, compatible context
    SEMANTIC = "semantic"  # Semantic similarity
    NO_MATCH = "no_match"  # No match found


class MatchConfidence(Enum):
    """Confidence levels for matches."""
    HIGH = "high"  # >90% confidence
    MEDIUM = "medium"  # 60-90% confidence
    LOW = "low"  # 30-60% confidence
    VERY_LOW = "very_low"  # <30% confidence


@dataclass
class SemanticMatch:
    """
    Represents a match between a source and target semantic node.
    
    Attributes:
        source_node: Node from source file
        target_node: Node from target file
        match_type: Type of match
        confidence: Confidence level
        score: Matching score (0.0 to 1.0)
        details: Additional matching details
    """
    source_node: SemanticNode
    target_node: SemanticNode
    match_type: MatchType
    confidence: MatchConfidence
    score: float
    details: Dict[str, any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert match to dictionary for export."""
        src_meta = self.source_node.metadata or {}
        tgt_meta = self.target_node.metadata or {}
        return {
            "source_idShort": src_meta.get("id_short") or src_meta.get("idShort") or self.source_node.name,
            "source_name": self.source_node.name,
            "source_normalized_name": src_meta.get("normalized_name") or self.source_node.name,
            "target_idShort": tgt_meta.get("id_short") or tgt_meta.get("idShort") or self.target_node.name,
            "target_name": self.target_node.name,
            "target_normalized_name": tgt_meta.get("normalized_name") or self.target_node.name,
            "source_value": str(self.source_node.value),
            "target_value": str(self.target_node.value),
            "source_type": self.source_node.value_type,
            "target_type": self.target_node.value_type,
            "source_unit": self.source_node.unit,
            "target_unit": self.target_node.unit,
            "match_type": self.match_type.value,
            "confidence": self.confidence.value,
            "score": round(self.score, 3),
            "details": self.details
        }
    
    def __repr__(self) -> str:
        return f"Match({self.source_node.name} → {self.target_node.name}, {self.confidence.value}, {self.score:.2f})"


class SemanticMatcher:
    """
    Main semantic matching engine that compares source and target semantic nodes.
    """
    
    def __init__(self, 
                 exact_match_threshold: float = 1.0,
                 fuzzy_match_threshold: float = 0.7,
                 semantic_match_threshold: float = 0.5):
        """
        Initialize semantic matcher.
        
        Args:
            exact_match_threshold: Threshold for exact matches (default: 1.0)
            fuzzy_match_threshold: Threshold for fuzzy matches (default: 0.7)
            semantic_match_threshold: Threshold for semantic matches (default: 0.5)
        """
        self.exact_threshold = exact_match_threshold
        self.fuzzy_threshold = fuzzy_match_threshold
        self.semantic_threshold = semantic_match_threshold
        
        self.matches: List[SemanticMatch] = []
        self.unmatched_source: List[SemanticNode] = []
        self.unmatched_target: List[SemanticNode] = []
    
    def match_collections(self, 
                         source: SemanticNodeCollection,
                         target: SemanticNodeCollection) -> List[SemanticMatch]:
        """
        Match all nodes from source collection to target collection.
        
        Args:
            source: Source semantic node collection
            target: Target semantic node collection
        
        Returns:
            List of semantic matches
        """
        self.matches = []
        self.unmatched_source = []
        self.unmatched_target = list(target.nodes)  # Start with all target nodes
        
        for source_node in source.nodes:
            best_match = self._find_best_match(source_node, target.nodes)
            
            if best_match:
                self.matches.append(best_match)
                # Remove matched target node from unmatched list
                if best_match.target_node in self.unmatched_target:
                    self.unmatched_target.remove(best_match.target_node)
            else:
                self.unmatched_source.append(source_node)
        
        return self.matches
    
    def _find_best_match(self, 
                        source_node: SemanticNode,
                        target_nodes: List[SemanticNode]) -> Optional[SemanticMatch]:
        """
        Find the best match for a source node among target nodes.
        
        Args:
            source_node: Node to match
            target_nodes: Candidate target nodes
        
        Returns:
            Best matching SemanticMatch or None
        """
        candidates = []
        
        for target_node in target_nodes:
            match_result = self._calculate_match(source_node, target_node)
            if match_result and match_result.score > 0.25:  # Minimum threshold (matches _calculate_match)
                candidates.append(match_result)
                # Debug output for first few matches
                if len(candidates) <= 3:
                    comp_scores = match_result.details.get("component_scores", {})
                    print(f"    [DEBUG] Match candidate: {source_node.name} → {target_node.name}")
                    print(f"      Score: {match_result.score:.3f} | Unit: {comp_scores.get('unit_compatibility', 0):.2f} | "
                          f"Type: {comp_scores.get('type_compatibility', 0):.2f} | "
                          f"Lexical: {comp_scores.get('lexical_similarity', 0):.2f} | "
                          f"Semantic: {comp_scores.get('semantic_similarity', 0):.2f}")
        
        if not candidates:
            # Debug: Show why no matches found
            if len(target_nodes) > 0:
                print(f"    [DEBUG] No matches found for '{source_node.name}' (tried {len(target_nodes)} targets)")
                # Try to show why first target didn't match
                test_match = self._calculate_match(source_node, target_nodes[0])
                if test_match:
                    print(f"      First target '{target_nodes[0].name}' score: {test_match.score:.3f} (below threshold 0.3)")
                    comp_scores = test_match.details.get("component_scores", {})
                    print(f"        Components - Unit: {comp_scores.get('unit_compatibility', 0):.2f}, "
                          f"Type: {comp_scores.get('type_compatibility', 0):.2f}, "
                          f"Lexical: {comp_scores.get('lexical_similarity', 0):.2f}, "
                          f"Semantic: {comp_scores.get('semantic_similarity', 0):.2f}")
                else:
                    print(f"      First target '{target_nodes[0].name}' - no match calculated (score was None)")
            return None
        
        # Return candidate with highest score
        best = max(candidates, key=lambda m: m.score)
        print(f"    [OK] Best match: {source_node.name} → {best.target_node.name} (score: {best.score:.3f})")
        return best
    
    def _calculate_match(self, 
                        source: SemanticNode,
                        target: SemanticNode) -> Optional[SemanticMatch]:
        """
        Calculate match score using Hybrid Matching Algorithm.
        
        Combines four components:
        1. Unit Compatibility (1.0) - Physical sanity check
        2. Type Compatibility (1.0) - Structural integrity check
        3. Lexical Similarity (0.950) - Character-level overlap
        4. Semantic Similarity (0.892) - Conceptual meaning
        
        Args:
            source: Source semantic node
            target: Target semantic node
        
        Returns:
            SemanticMatch object or None
        """
        # Calculate all four components
        unit_compat = self._unit_compatibility(source, target)
        type_compat = self._type_compatibility(source, target)
        lexical_sim = self._lexical_similarity(source, target)
        semantic_sim = self._semantic_similarity_hybrid(source, target)
        
        # Component scores for details
        component_scores = {
            "unit_compatibility": unit_compat,
            "type_compatibility": type_compat,
            "lexical_similarity": lexical_sim,
            "semantic_similarity": semantic_sim
        }
        
        # Weighted combination (prioritize semantic and compatibility)
        # Weights: Unit=0.25, Type=0.25, Lexical=0.20, Semantic=0.30
        weights = {
            "unit": 0.25,
            "type": 0.25,
            "lexical": 0.20,
            "semantic": 0.30
        }
        
        # Calculate weighted confidence score
        confidence_score = (
            unit_compat * weights["unit"] +
            type_compat * weights["type"] +
            lexical_sim * weights["lexical"] +
            semantic_sim * weights["semantic"]
        )
        
        # Determine match type based on highest contributing component
        if unit_compat == 1.0 and type_compat == 1.0 and lexical_sim >= 0.9:
            match_type = MatchType.EXACT
        elif lexical_sim >= 0.7:
            match_type = MatchType.FUZZY
        elif semantic_sim >= 0.6:
            match_type = MatchType.SEMANTIC
        elif unit_compat == 1.0 or type_compat == 1.0:
            match_type = MatchType.UNIT_BASED if unit_compat == 1.0 else MatchType.TYPE_BASED
        else:
            match_type = MatchType.SEMANTIC  # Default to semantic
        
        # Only return match if confidence score meets minimum threshold
        # Lower threshold to 0.25 to catch more semantic matches
        if confidence_score < 0.25:  # Minimum threshold
            return None
        
        confidence = self._determine_confidence(confidence_score)
        
        return SemanticMatch(
            source_node=source,
            target_node=target,
            match_type=match_type,
            confidence=confidence,
            score=confidence_score,
            details={
                "method": "hybrid_matching",
                "component_scores": component_scores,
                "weights": weights
            }
        )
    
    def _unit_compatibility(self, source: SemanticNode, target: SemanticNode) -> float:
        """
        Unit Compatibility Component (Score: 1.0 if match, 0.0 if not).
        
        Ensures physical sanity by checking if measurement units align exactly
        with the standardized unit. Units are normalized (e.g., sec, seconds, s -> s).
        
        Returns:
            1.0 if units match (after normalization), 0.0 otherwise
        """
        if not source.unit or not target.unit:
            # If one or both units are missing, return 0.5 (neutral)
            return 0.5
        
        source_unit = self._normalize_unit(source.unit)
        target_unit = self._normalize_unit(target.unit)
        
        if source_unit == target_unit:
            return 1.0
        
        # Check if units are compatible (same physical quantity)
        if self._are_units_compatible(source.unit, target.unit):
            return 0.7  # Partial compatibility
        
        return 0.0
    
    def _type_compatibility(self, source: SemanticNode, target: SemanticNode) -> float:
        """
        Type Compatibility Component (Score: 1.0 if match, 0.0 if not).
        
        Ensures structural integrity by verifying that the normalized data format
        is syntactically compatible with the type required by the target.
        This is MANDATORY for syntactic correctness (e.g., xs:float vs xs:float).
        
        Returns:
            1.0 if types match exactly, 0.7 if compatible, 0.0 if incompatible
        """
        if not source.value_type or not target.value_type:
            # If one or both types are missing, return 0.5 (neutral)
            return 0.5
        
        source_type = self._normalize_type(source.value_type)
        target_type = self._normalize_type(target.value_type)
        
        if source_type == target_type:
            return 1.0
        
        # Check if types are compatible (e.g., float and double)
        if self._are_types_compatible(source.value_type, target.value_type):
            return 0.7  # Compatible but not exact
        
        return 0.0
    
    def _lexical_similarity(self, source: SemanticNode, target: SemanticNode) -> float:
        """
        Lexical Similarity Component (Score: 0.0 to 1.0).
        
        Quantifies character-level overlap between parameter names using
        Levenshtein distance (fuzzy matching). Provides fast initial filtering
        and secondary confirmation. High score (near 1.0) reinforces that names
        are highly related, but is insufficient on its own for abbreviations.
        
        Returns:
            Similarity score between 0.0 and 1.0
        """
        source_name = source.name.lower().strip()
        target_name = target.name.lower().strip()
        
        # Exact match
        if source_name == target_name:
            return 1.0
        
        # Levenshtein distance
        distance = self._levenshtein_distance(source_name, target_name)
        max_len = max(len(source_name), len(target_name))
        
        if max_len == 0:
            return 1.0
        
        # Convert distance to similarity (0.0 to 1.0)
        similarity = 1.0 - (distance / max_len)
        
        # Also check token-based similarity (Jaccard) for multi-word names
        source_tokens = set(re.split(r'[_\-\s]+', source_name))
        target_tokens = set(re.split(r'[_\-\s]+', target_name))
        
        if source_tokens and target_tokens:
            intersection = len(source_tokens & target_tokens)
            union = len(source_tokens | target_tokens)
            jaccard = intersection / union if union > 0 else 0.0
            
            # Combine Levenshtein and Jaccard (weighted average)
            similarity = (similarity * 0.6) + (jaccard * 0.4)
        
        return max(0.0, min(1.0, similarity))
    
    def _semantic_similarity_hybrid(self, source: SemanticNode, target: SemanticNode) -> float:
        """
        Semantic Similarity Component (Score: 0.0 to 1.0).
        
        Measures true conceptual meaning using vector embeddings and cosine similarity.
        This is the core intelligence that overcomes linguistic barriers and matches
        concepts based on meaning (e.g., "max flow rate" vs "largest volume per time").
        
        Uses vector embeddings if available (sentence-transformers), otherwise falls back
        to enhanced text-based similarity.
        
        Returns:
            Semantic similarity score between 0.0 and 1.0
        """
        # Build pseudo-sentence from node information
        source_text = self._build_pseudo_sentence(source)
        target_text = self._build_pseudo_sentence(target)
        
        if not source_text or not target_text:
            return 0.0
        
        # Try vector embeddings first (if available)
        if EMBEDDINGS_AVAILABLE and EMBEDDING_MODEL:
            try:
                # Generate embeddings for both texts
                source_embedding = EMBEDDING_MODEL.encode(source_text, convert_to_numpy=True)
                target_embedding = EMBEDDING_MODEL.encode(target_text, convert_to_numpy=True)
                
                # Calculate cosine similarity
                # Reshape for sklearn cosine_similarity (needs 2D arrays)
                source_emb_2d = source_embedding.reshape(1, -1)
                target_emb_2d = target_embedding.reshape(1, -1)
                
                cosine_sim = cosine_similarity(source_emb_2d, target_emb_2d)[0][0]
                
                # Normalize to 0-1 range (cosine similarity is already -1 to 1, but typically 0-1 for similar texts)
                # Apply a slight adjustment to make it more comparable to text-based scores
                embedding_score = max(0.0, min(1.0, cosine_sim))
                
                # Combine with text-based similarity for robustness
                # This gives us the best of both worlds
                text_score = self._semantic_similarity_text_based(source_text, target_text)
                
                # Weighted combination: 70% embeddings (better semantic understanding), 30% text-based (handles exact matches)
                final_score = (embedding_score * 0.7) + (text_score * 0.3)
                
                return max(0.0, min(1.0, final_score))
            except Exception as e:
                # If embeddings fail, fall back to text-based
                print(f"Warning: Embedding calculation failed, using text-based similarity: {e}")
                return self._semantic_similarity_text_based(source_text, target_text)
        else:
            # Fall back to text-based similarity
            return self._semantic_similarity_text_based(source_text, target_text)
    
    def _semantic_similarity_text_based(self, source_text: str, target_text: str) -> float:
        """
        Enhanced text-based similarity (fallback when embeddings not available).
        
        Uses word overlap, TF-IDF-like weighting, and phrase matching.
        
        Returns:
            Semantic similarity score between 0.0 and 1.0
        """
        # 1. Word overlap (Jaccard)
        source_words = set(re.findall(r'\b\w+\b', source_text.lower()))
        target_words = set(re.findall(r'\b\w+\b', target_text.lower()))
        
        if not source_words or not target_words:
            return 0.0
        
        intersection = len(source_words & target_words)
        union = len(source_words | target_words)
        jaccard = intersection / union if union > 0 else 0.0
        
        # 2. TF-IDF-like weighted similarity (emphasize important words)
        important_words = {'maximum', 'minimum', 'average', 'rate', 'speed', 'velocity',
                          'force', 'torque', 'pressure', 'temperature', 'distance', 'range',
                          'accuracy', 'precision', 'repetition', 'reproducibility'}
        
        source_important = source_words & important_words
        target_important = target_words & important_words
        
        if source_important and target_important:
            important_overlap = len(source_important & target_important) / len(source_important | target_important)
            jaccard = (jaccard * 0.7) + (important_overlap * 0.3)
        
        # 3. Substring matching for key phrases
        source_lower = source_text.lower()
        target_lower = target_text.lower()
        
        # Check for common phrases
        common_phrases = [
            'maximum', 'minimum', 'peak', 'upper', 'lower', 'limit',
            'linear', 'rotational', 'angular', 'axial', 'radial',
            'force', 'torque', 'velocity', 'speed', 'acceleration',
            'accuracy', 'precision', 'reproducibility', 'repeatability'
        ]
        
        source_phrases = [p for p in common_phrases if p in source_lower]
        target_phrases = [p for p in common_phrases if p in target_lower]
        
        if source_phrases and target_phrases:
            phrase_overlap = len(set(source_phrases) & set(target_phrases)) / len(set(source_phrases) | set(target_phrases))
            jaccard = (jaccard * 0.8) + (phrase_overlap * 0.2)
        
        return max(0.0, min(1.0, jaccard))
    
    def _build_pseudo_sentence(self, node: SemanticNode) -> str:
        """
        Build a pseudo-sentence from node information for semantic matching.
        
        Combines Context (Parent/Asset), Name, Conceptual Definition, and Usage of Data 
        into a single text string. This is the input for semantic encoding (vector embedding).
        """
        parts = []
        
        # 1. Inject Contextual Metadata (Crucial for differentiating duplicate names like "SetupTime")
        context_parts = []
        
        # Check source_asset (often used in target structures)
        if node.metadata.get("source_asset"):
            context_parts.append(str(node.metadata["source_asset"]))
            
        # Check parent_id (often used in extracted source properties)
        if node.metadata.get("parent_id"):
            context_parts.append(str(node.metadata["parent_id"]))
            
        # Check source_submodel (often used in AAS structure)
        if node.metadata.get("source_submodel"):
            context_parts.append(str(node.metadata["source_submodel"]))
            
        # If we found any context, prepend it in brackets to strongly associate it
        if context_parts:
            # Join unique context parts to avoid repetition (e.g., if parent_id == source_asset)
            unique_context = " ".join(dict.fromkeys(context_parts))
            parts.append(f"[{unique_context}]")
        
        # 2. Add standard node fields
        if node.name:
            parts.append(node.name)
        
        if node.conceptual_definition:
            parts.append(node.conceptual_definition)
        
        if node.usage_of_data:  # Fixed: use usage_of_data instead of usage
            parts.append(node.usage_of_data)
        
        return " ".join(parts)
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.
        
        Returns the minimum number of single-character edits (insertions, deletions,
        or substitutions) required to change one string into the other.
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _normalize_unit(self, unit: str) -> str:
        """
        Normalize unit to standard form (e.g., sec, seconds, s -> s).
        
        This is part of the Normalization Layer (Layer 3) where units are
        converted to a single, standardized form.
        """
        if not unit:
            return ""
        
        unit_lower = unit.lower().strip()
        
        # Time units
        time_units = {
            's': 's', 'sec': 's', 'second': 's', 'seconds': 's',
            'min': 'min', 'minute': 'min', 'minutes': 'min',
            'h': 'h', 'hr': 'h', 'hour': 'h', 'hours': 'h'
        }
        
        # Length units
        length_units = {
            'm': 'm', 'meter': 'm', 'metre': 'm', 'meters': 'm', 'metres': 'm',
            'mm': 'mm', 'millimeter': 'mm', 'millimetre': 'mm',
            'cm': 'cm', 'centimeter': 'cm', 'centimetre': 'cm',
            'km': 'km', 'kilometer': 'km', 'kilometre': 'km'
        }
        
        # Mass units
        mass_units = {
            'kg': 'kg', 'kilogram': 'kg', 'kilograms': 'kg',
            'g': 'g', 'gram': 'g', 'grams': 'g'
        }
        
        # Force units
        force_units = {
            'n': 'N', 'newton': 'N', 'newtons': 'N'
        }
        
        # Torque units
        torque_units = {
            'nm': 'Nm', 'n*m': 'Nm', 'newton meter': 'Nm', 'newton metre': 'Nm'
        }
        
        # Pressure units
        pressure_units = {
            'bar': 'bar', 'pa': 'Pa', 'pascal': 'Pa', 'pascals': 'Pa',
            'kpa': 'kPa', 'mpa': 'MPa', 'psi': 'psi'
        }
        
        # Temperature units
        temp_units = {
            '°c': '°C', 'c': '°C', 'celsius': '°C',
            '°f': '°F', 'f': '°F', 'fahrenheit': '°F',
            'k': 'K', 'kelvin': 'K'
        }
        
        # Speed/velocity units (m/s and km/h are same quantity; normalize to m/s for consistency)
        speed_units = {
            'm/s': 'm/s', 'mps': 'm/s', 'meter per second': 'm/s',
            'km/h': 'm/s', 'kmh': 'm/s', 'kilometer per hour': 'm/s',
            'mm/s': 'mm/s',
            'rpm': 'rpm', 'rotations per minute': 'rpm', 'rev/min': 'rpm'
        }
        
        # Combine all unit maps
        all_units = {**time_units, **length_units, **mass_units, **force_units,
                    **torque_units, **pressure_units, **temp_units, **speed_units}
        
        # Remove common prefixes/suffixes and check
        unit_clean = unit_lower.replace('°', '').replace(' ', '')
        
        if unit_clean in all_units:
            return all_units[unit_clean]
        
        # If not found, return normalized version (remove spaces, lowercase)
        return unit_clean
    
    def _exact_name_match(self, source: SemanticNode, target: SemanticNode) -> float:
        """Calculate exact name match score."""
        source_name = source.name.lower().strip()
        target_name = target.name.lower().strip()
        
        if source_name == target_name:
            # Bonus if units also match
            if source.unit and target.unit and source.unit == target.unit:
                return 1.0
            return 0.95
        
        return 0.0
    
    def _fuzzy_name_match(self, source: SemanticNode, target: SemanticNode) -> float:
        """Calculate fuzzy name match score using various string similarity metrics."""
        source_name = source.name.lower().strip()
        target_name = target.name.lower().strip()
        
        # Tokenize names
        source_tokens = set(source_name.replace('_', ' ').replace('-', ' ').split())
        target_tokens = set(target_name.replace('_', ' ').replace('-', ' ').split())
        
        if not source_tokens or not target_tokens:
            return 0.0
        
        # Jaccard similarity
        intersection = len(source_tokens & target_tokens)
        union = len(source_tokens | target_tokens)
        jaccard = intersection / union if union > 0 else 0.0
        
        # Bonus for unit match
        unit_bonus = 0.0
        if source.unit and target.unit:
            if source.unit.lower() == target.unit.lower():
                unit_bonus = 0.15
        
        # Bonus for type match
        type_bonus = 0.0
        if source.value_type and target.value_type:
            if self._normalize_type(source.value_type) == self._normalize_type(target.value_type):
                type_bonus = 0.1
        
        return min(1.0, jaccard + unit_bonus + type_bonus)
    
    def _unit_type_match(self, source: SemanticNode, target: SemanticNode) -> float:
        """Calculate match score based on unit and type compatibility."""
        score = 0.0
        
        # Type match
        if source.value_type and target.value_type:
            if self._normalize_type(source.value_type) == self._normalize_type(target.value_type):
                score += 0.5
            elif self._are_types_compatible(source.value_type, target.value_type):
                score += 0.3
        
        # Unit match
        if source.unit and target.unit:
            if source.unit.lower() == target.unit.lower():
                score += 0.5
            elif self._are_units_compatible(source.unit, target.unit):
                score += 0.3
        
        return score
    
    def _semantic_similarity(self, source: SemanticNode, target: SemanticNode) -> float:
        """Calculate semantic similarity based on definitions."""
        if not source.conceptual_definition or not target.conceptual_definition:
            return 0.0
        
        source_def = source.conceptual_definition.lower()
        target_def = target.conceptual_definition.lower()
        
        # Simple word-based similarity
        source_words = set(source_def.split())
        target_words = set(target_def.split())
        
        if not source_words or not target_words:
            return 0.0
        
        intersection = len(source_words & target_words)
        union = len(source_words | target_words)
        
        return intersection / union if union > 0 else 0.0
    
    def _normalize_type(self, value_type: str) -> str:
        """Normalize value type for comparison."""
        type_map = {
            'xs:string': 'string',
            'string': 'string',
            'xs:float': 'float',
            'xs:double': 'float',
            'float': 'float',
            'double': 'float',
            'real': 'float',
            'xs:integer': 'integer',
            'xs:int': 'integer',
            'integer': 'integer',
            'int': 'integer',
            'xs:boolean': 'boolean',
            'boolean': 'boolean',
            'bool': 'boolean'
        }
        return type_map.get(value_type.lower(), value_type.lower())
    
    def _are_types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two types are compatible."""
        numeric_types = {'float', 'double', 'real', 'integer', 'int'}
        
        norm1 = self._normalize_type(type1)
        norm2 = self._normalize_type(type2)
        
        # Same type
        if norm1 == norm2:
            return True
        
        # Both numeric
        if norm1 in numeric_types and norm2 in numeric_types:
            return True
        
        return False
    
    def _are_units_compatible(self, unit1: str, unit2: str) -> bool:
        """Check if two units are compatible (same physical quantity)."""
        # Temperature units
        temp_units = {'°c', 'c', 'celsius', 'k', 'kelvin', '°f', 'f', 'fahrenheit'}
        # Pressure units
        pressure_units = {'bar', 'pa', 'pascal', 'psi', 'kpa', 'mpa'}
        # Length units
        length_units = {'m', 'mm', 'cm', 'km', 'in', 'ft'}
        # Mass units
        mass_units = {'kg', 'g', 't', 'ton', 'lb'}
        # Speed/velocity (m/s and km/h are same quantity)
        speed_units = {'m/s', 'mps', 'km/h', 'kmh', 'mm/s', 'velocity', 'speed'}
        # Rotational speed
        angular_speed_units = {'rpm', 'rad/s', '1/s', 'rotations per minute'}
        # Torque
        torque_units = {'nm', 'n·m', 'n*m', 'newton meter', 'newton metre'}
        
        unit1_lower = unit1.lower().strip()
        unit2_lower = unit2.lower().strip()
        
        unit_groups = [temp_units, pressure_units, length_units, mass_units,
                       speed_units, angular_speed_units, torque_units]
        
        for group in unit_groups:
            if unit1_lower in group and unit2_lower in group:
                return True
        
        return False
    
    def _determine_confidence(self, score: float) -> MatchConfidence:
        """Determine confidence level based on match score."""
        if score >= 0.9:
            return MatchConfidence.HIGH
        elif score >= 0.6:
            return MatchConfidence.MEDIUM
        elif score >= 0.3:
            return MatchConfidence.LOW
        else:
            return MatchConfidence.VERY_LOW
    
    def get_statistics(self) -> Dict[str, any]:
        """Get matching statistics."""
        if not self.matches:
            return {
                "total_matches": 0,
                "high_confidence": 0,
                "medium_confidence": 0,
                "low_confidence": 0,
                "unmatched_source": 0,
                "unmatched_target": 0
            }
        
        return {
            "total_matches": len(self.matches),
            "high_confidence": len([m for m in self.matches if m.confidence == MatchConfidence.HIGH]),
            "medium_confidence": len([m for m in self.matches if m.confidence == MatchConfidence.MEDIUM]),
            "low_confidence": len([m for m in self.matches if m.confidence == MatchConfidence.LOW]),
            "by_type": {
                mt.value: len([m for m in self.matches if m.match_type == mt])
                for mt in MatchType if mt != MatchType.NO_MATCH
            },
            "average_score": sum(m.score for m in self.matches) / len(self.matches),
            "unmatched_source": len(self.unmatched_source),
            "unmatched_target": len(self.unmatched_target)
        }
    
    def export_matches(self, filepath: str):
        """Export matches to JSON file."""
        export_data = {
            "matches": [m.to_dict() for m in self.matches],
            "unmatched_source": [
                {"name": n.name, "value": str(n.value), "type": n.value_type, "unit": n.unit}
                for n in self.unmatched_source
            ],
            "unmatched_target": [
                {"name": n.name, "value": str(n.value), "type": n.value_type, "unit": n.unit}
                for n in self.unmatched_target
            ],
            "statistics": self.get_statistics()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"Matches exported to: {filepath}")
    
    def generate_similarity_matrix(self, 
                                   source: SemanticNodeCollection,
                                   target: SemanticNodeCollection,
                                   output_file: str = None) -> List[List[float]]:
        """
        Generate a similarity matrix showing scores for all source-target pairs.
        
        Creates a matrix where:
        - Rows = Source nodes (manufacturer's specifications)
        - Columns = Target nodes (standardized ECLASS definitions)
        - Cells = Matching scores (0.0 to 1.0)
        
        Args:
            source: Source semantic node collection
            target: Target semantic node collection
            output_file: Optional CSV file path to save the matrix
        
        Returns:
            2D list of scores [source_index][target_index]
        """
        matrix = []
        source_names = []
        target_names = []
        
        print(f"\n  Generating similarity matrix for {len(source.nodes)} source × {len(target.nodes)} target nodes...")
        
        # Get target names once
        target_names = [tn.name for tn in target.nodes]
        
        # Calculate scores for all pairs
        for source_node in source.nodes:
            source_names.append(source_node.name)
            row = []
            
            for target_node in target.nodes:
                match_result = self._calculate_match(source_node, target_node)
                score = match_result.score if match_result else 0.0
                row.append(score)
            
            matrix.append(row)
        
        # Save to CSV if file path provided
        if output_file:
            self._export_matrix_to_csv(matrix, source_names, target_names, output_file)
        
        return matrix
    
    def _export_matrix_to_csv(self, 
                              matrix: List[List[float]],
                              source_names: List[str],
                              target_names: List[str],
                              filepath: str):
        """Export similarity matrix to CSV file."""
        # target_names is already a list of strings
        column_names = target_names if target_names else []
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header row
            header = ['Source Node'] + column_names
            writer.writerow(header)
            
            # Write data rows
            for i, source_name in enumerate(source_names):
                row = [source_name] + [f"{score:.3f}" for score in matrix[i]]
                writer.writerow(row)
        
        print(f"  [OK] Similarity matrix exported to: {filepath}")
    
    def generate_detailed_similarity_matrix(self,
                                           source: SemanticNodeCollection,
                                           target: SemanticNodeCollection,
                                           output_file: str = None) -> Dict:
        """
        Generate a detailed similarity matrix with component scores.
        
        Creates a comprehensive matrix showing:
        - Overall confidence score
        - Unit compatibility score
        - Type compatibility score
        - Lexical similarity score
        - Semantic similarity score
        
        Args:
            source: Source semantic node collection
            target: Target semantic node collection
            output_file: Optional CSV file path to save the matrix
        
        Returns:
            Dictionary with matrix data and metadata
        """
        print(f"\n  Generating detailed similarity matrix...")
        
        source_names = [node.name for node in source.nodes]
        target_names = [node.name for node in target.nodes]
        
        # Matrices for each component
        overall_scores = []
        unit_scores = []
        type_scores = []
        lexical_scores = []
        semantic_scores = []
        
        # Calculate all component scores for every pair
        for source_node in source.nodes:
            overall_row = []
            unit_row = []
            type_row = []
            lexical_row = []
            semantic_row = []
            
            for target_node in target.nodes:
                # Calculate all components
                unit_compat = self._unit_compatibility(source_node, target_node)
                type_compat = self._type_compatibility(source_node, target_node)
                lexical_sim = self._lexical_similarity(source_node, target_node)
                semantic_sim = self._semantic_similarity_hybrid(source_node, target_node)
                
                # Calculate weighted overall score
                weights = {"unit": 0.25, "type": 0.25, "lexical": 0.20, "semantic": 0.30}
                overall_score = (
                    unit_compat * weights["unit"] +
                    type_compat * weights["type"] +
                    lexical_sim * weights["lexical"] +
                    semantic_sim * weights["semantic"]
                )
                
                overall_row.append(overall_score)
                unit_row.append(unit_compat)
                type_row.append(type_compat)
                lexical_row.append(lexical_sim)
                semantic_row.append(semantic_sim)
            
            overall_scores.append(overall_row)
            unit_scores.append(unit_row)
            type_scores.append(type_row)
            lexical_scores.append(lexical_row)
            semantic_scores.append(semantic_row)
        
        matrix_data = {
            "source_names": source_names,
            "target_names": target_names,
            "overall_scores": overall_scores,
            "unit_compatibility": unit_scores,
            "type_compatibility": type_scores,
            "lexical_similarity": lexical_scores,
            "semantic_similarity": semantic_scores
        }
        
        # Export to CSV if file path provided
        if output_file:
            self._export_detailed_matrix_to_csv(matrix_data, output_file)
        
        return matrix_data
    
    def _export_detailed_matrix_to_csv(self, matrix_data: Dict, filepath: str):
        """Export detailed similarity matrix with component scores to CSV."""
        source_names = matrix_data["source_names"]
        target_names = matrix_data["target_names"]
        overall_scores = matrix_data["overall_scores"]
        unit_scores = matrix_data["unit_compatibility"]
        type_scores = matrix_data["type_compatibility"]
        lexical_scores = matrix_data["lexical_similarity"]
        semantic_scores = matrix_data["semantic_similarity"]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header with target names
            header = ['Source Node'] + target_names
            writer.writerow(header)
            
            # Write overall scores section
            writer.writerow(['=== OVERALL CONFIDENCE SCORES ==='])
            for i, source_name in enumerate(source_names):
                row = [source_name] + [f"{score:.3f}" for score in overall_scores[i]]
                writer.writerow(row)
            
            writer.writerow([])  # Empty row separator
            
            # Write unit compatibility section
            writer.writerow(['=== UNIT COMPATIBILITY SCORES ==='])
            for i, source_name in enumerate(source_names):
                row = [source_name] + [f"{score:.3f}" for score in unit_scores[i]]
                writer.writerow(row)
            
            writer.writerow([])  # Empty row separator
            
            # Write type compatibility section
            writer.writerow(['=== TYPE COMPATIBILITY SCORES ==='])
            for i, source_name in enumerate(source_names):
                row = [source_name] + [f"{score:.3f}" for score in type_scores[i]]
                writer.writerow(row)
            
            writer.writerow([])  # Empty row separator
            
            # Write lexical similarity section
            writer.writerow(['=== LEXICAL SIMILARITY SCORES ==='])
            for i, source_name in enumerate(source_names):
                row = [source_name] + [f"{score:.3f}" for score in lexical_scores[i]]
                writer.writerow(row)
            
            writer.writerow([])  # Empty row separator
            
            # Write semantic similarity section
            writer.writerow(['=== SEMANTIC SIMILARITY SCORES ==='])
            for i, source_name in enumerate(source_names):
                row = [source_name] + [f"{score:.3f}" for score in semantic_scores[i]]
                writer.writerow(row)
        
        print(f"  [OK] Detailed similarity matrix exported to: {filepath}")
    
    def generate_html_similarity_matrix(self,
                                        source: SemanticNodeCollection,
                                        target: SemanticNodeCollection,
                                        output_file: str = None):
        """
        Generate an HTML similarity matrix with color coding.
        
        Creates an HTML table with:
        - Green highlighting for high scores (>0.6)
        - Yellow highlighting for medium scores (0.3-0.6)
        - White for low scores (<0.3)
        
        Args:
            source: Source semantic node collection
            target: Target semantic node collection
            output_file: HTML file path to save the matrix
        """
        print(f"\n  Generating HTML similarity matrix...")
        
        matrix_data = self.generate_detailed_similarity_matrix(source, target)
        
        source_names = matrix_data["source_names"]
        target_names = matrix_data["target_names"]
        overall_scores = matrix_data["overall_scores"]
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Semantic Similarity Matrix</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th {
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #ddd;
            position: sticky;
            top: 0;
        }
        th.source-header {
            background-color: #2196F3;
            text-align: left;
        }
        td {
            padding: 10px;
            text-align: center;
            border: 1px solid #ddd;
        }
        td.source-name {
            background-color: #e3f2fd;
            font-weight: bold;
            text-align: left;
        }
        .score-high {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .score-medium {
            background-color: #FFEB3B;
            color: #333;
        }
        .score-low {
            background-color: #ffffff;
            color: #666;
        }
        .legend {
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
        }
        .legend-item {
            display: inline-block;
            margin-right: 20px;
            padding: 5px 10px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>Semantic Similarity Matrix</h1>
    <div class="container">
        <div class="legend">
            <strong>Score Legend:</strong>
            <span class="legend-item score-high">High (≥0.6)</span>
            <span class="legend-item score-medium">Medium (0.3-0.6)</span>
            <span class="legend-item score-low">Low (&lt;0.3)</span>
        </div>
        <table>
            <thead>
                <tr>
                    <th class="source-header">Source Node</th>
"""
        
        # Add target names as column headers
        for target_name in target_names:
            html_content += f'                    <th>{target_name}</th>\n'
        
        html_content += "                </tr>\n            </thead>\n            <tbody>\n"
        
        # Add data rows
        for i, source_name in enumerate(source_names):
            html_content += "                <tr>\n"
            html_content += f'                    <td class="source-name">{source_name}</td>\n'
            
            for j, score in enumerate(overall_scores[i]):
                # Determine score class
                if score >= 0.6:
                    score_class = "score-high"
                elif score >= 0.3:
                    score_class = "score-medium"
                else:
                    score_class = "score-low"
                
                html_content += f'                    <td class="{score_class}">{score:.3f}</td>\n'
            
            html_content += "                </tr>\n"
        
        html_content += """            </tbody>
        </table>
    </div>
</body>
</html>
"""
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"  [OK] HTML similarity matrix exported to: {output_file}")
        
        return html_content


# Example usage
if __name__ == "__main__":
    from semantic_node_enhanced import SemanticNode, SemanticNodeCollection
    
    print("=== Semantic Mapping Module ===\n")
    
    # Create source collection (e.g., from IDTA file)
    source = SemanticNodeCollection()
    source.add_node(SemanticNode(
        name="ProcessTemperature",
        conceptual_definition="Operating temperature of the process",
        value=180.0,
        value_type="Float",
        unit="°C",
        source_file="idta_source.json"
    ))
    source.add_node(SemanticNode(
        name="SystemPressure",
        conceptual_definition="Pressure in the system",
        value=5.2,
        value_type="Float",
        unit="bar",
        source_file="idta_source.json"
    ))
    source.add_node(SemanticNode(
        name="ManufacturerName",
        value="ACME Corp",
        value_type="String",
        source_file="idta_source.json"
    ))
    
    # Create target collection (e.g., from OPC UA file)
    target = SemanticNodeCollection()
    target.add_node(SemanticNode(
        name="Temperature",
        conceptual_definition="Temperature measurement",
        value=0.0,
        value_type="Double",
        unit="°C",
        source_file="opcua_target.xml"
    ))
    target.add_node(SemanticNode(
        name="Pressure",
        conceptual_definition="Pressure value",
        value=0.0,
        value_type="Real",
        unit="bar",
        source_file="opcua_target.xml"
    ))
    target.add_node(SemanticNode(
        name="Manufacturer",
        value="",
        value_type="String",
        source_file="opcua_target.xml"
    ))
    target.add_node(SemanticNode(
        name="Speed",
        value=0.0,
        value_type="Float",
        unit="rpm",
        source_file="opcua_target.xml"
    ))
    
    # Create matcher and find matches
    matcher = SemanticMatcher()
    matches = matcher.match_collections(source, target)
    
    print(f"Found {len(matches)} matches:\n")
    for match in matches:
        print(f"  {match.source_node.name} → {match.target_node.name}")
        print(f"    Type: {match.match_type.value}")
        print(f"    Confidence: {match.confidence.value}")
        print(f"    Score: {match.score:.2f}")
        print()
    
    print("\nStatistics:")
    stats = matcher.get_statistics()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\nUnmatched source nodes: {len(matcher.unmatched_source)}")
    for node in matcher.unmatched_source:
        print(f"  - {node.name}")
    
    print(f"\nUnmatched target nodes: {len(matcher.unmatched_target)}")
    for node in matcher.unmatched_target:
        print(f"  - {node.name}")
    
    # Export matches
    matcher.export_matches("semantic_matches.json")

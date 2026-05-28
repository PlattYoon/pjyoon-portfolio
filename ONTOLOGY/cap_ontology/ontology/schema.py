"""
ontology/schema.py

Defines the fine-grained entity and relation types for Climate Action Plans.
All annotation must conform to these types.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Entity Types
# ---------------------------------------------------------------------------

class EntityType(str, Enum):
    EMISSIONS_TARGET   = "EmissionsTarget"    # e.g. "net-zero by 2050"
    ADAPTATION_MEASURE = "AdaptationMeasure"  # e.g. "coastal flood barriers"
    JURISDICTION       = "Jurisdiction"       # e.g. "City of Pittsburgh"
    SECTOR             = "Sector"             # e.g. "transportation", "buildings"
    DEADLINE           = "Deadline"           # e.g. "by 2030", "within 5 years"
    STAKEHOLDER        = "Stakeholder"        # e.g. "EPA", "local businesses"
    BASELINE_YEAR      = "BaselineYear"       # reference year for targets
    METRIC             = "Metric"             # e.g. "CO2e", "MtCO2", "%"
    FUNDING_SOURCE     = "FundingSource"      # e.g. "federal grant", "carbon tax"
    POLICY_INSTRUMENT  = "PolicyInstrument"   # e.g. "building code", "zoning law"


class RelationType(str, Enum):
    TARGETS       = "targets"        # Jurisdiction --targets--> EmissionsTarget
    IMPLEMENTS    = "implements"     # Jurisdiction --implements--> AdaptationMeasure
    GOVERNS       = "governs"        # PolicyInstrument --governs--> Sector
    REPORTS_TO    = "reports_to"     # Stakeholder --reports_to--> Jurisdiction
    SUPERSEDES    = "supersedes"     # CAP --supersedes--> older CAP
    FUNDED_BY     = "funded_by"      # Measure --funded_by--> FundingSource
    HAS_DEADLINE  = "has_deadline"   # Target --has_deadline--> Deadline
    MEASURED_IN   = "measured_in"    # EmissionsTarget --measured_in--> Metric
    APPLIES_TO    = "applies_to"     # Measure --applies_to--> Sector


# ---------------------------------------------------------------------------
# Data classes for annotation objects
# ---------------------------------------------------------------------------

@dataclass
class Span:
    """A contiguous text span within a document."""
    start: int            # character offset
    end: int              # character offset (exclusive)
    text: str
    entity_type: EntityType
    span_id: str          # unique within document, e.g. "s0"
    confidence: float = 1.0
    annotator: str = "human"
    notes: Optional[str] = None

    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError(f"Span start ({self.start}) must be < end ({self.end})")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be in [0, 1]")


@dataclass
class Relation:
    """A directed relation between two Spans."""
    head_id: str          # span_id of head entity
    tail_id: str          # span_id of tail entity
    relation_type: RelationType
    relation_id: str      # unique within document, e.g. "r0"
    confidence: float = 1.0
    annotator: str = "human"
    notes: Optional[str] = None


@dataclass
class AnnotatedDocument:
    """A fully annotated CAP document."""
    doc_id: str
    source_path: str
    jurisdiction: str
    year: Optional[int]
    text: str
    spans: list[Span] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def get_span(self, span_id: str) -> Optional[Span]:
        return next((s for s in self.spans if s.span_id == span_id), None)

    def spans_by_type(self, entity_type: EntityType) -> list[Span]:
        return [s for s in self.spans if s.entity_type == entity_type]

    def relations_for_span(self, span_id: str) -> list[Relation]:
        return [r for r in self.relations
                if r.head_id == span_id or r.tail_id == span_id]


# ---------------------------------------------------------------------------
# Valid head/tail pairs per relation (schema constraint)
# ---------------------------------------------------------------------------

VALID_RELATION_ARGS: dict[RelationType, tuple[set[EntityType], set[EntityType]]] = {
    RelationType.TARGETS:      ({EntityType.JURISDICTION},          {EntityType.EMISSIONS_TARGET}),
    RelationType.IMPLEMENTS:   ({EntityType.JURISDICTION},          {EntityType.ADAPTATION_MEASURE}),
    RelationType.GOVERNS:      ({EntityType.POLICY_INSTRUMENT},     {EntityType.SECTOR}),
    RelationType.REPORTS_TO:   ({EntityType.STAKEHOLDER},           {EntityType.JURISDICTION}),
    RelationType.SUPERSEDES:   ({EntityType.JURISDICTION},          {EntityType.JURISDICTION}),
    RelationType.FUNDED_BY:    ({EntityType.ADAPTATION_MEASURE,
                                  EntityType.POLICY_INSTRUMENT},    {EntityType.FUNDING_SOURCE}),
    RelationType.HAS_DEADLINE: ({EntityType.EMISSIONS_TARGET,
                                  EntityType.ADAPTATION_MEASURE},   {EntityType.DEADLINE}),
    RelationType.MEASURED_IN:  ({EntityType.EMISSIONS_TARGET},      {EntityType.METRIC}),
    RelationType.APPLIES_TO:   ({EntityType.ADAPTATION_MEASURE,
                                  EntityType.POLICY_INSTRUMENT},    {EntityType.SECTOR}),
}


def validate_relation(relation: Relation, spans: list[Span]) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errors = []
    span_map = {s.span_id: s for s in spans}

    head = span_map.get(relation.head_id)
    tail = span_map.get(relation.tail_id)

    if head is None:
        errors.append(f"Unknown head span_id: {relation.head_id}")
    if tail is None:
        errors.append(f"Unknown tail span_id: {relation.tail_id}")

    if head and tail and relation.relation_type in VALID_RELATION_ARGS:
        valid_heads, valid_tails = VALID_RELATION_ARGS[relation.relation_type]
        if head.entity_type not in valid_heads:
            errors.append(
                f"Relation {relation.relation_type} expects head in "
                f"{valid_heads}, got {head.entity_type}"
            )
        if tail.entity_type not in valid_tails:
            errors.append(
                f"Relation {relation.relation_type} expects tail in "
                f"{valid_tails}, got {tail.entity_type}"
            )
    return errors

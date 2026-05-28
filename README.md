{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AnnotatedDocument",
  "description": "Schema for a single annotated Climate Action Plan document (one record per JSONL line).",
  "type": "object",
  "required": ["doc_id", "source_path", "jurisdiction", "text", "spans", "relations"],
  "additionalProperties": false,
  "properties": {
    "doc_id":       { "type": "string" },
    "source_path":  { "type": "string" },
    "jurisdiction": { "type": "string" },
    "year":         { "type": ["integer", "null"], "minimum": 1990, "maximum": 2100 },
    "text":         { "type": "string", "minLength": 1 },
    "metadata":     { "type": "object" },
    "spans": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["span_id", "start", "end", "text", "entity_type"],
        "additionalProperties": false,
        "properties": {
          "span_id":     { "type": "string" },
          "start":       { "type": "integer", "minimum": 0 },
          "end":         { "type": "integer", "minimum": 1 },
          "text":        { "type": "string" },
          "entity_type": {
            "type": "string",
            "enum": [
              "EmissionsTarget", "AdaptationMeasure", "Jurisdiction",
              "Sector", "Deadline", "Stakeholder", "BaselineYear",
              "Metric", "FundingSource", "PolicyInstrument"
            ]
          },
          "confidence":  { "type": "number", "minimum": 0.0, "maximum": 1.0 },
          "annotator":   { "type": "string" },
          "notes":       { "type": ["string", "null"] }
        }
      }
    },
    "relations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["relation_id", "head_id", "tail_id", "relation_type"],
        "additionalProperties": false,
        "properties": {
          "relation_id":   { "type": "string" },
          "head_id":       { "type": "string" },
          "tail_id":       { "type": "string" },
          "relation_type": {
            "type": "string",
            "enum": [
              "targets", "implements", "governs", "reports_to",
              "supersedes", "funded_by", "has_deadline", "measured_in", "applies_to"
            ]
          },
          "confidence":  { "type": "number", "minimum": 0.0, "maximum": 1.0 },
          "annotator":   { "type": "string" },
          "notes":       { "type": ["string", "null"] }
        }
      }
    }
  }
}

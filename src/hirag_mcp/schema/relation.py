from dataclasses import dataclass

from hirag_mcp.schema import Entity


@dataclass
class Relation:
    source: Entity
    target: Entity
    properties: dict

from typing import NamedTuple


PolicyInput = dict

class GovernanceEvent(NamedTuple):
    kind: str
    descriptor: dict
from collections import defaultdict
from rai_digital_twin.models.digital_twin_v1.model.parts.debt_market import s_update_interest_bitten
from typing import NamedTuple, Dict, TypedDict
from rai_digital_twin.units import *

# cadCAD objects
Parameters = Dict[str, object]
State = Dict[str, object]
PolicyInput = Dict[str, object]


class GovernanceEvent(NamedTuple):
    kind: str
    descriptor: dict


class UserAction(TypedDict):
    add_ETH_collateral: ETH
    add_RAI_debt: RAI
    add_RAI_reserve: RAI
    add_ETH_reserve: ETH

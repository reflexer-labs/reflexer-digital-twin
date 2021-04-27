"""

"""
from rai_digital_twin.types import GovernanceEvent, PolicyInput


def decode_event(event: GovernanceEvent) -> PolicyInput:
    """
    Transforms Governance Events into Actionable Policy Inputs.
    """
    action = {}

    if event.kind == 'Kp_change':
        action = event.descriptor['new_value']
    else:
        pass

    return action

def p_governance_events(params, _1, _2, state):
    """
    Policy to decode governance events.
    """
    events = params['governance_events']
    t = state['timestep']

    action = {}
    if t in events:
        event = events[t]
        action = decode_event(event)
    else:
        pass

    return action


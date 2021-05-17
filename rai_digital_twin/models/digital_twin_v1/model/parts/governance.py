"""

"""
from rai_digital_twin.types import ControllerParams, GovernanceEvent, GovernanceEventKind
from cadCAD_tools.types import Signal


def decode_event(event: GovernanceEvent) -> Signal:
    """
    Transforms Governance Events into Actionable Policy Inputs.
    """
    action: dict = {}

    if event.kind == GovernanceEventKind.change_pid_params:
        action['pid_params'] = event.descriptor
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


def s_pid_params(_1, _2, _3, state, signal):
    if 'pid_params' in signal:
        new_pid_params = ControllerParams(**signal['pid_params'])
    else:
        new_pid_params = state['pid_params']
    return ('pid_params', new_pid_params)
from pytest import approx

from rai_digital_twin.models.digital_twin_v1.model.parts.governance import *


def test_decoder():

    event = GovernanceEvent('', None)
    action = decode_event(event)
    assert action == {}

    event_desc = {}
    event = GovernanceEvent(GovernanceEventKind.change_pid_params,
                            event_desc)
    action = decode_event(event)
    assert action == {'pid_params': event_desc}

    event_desc = {'kp': 0,
                  'ki': 1,
                  'leaky_factor': 2,
                  'period': 4,
                  'enabled': 5}
    event = GovernanceEvent(GovernanceEventKind.change_pid_params,
                            event_desc)
    action = decode_event(event)
    assert action == {'pid_params': event_desc}


def test_governance_events():
    event_desc = {'kp': 0,
                  'ki': 1,
                  'leaky_factor': 2,
                  'period': 4,
                  'enabled': 5}
    event = GovernanceEvent(GovernanceEventKind.change_pid_params,
                            event_desc)
    governance_events = {0: event}
    params = {'governance_events': governance_events}
    state = {'timestep': 0}

    signal = p_governance_events(params, None, None, state)
    assert signal == {'pid_params': event_desc}

    update = s_pid_params(None, None, None, state, signal)
    assert update == ('pid_params', ControllerParams(**event_desc))

    state.update(timestep=1,
                 pid_params=ControllerParams(**event_desc))
    signal = p_governance_events(params, None, None, state)
    assert signal == {}

    update = s_pid_params(None, None, None, state, signal)
    assert update == ('pid_params', state['pid_params'])

import numpy as np
import pandas as pd
import math
import logging
import time


def s_update_sim_metrics(params, substep, state_history, state, policy_input):
    previous_timestep_time = state['sim_metrics'].get('timestep_time', 0)
    sim_metrics = {
        'timestep_time': time.time() - previous_timestep_time
    }
    return 'sim_metrics', sim_metrics

def save_partial_results(params, substep, state_history, state):
    partial_results: pd.DataFrame = pd.read_pickle(params['partial_results'])
    partial_results = partial_results.append(state, ignore_index=True)
    partial_results.to_pickle(params['partial_results'])
    return {}

def p_free_memory(params, substep, state_history, state):
    if state['timestep'] > 0:
        for key in params['free_memory_states']:
            try:
                # Clear states older than 2nd last
                substates = state_history[-2]
                for substate in substates:
                    substate[key] = None
            except IndexError as e:
                print(e)
                continue
    return {}

def s_collect_events(params, substep, state_history, state, policy_input):
    return 'events', state['events'] + policy_input.get('events', [])

def approx_greater_equal_zero(value, rel_tol=0.0, abs_tol=1e-10):
    return value >= 0 or math.isclose(value, 0, rel_tol=rel_tol, abs_tol=abs_tol)

def approx_eq(v1, v2, rel_tol=0.0, abs_tol=1e-10):
    return math.isclose(v1, v2, rel_tol=rel_tol, abs_tol=abs_tol)

def assert_log(condition, message="", _raise=True):
    try:
        assert condition, message
    except AssertionError as e:
        logging.warning(e)
        if _raise: raise e

    return condition

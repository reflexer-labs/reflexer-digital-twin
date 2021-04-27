import numpy as np
import pandas as pd
import math
import logging
import time
from functools import wraps
import rai_digital_twin.failure_modes as failure


def print_time(f):
    """
    Decorator for printing the execution time and the output from it.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Current timestep
        t1 = time.time()
        f_out = f(*args, **kwargs)
        t2 = time.time()
        text = f"{f.__name__} output (exec time: {(t2 - t1) * 1000 :.6f} ms)"
        print(text)
        return f_out
    return wrapper


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
        logging.warning(f"{e}: {message}")
        if _raise: raise failure.AssertionError(f"{e}: {message}")

    return condition

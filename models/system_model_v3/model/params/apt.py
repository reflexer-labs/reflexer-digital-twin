import pickle


# The full feature vector available for the APT model
features = ['beta', 'Q', 'v_1', 'v_2 + v_3', 
                    'D_1', 'u_1', 'u_2', 'u_3', 'u_2 + u_3', 
                    'D_2', 'w_1', 'w_2', 'w_3', 'w_2 + w_3',
                    'D']

# The feature vector subset used for the APT ML model
features_ml = ['beta', 'Q', 'v_1', 'v_2 + v_3', 'u_1', 'u_2', 'u_3', 'w_1', 'w_2', 'w_3', 'D']

# The unobservable events, or optimal values, returned from the root-finding algorithm
optvars = ['u_1', 'u_2', 'v_1', 'v_2 + v_3']

# Load the APT model from a Pickle file, and configure the root-finding algorithm to be optimized using Scipy's `minimize` function and Powell's method.

# NB: Pickle files must be downloaded seperately and copied into `models/pickes/` directory
model = pickle.load(open('models/pickles/apt_debt_model_2020-11-28.pickle', 'rb'))

ml_data_list = []
global tol
tol = 1e-2
global curr_error, best_error, best_val
global strikes
strikes = 0
best_error = 1e10

def glf_continue_callback(xopt):
    print('entered callback')
    global curr_error, best_error, best_val, strikes, tol
    if curr_error > tol: # keep searching
        print('bigger than tol, keep searching')
        return False
    else:
        if curr_error > best_error: # add strike
            strikes += 1
            if strikes < 3: # continue trying
                print('bigger than prev best, add strike')
                return False
            else: # move on, not working
                strikes = 0
                print('3rd strike, stop')
                return True
        else: # better outcome, continue
            best_error = curr_error
            best_val = xopt
            strikes = 0
            print('New best, reset strikes')
            return False

# Global minimizer function
def glf(x, to_opt, data, constant, timestep):
    global curr_error
    for i,y in enumerate(x):
        data[:,to_opt[i]] = y
    err = model.predict(data)[0] - constant
    curr_error = abs(err)

    return curr_error

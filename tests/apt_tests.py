apt_tests = [
        # {
        #     'enable': False,
        #     'params': {
        #         'optimal_values': {
        #             'v_1': lambda timestep=0, df=simulation_results_df: \
        #                 simulation_results_df.iloc[timestep]['optimal_values'].get('v_1', historical_initial_state['v_1']),
        #             'v_2 + v_3': lambda timestep=0, df=simulation_results_df: \
        #                 simulation_results_df.iloc[timestep]['optimal_values'].get('v_2 + v_3', historical_initial_state['v_2 + v_3']),
        #             'u_1': lambda timestep=0, df=simulation_results_df: \
        #                 simulation_results_df.iloc[timestep]['optimal_values'].get('u_1', historical_initial_state['u_1']),
        #             'u_2': lambda timestep=0, df=simulation_results_df: \
        #                 simulation_results_df.iloc[timestep]['optimal_values'].get('u_2', historical_initial_state['u_2'])
        #         }
        #     }
        # },
        # {
        #     'enable': False,
        #     'params': {
        #         'optimal_values': {
        #             'v_1': lambda timestep=0: historical_initial_state['v_1'],
        #             'v_2 + v_3': lambda timestep=0: historical_initial_state['v_2 + v_3'],
        #             'u_1': lambda timestep=0: historical_initial_state['u_1'],
        #             'u_2': lambda timestep=0: historical_initial_state['u_2']
        #         }
        #     }
        # },
        {
            'enable': True,
            'params': {
                'optimal_values': {
                    'v_1': lambda timestep=0: 1000,
                    'v_2 + v_3': lambda timestep=0: 500,
                    'u_1': lambda timestep=0: 100,
                    'u_2': lambda timestep=0: 50
                }
            }
        },
        # {
        #     'enable': False,
        #     'params': {
        #         'optimal_values': {
        #             'v_1': lambda timestep=0: 500,
        #             'v_2 + v_3': lambda timestep=0: 1000,
        #             'u_1': lambda timestep=0: 50,
        #             'u_2': lambda timestep=0: 100
        #         }
        #     }
        # }
]

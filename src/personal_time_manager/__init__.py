'''
runs the listener logic and runs backtracking search.
'''
from personal_time_manager.csp import create_csp

def main():
    '''
    Finally, The Main Routine ;)
    '''
    #TODO: implement the DB listener logic
    #TODO: think how to take trigger from google calendar api if calendar events change?

    csp = create_csp()
    # Step 4: Execute DP Algorithm to find solution ;D
    solution: Optional[dict[str, int]] = csp.backtracking_search()
    if solution is None:
        #TODO: what do I do if no timetable possible?!?
        print("No solution found!")
        raise ValueError("CSP no solution found!")

    else:  # will print proper in the test_visualize
        return solution



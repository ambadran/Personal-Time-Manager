'''
**Constraint Satisfactory Problem Framework**
(As defined in my favourite programming book: Classic Computer Science Problems in Python by David Kopec)

* INPUTS *
CSP Variable Type: `Session`
CSP Domain Type: `list[datetime]`
CSP Constraint class(es): `NoTimeOverlapConstraint`

CSP Variable Type: `Session`
    - Describes what a time slot (session) hold in terms of the activity being done including the duration needed
    - The Session class is designed to accomodate any type of activity (like google calendar-defined meeting, tuitions, prayers, etc..)

CSP Domain Type: `list[datetime]`
    - list of all the MINUTES(in the form of datetime) that a specific session can start in.
    - *NOT INCLUDING the time that the session can theoritically start in but not be finished if started then
    - datetime was choosen as it is a standard Python represetation of absolute times
    - also the datetime has a very useful timedelta type that is used to represetation the duration in the Session

CSP Constraint class(es): `NoTimeOverlapConstraint`
    - While the nature of the CSP framework covers the fact that all session can only be done within a defined period of time (domain)
    - Another custom designed Constraint is needed to achieve the Perfect TimeTable
    - Must define how some sessions can't overlap with anything, some can overlap and break a session in half(or more).

The CSP Framework inputs all CSP Variables and domain for a Week (Starts Saturday, Ends Friday)

* OUTPUTS *

CSP Assignment Type: `dict[Session: datetime]`
    - Contains ALL `Session` variables in a week as keys
    - Contains assigned exact `datetime` for each `Session`
    - The PERFECT Timetable! :D
'''
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from personal_time_manager.sessions.base_session import Session

class Constraint(ABC):
    '''
    Abstract Class for All custom Constraint class
    '''
    def __init__(self, variables: list[Session]):
        self.variables = variables
        
    # abstractmethod decorator makes sure the two rules of abstract base classes are met
    # it will raise a well documented TypeError on what rule of the two is broken if 
    @abstractmethod
    def satisfied(self, assignment: dict[Session: datetime]) -> bool:
        """
        :param assignment: dict of variables keys and possible value from the domains dict for the dict value
        :return boolean: True if this particular constraint object is satisfied on the variables this object affect(in the variables attrib)
                        according to the value assignment in the passed assignments argument
        """
        pass


class CSP:
    '''
    Constraint Satisfactory Problem 

    CSP Variable Type: `Session`
    CSP Domain Type: `list[datetime]`
    '''
    def __init__(self, variables: list[Session], domains: dict[Session: list[datetime]]):

        self.variables = variables # varaibles that need to be assignment with all constraint satisfied domain value
        self.domains = domains # possible values for each variable
        self.constraints = {} # list of constraints imposed on each variable

        # creating the constraints Dict
        for variable in self.variables:
            self.constraints[variable] = [] # assigning the supposed list of constraints to each varaible

            # as we are looping varaibles, checking that all variables are in the domain dict by the way
            if variable not in self.domains:
                raise LookupError(f"Every variable must have a domain list assigned to it in the domain dict\n{variable} is not in domains")


    def add_constraint(self, constraint: Constraint):
        """
        :param constraint: constraint object from the custom defined constraint class

        Imposes the constraint on all variables by adding the constraint object to the value of the constraints dict of each variable
        """
        for variable in constraint.variables:
            # Checking if variable is in constraint and csp.variables
            if variable not in self.variables:
                raise LookupError("constraint affect a variable that is not found in the csp.variables list")

            else:
                self.constraints[variable].append(constraint) # adding the constraint

    def consistent(self, variable: Session, assignment: dict[Session: datetime]):
        """
        :param assignment: dict of variables keys and possible value from the domains dict for the dict value
        :return boolean: checks that ALL constraints in a variable's constraint list(in constraints dict) is satisfied
                        according to the value assigned to the variable in the passed assignment dict argument in this function
        """
        for constraint in self.constraints[variable]: # looping each constraint object
            if not constraint.satisfied(assignment):
                return False

        return True # after looping all constraints in the variable and making sure it is all saitisfied according to the value in the assingment dict


    def backtracking_search(self, assignment = {}):
        # assignment is complete if every variable is assigned (our base case)
        if len(assignment) == len(self.variables):
            return assignment

        # get all variables in the CSP but not in the assignment
        unassigned: List[V] = [v for v in self.variables if v not in assignment]

        # get the every possible domain value of the first unassigned variable
        first: V = unassigned[0]
        for value in self.domains[first]:
            local_assignment = assignment.copy()
            local_assignment[first] = value
            # if we're still consistent, we recurse (continue)
            if self.consistent(first, local_assignment):
                result: Optional[Dict[V, D]] = self.backtracking_search(local_assignment)
                # if we didn't find the result, we will end up backtracking
                if result is not None:
                    return result
        return None


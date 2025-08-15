'''

'''
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from personal_time_manager.sessions.base_session import Session

# Abstract base class
# This is a parent class meant a blue print to be inherited by other classes
# it makes sure that rule 1 of abstract base classes is met
# Subclasses inherited from a specific base class must implement all the methods and properties defined in the abstract base class.
# While Rule two is
# Abstract base classes cannot be instantiated. They are inherited by the other subclasses.
class Constraint(ABC):
    
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














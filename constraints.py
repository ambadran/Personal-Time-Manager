from csp import Constraint, CSP
from sessions import Prayers, Tuitions, Personal

class NoTimeOverlapConstraint(Constraint):
    '''
    Constraint class to prevent time slots from overlapping
    '''
    def __init__(self, variables: list):
        super().__init__(variables)

    def satisfied(self, assignment) -> bool:
        '''
        actual testing for overlap
        '''
        pass

class TimeNeededConstraint(Constraint):
    '''
    Constraint to make sure timeslot took it's needed time
    '''
    def __init__(self, variable, time_needed: int):
        super().__init__([variable])
        self.time_needed = time_needed
        
    def satisfied(self, assignments) -> bool:
        '''
        test if variable has enough time assigned to it
        '''
        pass

if __name__ == "__main__":

    sessions: list = []
    domains: dict[str: list[int]] = {}

    # the sessions needed to be fulfilled
    prayers = ["dhur_saturday", "asr_saturday", "maghrib_saturday", "isha_saturday", "dhur_sunday", "asr_sunday", "maghrib_sunday", "isha_sunday"]
    work_meetings = ["weekly_plan_saturday_meeting"]
    lessons = ["abdullah_math1", "abdullah_math2", "omran_mila_math"]
    personal_things = ["lunch_prepare", "lunch_time"]
    others = []
    sessions.extend(prayers) # Prayers
    sessions.extend(work_meetings) # Main Job / freelance meetings
    sessions.extend(lessons) # lessons
    sessions.extend(personal) # personal
    sessions.extend(others)

    # Applying correct domain for each session
    #TODO: apply the correct time for each prayer
    domains.update(prayer.get_variable_domain_dict())
    for session in work_meetings:

        pass #TODO: apply correct time for work meetings

    for session in lessons:
        pass #TODO: apply the possible times for each student

    for session in personal:
        pass #TODO: put appropriate time for each personal activity

    for session in others:
        pass #TODO

    # Creating CSP framework
    csp: CSP = CSP(sessions, domains)

    # Applying constraints
    csp.add_constraint(NoTimeOverlapConstraint(sessions)) # no overlap constraint
    for session in prayers:
        pass #TODO: i think it's not needed because prayer time is very exact anyway no options
    for session in work_meetings:
        pass #TODO:
    for session in lessons:
        pass #TODO: assign the appropriate time for each lesson
    for session in personal:
        pass #TODO: assign the appropriate time for each personal item
    for session in others:
        pass #TODO

    # Find solution
    solution: Optional[dict[str, int]] = csp.backtracking_search()
    if solution is None:
        print("No solution found!")
    else:
        print(solution)








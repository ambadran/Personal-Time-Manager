
db_mock =  [
    RealDictRow(
        {'id': 'a09a5e7d-aa13-451b-8086-9e35c0ac0fb0', 
         'email': 'admin', 
         'is_first_sign_in': False, 
         'students': [
             {'id': 'e1d3498f-cca5-48dc-a977-e50e876668c8', 
              'subjects': [{'name': 'Math', 'lessonsPerWeek': 2}, 
                           {'name': 'Physics', 'lessonsPerWeek': 1}, 
                           {'name': 'Chemistry', 'lessonsPerWeek': 1}], 
              'basicInfo': {'grade': '8', 'lastName': 'Doe', 'firstName': 'John'},
              'availability': {'friday': [], 
                               'monday': [
                                   {'end': '15:00', 'type': 'school', 'start': '06:00'}
                                   ], 
                               'sunday': [
                                   {'end': '15:00', 'type': 'school', 'start': '06:00'},
                                   {'end': '21:30', 'type': 'sports', 'start': '19:30'}
                                   ],
                               'tuesday': [
                                   {'end': '15:00', 'type': 'school', 'start': '06:00'},
                                   {'end': '21:30', 'type': 'sports', 'start': '19:30'}], 'saturday': [], 'thursday': [{'end': '15:00', 'type': 'school', 'start': '06:00'}, {'end': '16:00', 'type': 'others', 'start': '15:00'}, {'end': '22:15', 'type': 'sports', 'start': '20:15'}], 'wednesday': [{'end': '15:00', 'type': 'school', 'start': '06:00'}]}}]})]

import numpy as np 
import pandas as pd 
import copy
import constants
from locations import Route, Student

TRAVEL_TIMES = constants.TRAVEL_TIMES
PHONEBOOK = constants.PHONEBOOK
GEOCODES = constants.GEOCODES
SCHOOLS_CODES_MAP = constants.SCHOOLS_CODES_MAP
CODES_INDS_MAP = constants.CODES_INDS_MAP
STOPS_CODES_MAP = constants.STOPS_CODES_MAP

# Californication
def californiafy(address):
    return address[:-6] + " California," + address[-6:]

# Convert routes to common
def convert_to_common(route):
    list_of_stops = list()
    list_of_visited_schools = [sch[0] for sch in route.school_path]
    for stop in route.stops_path:
        schools_at_stop = set()
        for stud in route.students_list:
            if stud.tt_ind == stop[0]:
                schools_at_stop.update((stud.school_ind, stud.age_type))
                print(schools_at_stop)
        
        print("NEW: " + str(schools_at_stop))
        stops_info = (stop[0], schools_at_stop)
        print("STOPS_INFO: " + str(stops_info))
        list_of_stops.append(stops_info)
    route_output = (list_of_stops, list_of_visited_schools, route.bus_size)    

    return route_output
    

# A route plan is stored as a list of routes.
# A route is stored as a 3-tuple (list of stops, list of tt_inds for visited schools, bus capacity)
# A stop is stored as a 2-tuple (tt_ind, set of 2-tuples (school, age_type))
# Convert routes from common 
def convert_from_common(route):
    
    list_of_students = list()
    schools_path = route[1]
    schools_set = set([school[0] for school in schools_path])
    
    stops_path = [(stop[0], round(TRAVEL_TIMES[schools_path[-1][0]][stop[0]],2)) if idx == 0 else (stop[0], round(TRAVEL_TIMES[route[0][idx-1][0]][stop[0]],2)) for idx, stop in enumerate(route[0])]

    subset_phonebook = PHONEBOOK[PHONEBOOK['tt_ind'].isin([schools[0] for schools in schools_path])]
    
    stops_lat_long = [(GEOCODES.iloc[stops[0]]['Lat'], GEOCODES.iloc[stops[0]]['Long']) for stops in stops_path]
    subset_phonebook = subset_phonebook[subset_phonebook['Lat'].isin([lat_long[0] for lat_long in stops_lat_long])]
    subset_phonebook = subset_phonebook[subset_phonebook['Long'].isin([lat_long[1] for lat_long in stops_lat_long])]
    
    for _, stud in subset_phonebook.iterrows():
        if stud.tt_ind in schools_set:
            stop_ind = CODES_INDS_MAP[STOPS_CODES_MAP[californiafy(stud.AM_Stop_Address)]]
            list_of_students.append(Student(stop_ind, stud.tt_ind))
                                            
    new_route = Route(schools_path, stops_path, None)
    new_route.add_students_manual(list_of_students)
    new_route.assign_bus_manual(route[2])
    
    return new_route




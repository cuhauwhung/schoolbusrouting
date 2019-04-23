import constants
import itertools
import numpy as np

#Used to get the data into a full address format        
def californiafy(address):
    return address[:-6] + " California," + address[-6:]

#Bit of a hack to compute seconds since midnight
def timesecs(time_string):
    pieces = time_string.split(':')
    if len(pieces) < 2:
        return 100000
    minutes = int(pieces[1][:2])  #minutes
    minutes += 60*int(pieces[0])  #hours
    if 'p' in pieces[1].lower():  #PM
        minutes += 12*60
    return minutes*60

def stud_trav_time_array(route_plan):
    stud_trav_times = [r.student_travel_times() for r in route_plan]
    #Flatten this list and convert to an np array
    stud_trav_times = np.array(list(itertools.chain(*stud_trav_times)))
    return stud_trav_times

#Determines a closest pair of locations in from_iter and to_iter
#from_iter and to_iter should both be iterables of Students and/or Schools
#optionally, can require a specific age type if to_iter has Students
def closest_pair(from_iter, to_iter, age_type = None):
    opt_dist = 100000
    opt_from_loc = None
    opt_to_loc = None
    for from_loc in from_iter:
        for to_loc in to_iter:
            if (constants.TRAVEL_TIMES[from_loc.tt_ind,
                                       to_loc.tt_ind] < opt_dist and
                (age_type == None or to_loc.type == age_type)):
                opt_dist = constants.TRAVEL_TIMES[from_loc.tt_ind,
                                                  to_loc.tt_ind]
                opt_from_loc = from_loc
                opt_to_loc = to_loc
    return opt_from_loc, opt_to_loc

def closest_addition(locations, betw_iter, available_time, alpha, age_type = None):
    opt_cost = 100000
    opt_dist = 100000
    opt_loc = None
    opt_ind = -1
    for i in range(len(locations) - 1):
        for loc in betw_iter:
            if ((constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind])/
                (constants.TRAVEL_TIMES[loc.tt_ind, loc.school.tt_ind]**alpha) < opt_cost and
                constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind] < available_time and
                (age_type == None or loc.type == age_type)):
            #if (constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
            #    constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
            #    constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind] < opt_dist and
            #    (age_type == None or loc.type == age_type)):
                opt_cost = ((constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                            constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                           constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind])/
                            (constants.TRAVEL_TIMES[loc.tt_ind, loc.school.tt_ind]**alpha))
                opt_dist = (constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                            constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                            constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind])
                opt_loc = loc
                opt_ind = i
                if opt_dist == 0:
                    break
        if opt_dist == 0:
            break
    return (opt_loc, opt_ind, opt_dist)

#Checks if two stop objects are isomorphic, even if they are
#not the same object in memory.
def isomorphic(stop1, stop2):
    return(stop1.type == stop2.type and
           stop1.school.name == stop2.school.name and
           stop1.tt_ind == stop2.tt_ind)

#Checks to see which routes in the first route plan share at least
#one stop with the passed-in route.
#Does not require pointer equality for stops, only object value
#equality.
def overlapping_routes(route_plan, route):
    out = set()
    for compare_route in route_plan:
        for stop1 in compare_route.stops:
            for stop2 in route.stops:
                if isomorphic(stop1, stop2):
                    out.add(compare_route)
    return out
        
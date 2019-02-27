import numpy as np 
from collections import Counter
prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
travel_times = np.load(prefix + "travel_times.npy")

cap_counts = [[16, 70], [17, 19], [24, 337], [33, 55], [34, 100], [41, 111], [62, 40], [65, 367], [71, 6], [84, 182]]

# TEST CASES
school_route = [9507]
stud_route = [7492, 8324]
max_time = 1800
current_time = 0

school_route = [10754]
stud_route = [612, 5230, 5551, 9312, 8455, 5383, 659]
max_time = 1800
current_time = 0

school_route = [10664, 10678]
stud_route = [443, 517, 535, 6782, 589, 4259, 5738]
max_time = 1000
current_time = 300

school_route = [10361, 9587] 
stud_route = [7860, 5284, 1986, 8324, 3853, 3578, 8125, 525, 168, 1428, 4471]
max_time = 1800 
current_time = [232.8]

school_route = [10417]
stud_route = [1962, 8479, 9211, 6253]
current_time = []

students = schoolcluster_students_map[34][0]



# Make route objects with route information in them
# Divide routes based on constraints 
def makeRoutes(school_route_time, school_route, stud_route, students):
    
    time = sum(school_route_time)
    path_info_list = list()
    path_info = list()
    base = school_route[-1]
        
    students.sort(key=lambda x: x.tt_ind, reverse=False)
    stop_counts =[stud.tt_ind for stud in students]
    stop_counts = dict(Counter(stop_counts))
        
    # Go through every stop and check if they meet the max_time or bus constraints
    # Create new route (starting from the schools) if the constraints are not met 
    for index, stop in enumerate(stud_route):
        path_info.append((travel_times[base][stop], stop_counts[stop]))
        
        # If the travel time or the bus capacity doesn't work, then break the routes
        if (time + sum([i for i, j in path_info]) > max_time) or (sum([j for i, j in path_info]) > cap_counts[-1][0]):
            base = school_route[-1]
            if len(path_info) == 1:
                path_info_list.append(path_info)
                path_info = list()
                
            else:
                path_info_list.append(path_info[:-1])
                path_info = list()
                path_info.append((travel_times[base][stop], stop_counts[stop]))
        base = stop
    
    # Add the 'leftover' routes back in to the list
    if path_info:
        path_info_list.append(path_info)

    # Deal with routes that have one stop, which exceed bus capacities
    

    # Get the list of routes from the stop_info_list
    result_list = list()
    ind = 0 
    for group in path_info_list:
        group_list = list()
        for stop in group:
            group_list.append(stud_route[ind])
            ind += 1
        result_list.append(school_route + group_list)
    
    # Add information about the routes between schools 
    # Prepend travel times from school -> school into the stop_info
    for info in path_info_list:
        for school_time in school_route_time:
            info.insert(0, (school_time, 0))

    # Make the route objects and put them into a list 
    route_list = list()
    for idx, route in enumerate(result_list):
        current_route = Route(route, path_info_list[idx])
        
        for stop in current_route.path:
            for idx, stud in enumerate(students):
                if stud.tt_ind == stop:
                    current_route.add_student(stud)
        
        for bus_ind in range(len(cap_counts)):
            bus = cap_counts[bus_ind]
            #found the smallest suitable bus
            if current_route.occupants <= bus[0]:
                #mark the bus as taken
                bus[1] -= 1
                current_route.updateBus(bus[0])
                #if all buses of this capacity are now taken, remove
                #this capacity
                if bus[1] == 0:
                    cap_counts.remove(bus)
                    
                break
        
        route_list.append(current_route)
        
    return route_list




route_list = makeRoutes(current_time, school_route, stud_route, students)

result_list, stop_info_list = originalBreakRoute(current_time, school_route, stud_route)




def originalBreakRoute(dropoff_time, school_route, stud_route):
    
    time_list = list()
    temp_times = list()
    base = school_route[-1]
    
    for index, stop in enumerate(stud_route):
        temp_times.append(travel_times[base][stop])

        if dropoff_time + sum(temp_times) > max_time:
            base = school_route[-1]
            if len(temp_times) == 1:
                time_list.append(temp_times)
                temp_times = list()
                
            else:
                time_list.append(temp_times[:-1])
                temp_times = list([travel_times[base][stop]])
        base = stop
        
    if temp_times:
        time_list.append(temp_times)
    
    result_list = list()
    ind = 0 
    for group in time_list:
        group_list = list()
        for stop in group:
            group_list.append(stud_route[ind])
            ind += 1
        result_list.append(school_route + group_list)

    return result_list, time_list


print("\n")
print(result_list)
print(time_list)



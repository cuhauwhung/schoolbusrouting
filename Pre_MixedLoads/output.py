import pandas as pd
import numpy as np 
import pickle
import constants
import statistics

# Output the clustered objects (schools/stops) with
# their respective geolocations
def output_geo_with_labels(clustered):
    clustered = clustered.sort_values(by='label')
    file = open("elem_schools_geo" + ".txt", "w") 
    file.write("category,latitude,longitude\n") 

# Write dictionaries to disc
# new_schools: dataframe of clustered schools
# schoolcluster_students_map_df: 
def output_dictionary(schools_students_attend, schoolcluster_students_map_df, student_level):
    schools_students_attend.to_csv(str(student_level) + '_clustered_schools_file.csv', sep=';', encoding='utf-8')
    with open(str(student_level) + '_clusteredschools_students_map' ,'wb') as handle:
        pickle.dump(schoolcluster_students_map_df, handle, protocol=pickle.HIGHEST_PROTOCOL)

# Print statistics of a school cluster
def print_begin_stats(cluster_school_map, schoolcluster_students_map, cap_counts, school_type):
    
    num_students = 0 
    num_schools = 0 

    for value in schoolcluster_students_map.values():
        for j in range(0, len(value)):
            num_students = num_students + len(value[j])
            
    for value in cluster_school_map.values():
        num_schools = num_schools + len(value)

    tot_cap = 0
    for bus in cap_counts:
        tot_cap += bus[0]*bus[1]

    print('--------------------------------------------------------------------')
    print("Starting to route " + school_type.upper() + " SCHOOL students")
    print('PARAMETERS USED')
    print('RADIUS: ' + str(constants.RADIUS))
    print('---------------------------------')
    print('Pre-routing statistics')
    print('---------------------------------')
    print("Num. of Students: " + str(num_students))
    print("Num. of Schools: " + str(num_schools))
    print("Num. of School Clusters: " +str(len(cluster_school_map)))
    print("Num. of School - Stops Cluster: " + str(len(schoolcluster_students_map)))
    print("Total capacity: " + str(tot_cap) + "\n")
    print("Bus Info: ")
    print(cap_counts)


# Print statistics after routing complete
def get_route_stats(routes_returned, cluster_school_map, schoolcluster_students_map):
    
    # Initialization
    buses_used = dict({16: 0, 17: 0, 24: 0, 33: 0, 34: 0, 41: 0, 62: 0, 65: 0, 71: 0, 84: 0})
    route_travel_info, utility_rate, exceeded_routes = list(), list(), list()
    student_count, routes_count, num_students, num_schools, num_combined_routes= 0, 0, 0, 0, 0
    
    for i in routes_returned:
        for j in routes_returned[i]:
            
            routes_count += len(j)
            
            for route in j:
                student_count += route.occupants
                
                if route.get_route_length() >= constants.MAX_TIME: 
                    exceeded_routes.append(route.get_route_length())

                if route.bus_size in buses_used: 
                    buses_used[route.bus_size] += 1
                   
                if route.is_combined_route == True:
                    num_combined_routes +=1 

                utility_rate.append(route.occupants/constants.CAPACITY_MODIFIED_MAP[route.bus_size][constants.SCHOOL_TYPE_INDEX])
                        
                for x in route.path_info:
                    route_travel_info.append(x)
                
    total_travel_time = round((sum([i for i, j in route_travel_info])/3600), 2)
    utility_rate = round(np.average(utility_rate), 2)
    average_travel_time = round(total_travel_time*60/routes_count)

    for value in schoolcluster_students_map.values():
        for j in range(0, len(value)):
            num_students = num_students + len(value[j])
            
    for value in cluster_school_map.values():
        num_schools = num_schools + len(value)
 
    print('---------------------------------')
    print(constants.SCHOOL_TYPE.upper() + '-schools routing statistics')
    print('---------------------------------')
    print("Num. of Students Routed: " + str(student_count))
    print("Num. of Routes Generated: " + str(routes_count))
    print("Num. of Schools: " + str(num_schools))
    print("Num. of School Clusters: " +str(len(cluster_school_map)))
    print("Total travel time: " + str(total_travel_time) + " hours" )
    print("Average travel time / route: " + str(average_travel_time) + " minutes")
    print("Utility rate: " + str(utility_rate*100) + "%")
    print("Buses used: " + str(sum(buses_used.values())))
    print(buses_used)
    print("Buses left: ") 
    print(dict(constants.CAP_COUNTS))

    if exceeded_routes:
        print(' - - - - - - - - - - - - - - - - -')
        print("COMBINED ROUTE STATS: ") 
        print("Number of combined routes: " + str(num_combined_routes))
        print("Number of routes that exceed time limit: " + str(len(exceeded_routes)))
        print("Average time of exceeded routes: " + str(round((statistics.mean(exceeded_routes)-constants.MAX_TIME)/60, 2)) + " minutes")
        print('----------------------------------\n') 
    
    output = [student_count, routes_count, total_travel_time, average_travel_time, utility_rate, buses_used, cluster_school_map, schoolcluster_students_map]
    return output
    
# write routes into .txt file
# cluster_school_map: maps clusters to schools
# routes_returned: bus routes for each school cluster
def output_routes_to_file(output, routes_returned, filename, title):

    prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
    all_geocodesFile = prefix+'all_geocodes.csv'
    geocodes = pd.read_csv(all_geocodesFile)

    if constants.REMOVE_LOW_OCC:
        file = open("remove_low_occ_" + str(filename) + ".txt", "w")   
    else:
        file = open("normal_" + str(filename) + ".txt", "w")   
    
    file.write('---------------------------------\n')
    file.write('ROUTE STATS: ' + str(title) + '\n')
    file.write('---------------------------------\n')
    file.write("LOW OCCUPANCY REMOVAL: " + str(constants.REMOVE_LOW_OCC) + '\n')
    file.write("Num. of Students Routed: " + str(output[0]) + '\n')
    file.write("Num. of Routes Generated: " + str(output[1]) + '\n')
    file.write("Total travel time: " + str(output[2]) + " hours" + '\n')
    file.write("Average travel time / route: " + str(output[3]) + " minutes" + '\n')
    file.write("Utility rate: " + str(round(output[4]*100, 2)) + '%\n')

    for index in range(0, len(routes_returned)):   
        
        file.write("----------------------\n")
        file.write("Cluster Number: " + str(index) + "\n")
        file.write("Schools in this cluster: \n") 
        
        count = 0
        for clus_school in output[6][index]:            
            file.write(str(clus_school.school_name) +  " (" + str(clus_school.cost_center) + ")"+"\n")
        
        file.write('\n')
        googlemap_routes = list()

        for idx in range(0, len(routes_returned[index])):
            
            for route in routes_returned[index][idx]:
                if int(route.occupants) < 8:
                    file.write("LOW OCCUPANCY BUS \n")
                
                if route.is_combined_route == True:
                    file.write("Combined Route == True\n")
               
                travel_time = 0 
                for route_stat in route.path_info:
                    travel_time += route_stat[0]

                file.write("Route index: " + str(index) + "." + str(count) + "\n")
                file.write("Route path: " + str(route.path) + "\n")
                file.write("Route travel time: " + str(round(travel_time/60, 2)) +  " minutes\n") 
                file.write("Route path information: " + str(route.path_info) + "\n")
                file.write("Bus capacity: " + str(route.bus_size) + "\n")
                file.write("Num. of occupants: " + str(route.occupants) + "\n")
                link = "https://www.google.com/maps/dir"
    
                for point in route.path:
                    point_geoloc = geocodes.iloc[point,: ]
                    
                    link += ("/" + str(round(point_geoloc['Lat'],6)) + "," + str(round(point_geoloc['Long'],6)))
                    
                googlemap_routes.append(link)
                file.write("Google Maps Link: \n")
                file.write(link)
                file.write("\n---------------------- \n")
                count += 1
                
        file.write("\n###################################################\n")
        file.write("BULK GOOGLE MAP ROUTES FOR CLUSTER \n")
        for x in googlemap_routes:
            file.write(x)
            file.write("\n")
        file.write("###################################################\n")

    file.close()

# Print out student statistics
def get_student_stats(total_routes): 
    student_travel_times = list()

    for i in total_routes: 
        for j in total_routes[i]:
            for route in j: 
                for stud in route.students:
                    student_travel_times.append(stud.time_on_bus)

    student_travel_times.sort() 
    print("Average student travel time: " + str(statistics.mean(student_travel_times)))
    pass
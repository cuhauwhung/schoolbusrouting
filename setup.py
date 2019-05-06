import pandas as pd
import numpy as np
import copy
import constants
from locations import School, Student
from clustering import obtainClust_DBSCAN_AGGO_combined, partition_students
from collections import defaultdict

def californiafy(address):
    return address[:-6] + " California," + address[-6:]

# Edit belltimes from ___AM to only seconds
def edit_bell_times(schools):
    newTime = list()
    for row in schools.iterrows():        
        if isinstance(row[1]["start_time"], str):
            hours, mins = row[1]["start_time"].split(":", 1)
            hours = int(hours)*3600
            mins = int(mins[:2])*60
            newTime.append(hours+mins)
        else:
            newTime.append(np.nan)
    schools['start_time'] = newTime
    return schools

# For verification purposes
def update_verif_counters(schoolcluster_students_map_df):
    cluster_counter_dict = dict()
    stop_counter_dict = defaultdict(int)
    
    for i in schoolcluster_students_map_df:
        stop_set = set()

        for _, row in schoolcluster_students_map_df[i].iterrows():
            stop = constants.CODES_INDS_MAP[constants.STOPS_CODES_MAP[californiafy(row['AM_Stop_Address'])]]
            stop_set.add(stop)
            stop_counter_dict[stop] += 1

        cluster_counter_dict[i] = stop_set
        
    constants.STUDENT_CLUSTER_COUNTER = cluster_counter_dict 
    constants.STUDENT_STOP_COUNTER = stop_counter_dict 

# For school dropoff information purposes 
def update_school_dropoff_info(schools_students_attend):
    
    dropoff_dict = dict()
    dropoff_interval = dict()
    start_time = dict()
    
    for idx, row in schools_students_attend.iterrows():
        dropoff_dict[row['tt_ind']] = row['dropoff_time']
        dropoff_interval[row['tt_ind']] = row['bell_time_intervals']
        start_time[row['tt_ind']] = row['start_time']
        
    constants.SCHOOL_DROPOFF_TIME = dropoff_dict 
    constants.SCHOOL_BELL_TIMES = start_time
    constants.SCHOOL_DROPOFF_RANGE = dropoff_interval


# Set up up the dataframes to make stops, zipdata, schools, and phonebook
# Filter and wrangle through data 
def setup_data(stops, zipdata, schools, phonebook, bell_times):
    
    prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'

    stops = prefix+'stop_geocodes_fixed.csv'
    zipdata =prefix+'zipData.csv'
    schools = prefix+'school_geocodes_fixed.csv'
    phonebook = prefix+'totalPhoneBook.csv'
    bell_times = prefix+'bell_times.csv'

    stops = pd.read_csv(stops, low_memory=False)
    zipdata = pd.read_csv(zipdata, low_memory=False)
    
    bell_times = pd.read_csv(bell_times, low_memory=False, encoding='windows-1252')
    schools = pd.read_csv(schools, dtype={'Location_Code': int, 'School_Name': str, 'Cost_Center': int, 'Lat': float, 'Long': float}, low_memory=False)
    schools = schools[['Location_Code', 'School_Name', 'Cost_Center', 'Lat', 'Long']]
    schools = pd.merge(schools, bell_times[['start_time','bell_time_intervals', 'dropoff_time', 'Cost_Center']], on ='Cost_Center', how='left')
    
    school_index_list = list()
    for row in schools.iterrows():
        school_index_list.append(constants.CODES_INDS_MAP[constants.SCHOOLS_CODES_MAP[str(row[1]['Cost_Center'])]])

    schools['tt_ind'] = school_index_list
    schools = edit_bell_times(schools)
    
    phonebook = pd.read_csv(phonebook, dtype={"RecordID": str, 'Prog': str, 'Mod_Grade': int, 'Cost_Center': str, "AM_Trip": str, "AM_Route": str, 'Lat': float, 'Long': float}, low_memory=False)
    phonebook = phonebook[['RecordID', 'Prog', 'Cost_Center', 'Cost_Center_Name','Mod_Grade','AM_Stop_Address', 'AM_Route', 'AM_Trip']]
    phonebook = phonebook[phonebook['AM_Route'] != str(9500)]
    phonebook = phonebook[phonebook['AM_Trip'] == str(1)]
    phonebook = phonebook[phonebook['AM_Stop_Address'] != str(", , ")]
    phonebook = pd.merge(phonebook, stops[['AM_Stop_Address','Lat', 'Long']], on= 'AM_Stop_Address', how='inner')
    phonebook = phonebook.dropna()     # 36145 -> 36143
    phonebook['Cost_Center']=phonebook['Cost_Center'].astype(int)

    phonebook["School_type"] = None
    mask = (phonebook['Mod_Grade'] < 6)
    phonebook['School_type'] = phonebook['School_type'].mask(mask, "elem")
    mask = (phonebook['Mod_Grade'] >= 6) & (phonebook['Mod_Grade'] < 9)
    phonebook['School_type'] = phonebook['School_type'].mask(mask, "middle")
    mask = (phonebook['Mod_Grade'] >= 9) & (phonebook['Mod_Grade'] <=13)
    phonebook['School_type'] = phonebook['School_type'].mask(mask, "high")
    
    phonebook.loc[phonebook['School_type'] == 'elem', 'School_type'] = 0
    phonebook.loc[phonebook['School_type'] == 'middle', 'School_type'] = 1
    phonebook.loc[phonebook['School_type'] == 'high', 'School_type'] = 2

    phonebook = phonebook[phonebook.Prog.isin(constants.PROG_TYPES)]
    phonebook = phonebook.rename(index=str, columns={"Lat": "Lat", "Long": "Long"})

    schools_students_attend = phonebook["Cost_Center"].drop_duplicates().dropna()
    schools_students_attend = schools.loc[schools['Cost_Center'].isin(schools_students_attend)]
    schools_students_attend = pd.merge(schools_students_attend, phonebook[['Cost_Center', 'School_type']], on=['Cost_Center'], how='inner')
    
    # Cluster schools and merge back into list of schools_students_attend
    clustered_schools = obtainClust_DBSCAN_AGGO_combined(schools_students_attend)
    schools_students_attend = pd.merge(schools_students_attend, clustered_schools[['label', 'tt_ind']], on=['tt_ind'], how='inner').drop_duplicates()
    schools_students_attend = schools_students_attend.sort_values(['label'], ascending=[True])
    update_school_dropoff_info(schools_students_attend)
    
#    # Geolocation based-approach
#    clustered_schools = obtainClust_DBSCAN(schools_students_attend, constants.RADIUS, constants.MIN_PER_CLUSTER)
#    schools_students_attend = pd.merge(schools_students_attend, clustered_schools, on=['Lat', 'Long'], how='inner').drop_duplicates()
#    schools_students_attend = schools_students_attend.sort_values(['label', 'r1_start'], ascending=[True, False])
    
    schoolcluster_students_map_df = partition_students(schools_students_attend, phonebook)
    update_verif_counters(schoolcluster_students_map_df)

    return schools_students_attend, schoolcluster_students_map_df


# Setup the buses
def setup_buses(bus_capacities):
    cap_counts_dict = dict()  #map from capacities to # of buses of that capacity
    caps = open(bus_capacities, 'r')
    for bus in caps.readlines():
        fields = bus.split(";")
        cap = int(fields[1])
        if cap not in cap_counts_dict:
            cap_counts_dict[cap] = 0
        cap_counts_dict[cap] += 1
    caps.close()
    #now turn into a list sorted by capacity
    cap_counts_list = list(cap_counts_dict.items())
    cap_counts_list = sorted(cap_counts_list, key = lambda x:x[0])
    for i in range(len(cap_counts_list)):
        cap_counts_list[i] = list(cap_counts_list[i])
    return cap_counts_list

# Setup contract buses
def setup_contract_buses():
    contract_cap_counts = copy.deepcopy(constants.CAP_COUNTS)
    for i in range(0, len(contract_cap_counts)):
        contract_cap_counts[i][1] = 0 
    return contract_cap_counts

# Setup clusters: input all required files 
def setup_clusters(cluster_schools_df, schoolcluster_students_df):
    
    # Cluster to schools map
    cluster_school_map = dict()
    
    for i in list(cluster_schools_df['label'].drop_duplicates()):
        subset = cluster_schools_df.loc[cluster_schools_df['label'] == i].copy()  
        schoollist = []
        for row in subset.iterrows():
            cost_center = str(int(row[1]['Cost_Center']))
            school_ind = constants.CODES_INDS_MAP[constants.SCHOOLS_CODES_MAP[cost_center]]
            schoollist.append(School(school_ind, cost_center, row[1]['School_Name']))
        cluster_school_map[i] = schoollist

    # School cluster to cluster of studentts map 
    schoolcluster_students_map = dict()
    
    for key, value in schoolcluster_students_df.items():
        list_of_clusters = []
        for val in list(value['label'].drop_duplicates()):
            subset = value.loc[value['label'] == val].copy()  
            student_list = []
            
            for index, row in subset.iterrows():
                stop = californiafy(row['AM_Stop_Address'])
                stop_ind = constants.CODES_INDS_MAP[constants.STOPS_CODES_MAP[stop]]
                cost_center = str(int(row['Cost_Center']))
                school_ind = constants.CODES_INDS_MAP[constants.SCHOOLS_CODES_MAP[cost_center]]
                this_student = Student(stop_ind, school_ind)
                student_list.append(this_student)
            list_of_clusters.append(student_list)
        schoolcluster_students_map[key] = list_of_clusters

    return cluster_school_map, schoolcluster_students_map

# Set up the school_type map 
def setup_schooltype_map(schools_students_attend):
    schooltype_map = dict()
    for index, row in schools_students_attend.iterrows():
        schooltype_map[row['tt_ind']] = row['School_type']
    return schooltype_map 

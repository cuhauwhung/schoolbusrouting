import constants
from locations import School, Student
from utils import californiafy, timesecs

#phonebooks: list of filenames for phonebooks
#phonebooks are assumed to be in the format that was provided to
#me in early November 2018
#all_geocodes: filename for list of all geocodes. gives map from geocode to ind
#geocoded_stops: file name for map from stop to geocode
#geocoded_schools: file name for map from school to geocode
#returns a list of all students, a dict from schools to sets of
#students, and a dict from schools to indices in the travel time matrix.
#bell_sched: file name for which column 3 is cost center and
#column 4 is start time
def setup_students(phonebooks, all_geocodes, geocoded_stops,
                   geocoded_schools, bell_sched):
    
    stops = open(geocoded_stops, 'r')
    stops_codes_map = dict()
    for address in stops.readlines():
        fields = address.split(";")
        if len(fields) < 3:
            continue
        stops_codes_map[fields[0]] = (fields[1].strip() + ";"
                                      + fields[2].strip())
    stops.close()
    
    belltimes = open(bell_sched, 'r')
    centers_times_map = dict()  #maps cost centers to times in seconds
    belltimes.readline()  #get rid of header
    for bell_record in belltimes.readlines():
        fields = bell_record.split(";")
        centers_times_map[fields[3]] = timesecs(fields[4])
    
    schools = open(geocoded_schools, 'r')
    schools_codes_map = dict()  #maps schools to geocodes
    schools_students_map = dict()  #maps schools to sets of students
    schools.readline()  #get rid of header
    for cost_center in schools.readlines():
         fields = cost_center.split(";")
         if len(fields) < 8:
             continue
         schools_codes_map[fields[1]] = (fields[6].strip() + ";"
                                         + fields[7].strip())
         schools_students_map[fields[1]] = set()
    schools.close()
    
    geocodes = open(all_geocodes, 'r')
    codes_inds_map = dict()
    ind = 0
    for code in geocodes.readlines():
        codes_inds_map[code.strip()] = ind
        ind += 1
    geocodes.close()
    
    schools_inds_map = dict()
    for school in schools_codes_map:
        schools_inds_map[school] = codes_inds_map[schools_codes_map[school]]
    
    students = []
    bus_col = 12
    #Maintain a dictionary of school indices to schools so that
    #school objects can be tested for equality.
    ind_school_dict = dict()
    for pb_part_filename in phonebooks:
        pb_part = open(pb_part_filename, 'r')
        pb_part.readline()  #header
        for student_record in pb_part.readlines():
            fields = student_record.split(";")
            if len(fields) <= bus_col + 6:
                continue
            if fields[bus_col + 6].strip() == ", ,":  #some buggy rows
                continue
            if fields[bus_col - 1].strip() == "9500":  #walker
                continue
            if fields[bus_col + 2].strip() not in ["1", "01"]:  #not first trip
                continue
            if fields[1].strip() == "":  #no school given
                continue
            #For now, I won't consider special ed.
            if fields[5].strip() not in ["M", "X", "P"]:
                continue
            stop = californiafy(fields[bus_col + 6])
            school = fields[1].strip()  #Cost center id
            stop_ind = codes_inds_map[stops_codes_map[stop]]
            school_ind = codes_inds_map[schools_codes_map[school]]
            grade = fields[3].strip()  #Grade level
            age_type = 'Other'
            try:
                grade = int(grade)
            except:
                grade = -1
            if int(grade) in constants.GRADES_TYPE_MAP:
                age_type = constants.GRADES_TYPE_MAP[int(grade)]
            if age_type == 'Other':
                print(grade)
            if school_ind not in ind_school_dict:
                belltime = 8*60*60  #default to 8AM start
                #None of the 19xxxxx schools have start times.
                if school in centers_times_map:
                    belltime = centers_times_map[school]
                else:
                    if constants.VERBOSE:
                        print("No time given for " + school)                    
                ind_school_dict[school_ind] = School(school_ind, belltime)
            this_student = Student(stop_ind, ind_school_dict[school_ind],
                                   age_type, fields)
            students.append(this_student)
            schools_students_map[school].add(this_student)
        pb_part.close()
        
    return students, schools_students_map, schools_inds_map



#bus_capacities is an input csv file where the first
#column is bus ID and the second is capacity.
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

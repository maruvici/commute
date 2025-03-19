import xml.etree.ElementTree as ET

# Load and parse the XML file
tree = ET.parse('tripinfo_out.xml')
root = tree.getroot()

tree2 = ET.parse('summary_out.xml')
root2 = tree2.getroot()

def extract_tripinfo(attribute_name, flag = 0):
    values = []
    for tripinfo in root.findall('tripinfo'):
        value = tripinfo.get(attribute_name)
        if value is not None:
            values.append(float(value))
        if value is not None and flag == 1:
            timestep = tripinfo.get('depart')
            if float(timestep) >= 14400.00:
                return sum(values)/len(values)
            
    return sum(values)/len(values)

def extract_summary(attribute_name, flag = 0):
    values = []
    for step in root2.findall('step'):
        value = step.get(attribute_name)
        if value is not None:
            values.append(float(value))
        if value is not None and flag == 1:
            timestep = step.get('time')
            if float(timestep) == 14400.00:
                return sum(values)/14400
    return sum(values)/14400

def extract_tripinfo_vfr():
    sum = 0.0
    # CHANGE LIST! GET FROM ARRIVAL LANE AND DEPART LANE IN TRIPINFO_OUT.XML
    #depart_bottom = ['R7_', 'univ-road-lower-out_','univ-road-upper-out_', 'f.dela-rosa-road_']
    #arrive_bottom = ['L12_', 'univ-road-lower-in_', 'univ-road-upper-in_']
    #depart_top =['L1_','thornton-drive-extension-outward_','b.gonzales-road_']
    #arrive_top =['R1_','thornton-drive-extension-towards']
    
    depart_bottom = ["R7", "aurora-lower_in", "aurora-upper_in"]
    arrive_bottom = ["L7", "aurora-lower_out", "aurora-upper_out"]

    depart_middle = ["f.dela_rosa-road", "univ_road-upper_in", "univ_road-lower_in"]
    arrive_middle = ["univ_road-upper_out", "univ_road-lower_out"]

    depart_top = ["L1", "thornton_drive-extension-in", "b.gonzales-road-in"]
    arrive_top = ["R1", "thornton_drive-extension-out", "b.gonzales-road-out"]
    
    tot_car = 0.0
    for tripinfo in root.findall('tripinfo'):
        value = tripinfo.get('arrival')
        if value is not None and float(value) <= 14440.0:
            #sum = sum + 1
            tot_car += 1.0
            car_departure= tripinfo.get('departLane')
            car_departure = car_departure[:-2]
            car_arrival= tripinfo.get('arrivalLane')
            car_arrival=car_arrival[:-2]

            # if vehicle traverses entire network (bottom -> top or top -> bottom), add 3 to flow count (pass all 3 intersections)
            if ((car_departure in depart_bottom) and (car_arrival in arrive_top)) or ((car_departure in depart_top) and (car_arrival in arrive_bottom)):
                sum += 3.0
            # else if vehicle traverses 2 intersections only, add 2 to flow count
            elif ((car_departure in depart_top) and (car_arrival in arrive_middle)) or ((car_departure in depart_bottom) and (car_arrival in arrive_middle)):
                sum += 2.0
            elif ((car_departure in depart_middle) and (car_arrival in arrive_top)) or ((car_departure in depart_middle) and (car_arrival in arrive_bottom)):
                sum += 2.0
            # otherwise only add 1 to flow count
            else:
                sum += 1.0
            
    return float(3600*sum/14400.0)

def serviced_4hr(attribute_name):
    for step in root2.findall('step'):
        value = step.get('arrived')
        if value is not None:
            timestep = step.get('time')
            if float(timestep) == 14400.00:
                return value

attribute_qt = 'halting'
average_qt_whole = extract_summary(attribute_qt,  0)
print(f"(WHOLE) Average queue length (veh): " + str(average_qt_whole/24))

average_qt_4hr = extract_summary(attribute_qt,  1)
print(f"(4 HR) Average queue length (veh) - 4 hour: " + str(average_qt_4hr/24))

attribute_wt = 'waitingTime'
average_wt_whole = extract_tripinfo(attribute_wt, 0)
print(f"(WHOLE) Average time in queue (s): " + str(average_wt_whole))

average_wt_4hr = extract_tripinfo(attribute_wt, 1)
print(f"(4 HR) Average time in queue (s): " + str(average_wt_4hr))

attribute_vfr = 'running'
average_vfr_whole = extract_tripinfo_vfr()
print(f"(WHOLE) Average vehicular flow rate (veh/hr): " + str (average_vfr_whole))

average_vfr_4hr = extract_tripinfo_vfr()
print(f"(4 HR) Average vehicular flow rate (veh/hr): " + str (average_vfr_4hr))

attribute_serviced = 'time'
cars_serviced = serviced_4hr(attribute_serviced)
print(f"Cars serviced in 4 hours is:  " + str (cars_serviced))

# We want to calculate the parameters every 15 minutes
list_seconds = []
list_hours = []
for x in range(16):
    list_seconds.append((str(x*15.00*60.00),str((x+1)*15.00*60.0)))
    list_hours.append(((6 + 0.25*x), (6 + 0.25*(x+1))))
    
    # Generate everything from 0-40 minutes.
#print(list_seconds)
print(list_hours)

def extract_summary_15min_ql(start, end):
    values = []
    for step in root2.findall('step'):
        value = step.get('halting')
        depart_time = step.get('time')
        if value is not None and float(depart_time) >= float(start):
            #print(f"value is:" + str(value))
            values.append(float(value))
            #print(values)
        if value is not None:
            timestep = step.get('time')
            if float(timestep) == float(end):
                x = sum(values)
                #print(x)
                return x/900.0
    #return sum(values)/14400

queue_lengths = []
for element in list_seconds:
    start = element[0]
    end = element[1]
    queue_length = extract_summary_15min_ql(start,end)
    if queue_length is not None:
        queue_lengths.append(queue_length/24.0)
print(f"QUEUE LENGTHS  6-10AM - 15 MINUTE INTERVALS")
print(queue_lengths)    
#print(len(queue_lengths) + len(list_hours))

def extract_tripinfo_15min_qt(start, end):
    values = []
    for step in root.findall('tripinfo'):
        value = step.get('waitingTime')
        depart_time = step.get('depart')
        if value is not None and float(depart_time) >= float(start)  and float(depart_time) <= float(end):
            values.append(float(value))
            #print(value)
    #print(len(values))
    queuetime= sum(values)/len(values)
    #print("queue time is: " + str(queuetime))
    return sum(values)/len(values)

queue_times = []
for element in list_seconds:
    start = element[0]
    end = element[1]
    queue_time = extract_tripinfo_15min_qt(start,end)
    queue_times.append(queue_time)

print(f"QUEUE TIMES  6-10AM - 15 MINUTE INTERVALS")
print(queue_times)
    
#print(len(queue_times) + len(list_hours))

def extract_tripinfo_15min_fr(start,end):
    sum = 0.0
    #depart_bottom = ['R7_', 'univ-road-lower-out_','univ-road-upper-out_', 'f.dela-rosa-road_']
    #arrive_bottom = ['L12_', 'univ-road-lower-in_', 'univ-road-upper-in_']
    #depart_top =['L1_','thornton-drive-extension-outward_','b.gonzales-road_']
    #arrive_top =['R1_','thornton-drive-extension-towards']

    depart_bottom = ["R7", "aurora-lower_in", "aurora-upper_in"]
    arrive_bottom = ["L7", "aurora-lower_out", "aurora-upper_out"]

    depart_middle = ["f.dela_rosa-road", "univ_road-upper_in", "univ_road-lower_in"]
    arrive_middle = ["univ_road-upper_out", "univ_road-lower_out"]

    depart_top = ["L1", "thornton_drive-extension-in"]
    arrive_top = ["R1", "thornton_drive-extension-out", "b.gonzales-road-out", "b.gonzales-road-in"]

    tot_car = 0.0
    for tripinfo in root.findall('tripinfo'):
        value = tripinfo.get('arrival')
        if value is not None and float(value) >= float(start) and float(value) <= float(end):
            #sum = sum + 1
            tot_car += 1.0
            car_departure= tripinfo.get('departLane')
            car_departure = car_departure[:-2]
            car_arrival= tripinfo.get('arrivalLane')
            car_arrival=car_arrival[:-2]

            # if vehicle traverses entire network (bottom -> top or top -> bottom), add 3 to flow count (pass all 3 intersections)
            if ((car_departure in depart_bottom) and (car_arrival in arrive_top)) or ((car_departure in depart_top) and (car_arrival in arrive_bottom)):
                sum += 3.0
            # else if vehicle traverses 2 intersections only, add 2 to flow count
            elif ((car_departure in depart_top) and (car_arrival in arrive_middle)) or ((car_departure in depart_bottom) and (car_arrival in arrive_middle)):
                sum += 2.0
            elif ((car_departure in depart_middle) and (car_arrival in arrive_top)) or ((car_departure in depart_middle) and (car_arrival in arrive_bottom)):
                sum += 2.0
            # otherwise only add 1 to flow count
            else:
                sum += 1.0
            
    return float(3600*sum/900.0)

flow_rates = []
for element in list_seconds:
    start = element[0]
    end = element[1]
    flow_rate = extract_tripinfo_15min_fr(start,end)
    flow_rates.append(flow_rate)

print(f"FLOW RATES  6-10AM - 15 MINUTE INTERVALS")
print(flow_rates)    
#print(len(flow_rates) + len(list_hours))





#print(extract_tripinfo_15min_qt(0,14400))
#print(sum(queue_times)/len(queue_times))
# adapted from previous iteration's implementation
# https://github.com/mylescoding/ssl07-2324/blob/main/README.md

import random

class Source:
    def __init__(self, source_name, possible_routes):
        self.source_name = source_name
        self.possible_routes = possible_routes
        
    def getSourceName(self):
        return self.source_name
    def getPossibleRoutes(self):
        return self.possible_routes

class Intermediate:
    def __init__(self, node_name, possible_sources):
        self.node_name = node_name
        self.possible_sources = possible_sources
    def getIntermediate_Node_Name(self):
        return self.node_name
    def getPossibleSources(self):
        return self.possible_sources

count = 0
def createXML_hourly_profiled(dic, idx):
    global count
    xml_entries = []
    #assume ratio between motorcycles to cars is  3:2
    start_end_times = [('0.0', '3600.0'), ('3600.0', '7200.0'), ('7200.0', '10800.0'), ('10800.0', '14400.0'), ('14400.0', '18000.0'), ('18000.0', '21600.0'), ('21600.0', '25200.0'), ('25200.0', '28800.0'), ('28800.0', '32400.0'), ('32400.0', '36000.0'), ('36000.0', '39600.0'), ('39600.0', '43200.0'), ('43200.0', '46800.0'), ('46800.0', '50400.0')]
    
    for key in dic:
        motor_count = int(round(dic[key] * 0.6))
        car_count = int(round(dic[key] * 0.4))
        xml_entry_motor = '<flow id ="f_' + str(count) +'"' + ' type = "phMotor" begin="'  + str(start_end_times[idx - 5][0]) + '0" route="' + str(key) + '" end="'+ str(start_end_times[idx - 5][1]) + '0" number="'+ str(motor_count) +'"'+' departLane="free" departSpeed="max"'+'/>' 
        count = count + 1
        xml_entry_car = '<flow id ="f_' + str(count) +'"' + ' type = "phCar" begin="'  + str(start_end_times[idx - 5][0]) + '0" route="' + str(key) + '" end="'+ str(start_end_times[idx - 5][1]) + '0" number="'+ str(car_count) +'"'+' departLane="free" departSpeed="max"'+'/>' 
        count = count + 1
        if motor_count != 0:
            xml_entries.append(xml_entry_motor)
        else:
            count = count - 1
        if car_count != 0:
            xml_entries.append(xml_entry_car)
        else:
            count = count - 1

    for entry in xml_entries:
        print(entry)
        pass

    return
def createXML_wholeday_profiled(dic):
    count = 0
    xml_entries = []
    #assume ratio between motorcycles to cars is  3:2
    start_end_times = [('0.0', '3600.0'), ('3600.0', '7200.0'), ('7200.0', '10800.0'), ('10800.0', '14400.0'), ('14400.0', '18000.0'), ('18000.0', '21600.0'), ('21600.0', '25200.0'), ('25200.0', '28800.0'), ('28800.0', '32400.0'), ('32400.0', '36000.0'), ('36000.0', '39600.0'), ('39600.0', '43200.0'), ('43200.0', '46800.0'), ('46800.0', '50400.0')]
    for idx in range (4):
        for key in dic:
            motor_count = int(round(dic[key] * 0.6))
            car_count = int(round(dic[key] * 0.4))
            xml_entry_motor = '<flow id ="f_' + str(count) +'"' + ' type = "phMotor" begin="'  + str(start_end_times[idx][0]) + '0" route="' + str(key) + '" end="'+ str(start_end_times[idx][1]) + '0" number="'+ str(motor_count) +'"/>' 
            count = count + 1
            xml_entry_car = '<flow id ="f_' + str(count) +'"' + ' type = "phCar" begin="'  + str(start_end_times[idx][0]) + '0" route="' + str(key) + '" end="'+ str(start_end_times[idx][1]) + '0" number="'+ str(car_count) +'"/>' 
            count = count + 1
            if motor_count != 0:
                xml_entries.append(xml_entry_motor)
            else:
                count = count - 1
            if car_count != 0:
                xml_entries.append(xml_entry_car)
            else:
                count = count - 1

    for entry in xml_entries:
        print(entry)
        pass

    return


def distribute(time_slot):

    for source_node in sources:
        sum_out_src = 0
        demand_sum = 0
        if (source_node.getPossibleRoutes() != []):
            for intermediate_node in intermediates:  
                if (intermediate_node.getIntermediate_Node_Name() in source_node.getPossibleRoutes()):
                    #print( source_node.getPossibleRoutes()) 
                    # kbt5: ["kuf4", "kuf4a_kbt2", "kuf4a_kbt3", "kuf4b", "kuf5"]
                    #print("Intermediate: " + str(intermediate_node.getIntermediate_Node_Name()))
                    #sum_out_src += intermediate_demand_dict[intermediate_node.getIntermediate_Node_Name()]
                    sum_out_src += intermediate_demand_dict_wholeday[intermediate_node.getIntermediate_Node_Name()][time_slot]
                    #print("sum_out_src is:" + str(sum_out_src))
            #print("OKAY SLAAAYYYY")
            for route in source_node.getPossibleRoutes():
                #once we get the some, get ratio
                ratio = float(intermediate_demand_dict_wholeday[route][time_slot] / sum_out_src)
                #print("source is: " + source_node.getSourceName() +" with demand of " + str(source_demand_dict_wholeday[source_node.getSourceName()][time_slot])+ " while route is: " + str(intermediate_demand_dict_wholeday[route][time_slot]))
                #print("ratio:" + str(ratio))
                demand = round(float(source_demand_dict_wholeday[source_node.getSourceName()][time_slot] * ratio))
                demand_sum += demand
                new_route_name = str(source_node.getSourceName()) + "_to_" + str(route)
                route_dict[new_route_name] = demand    
                route_name_list.append(new_route_name)
            #print("demand_sum is: " + str(demand_sum) + " actual: " + str(source_demand_dict_wholeday[source_node.getSourceName()][time_slot]))
        elif(source_node.getPossibleRoutes() == []):
            route_dict[source_node.getSourceName()] = source_demand_dict_wholeday[source_node.getSourceName()][time_slot]
            route_name_list.append(source_node.getSourceName())
    return

source_demand_dict_wholeday = {
        'ka-1': [569, 640, 619, 512, 471, 442, 432, 481, 486, 580, 607, 665, 603, 539],
        'ka-1ab': [485, 545, 527, 436, 401, 377, 368, 410, 414, 494, 517, 566, 513, 459],
        'ka-3': [3900, 4382, 4241, 3505, 3229, 3030, 2960, 3297, 3330, 3973, 4157, 4553, 4128, 3690], 
        'ka-8': [1963, 2205, 2134, 1764, 1625, 1524, 1489, 1659, 1676, 1999, 2092, 2291, 2077, 1857],
        'ka-9': [383, 430, 416, 344, 317, 297, 291, 324, 327, 390, 408, 447, 405, 362],
        'ka-10': [767, 862, 834, 689, 635, 596, 582, 648, 655, 781, 817, 895, 812, 726],
        'ka-11': [3153, 3543, 3429, 2833, 2610, 2449, 2392, 2665, 2692, 3211, 3360, 3681, 3337, 2983],
        'ka-12': [142, 160, 154, 128, 118, 110, 108, 120, 121, 145, 151, 166, 150, 134],
        'kuf-7': [139, 156, 151, 125, 115, 108, 106, 118, 119, 142, 148, 163, 147, 132],
        'kuf-8': [107, 120, 116, 96, 88, 83, 81, 90, 91, 109, 114, 125, 113, 101], 
        'kuf-8a': [104, 117, 113, 94, 86, 81, 79, 88, 89, 106, 111, 122, 110, 99], 
        'kuf-9': [84, 94, 91, 75, 69, 65, 64, 71, 72, 85, 89, 98, 89, 79],
        'kuf-10b': [210, 236, 228, 189, 174, 163, 159, 177, 179, 214, 224, 245, 222, 199], 
        'kuf-10c': [826, 928, 898, 742, 684, 642, 627, 698, 705, 841, 880, 964, 874, 781], 
        'kuf-12a': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
        'kbt-4': [49, 55, 53, 44, 41, 38, 37, 41, 42, 50, 52, 57, 52, 46], 
        'kbt-4a': [451, 507, 490, 405, 373, 350, 342, 381, 385, 459, 481, 526, 477, 427], 
        'kbt-5': [5425, 6095, 5899, 4875, 4491, 4214, 4117, 4585, 4632, 5525, 5782, 6333, 5741, 5133], 
        'kbt-6': [622, 699, 676, 559, 515, 483, 472, 525, 531, 633, 663, 726, 658, 588], 
        'kbt-7': [679, 763, 739, 610, 562, 528, 515, 574, 580, 692, 724, 793, 719, 643], 
        'kbt-8': [14, 16, 15, 13, 12, 11, 11, 12, 12, 14, 15, 17, 15, 13], 
        'kbt-9': [26, 29, 28, 23, 21, 20, 19, 22, 22, 26, 27, 30, 27, 24], 
        'kbt-10': [106, 119, 115, 95, 88, 82, 80, 89, 90, 108, 113, 124, 112, 100], 
        'kbt-11': [30, 34, 32, 27, 25, 23, 23, 25, 25, 30, 32, 35, 32, 28], 
        'kbt-12': [11, 12, 12, 10, 9, 9, 8, 9, 9, 11, 12, 13, 12, 10]
    }
    
intermediate_demand_dict_wholeday = {
        'ka-4': [1930, 2169, 2099, 1735, 1598, 1499, 1465, 1631, 1648, 1966, 2057, 2253, 2043, 1826],
        'ka-4ab_to_kuf-2': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'ka-4ab_to_kuf-3': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'ka-4ab_to_kuf-3a': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'ka-5a': [3917, 4401, 4259, 3520, 3243, 3042, 2972, 3310, 3344, 3989, 4175, 4572, 4145, 3706],
        'ka-6': [271, 304, 294, 243, 224, 210, 205, 229, 231, 276, 289, 316, 286, 256],
        'kuf-2': [4045, 4545, 4399, 3636, 3349, 3142, 3070, 3419, 3454, 4120, 4311, 4722, 4281, 3827],
        'kuf-3': [259, 291, 282, 233, 214, 201, 197, 219, 221, 264, 276, 302, 274, 245],
        'kuf-3a': [29, 32, 31, 26, 24, 22, 22, 24, 25, 29, 31, 34, 30, 27],
        'kuf-4': [142, 160, 155, 128, 118, 111, 108, 120, 122, 145, 152, 166, 151, 135],
        'kuf-4a': [4, 4, 4, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4],
        'kuf-4a_to_kbt-2': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'kuf-4a_to_kbt-3': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'kuf-4b': [122, 137, 132, 109, 101, 94, 92, 103, 104, 124, 130, 142, 129, 115],
        'kuf-5': [5288, 5942, 5751, 4753, 4378, 4108, 4013, 4470, 4515, 5387, 5637, 6174, 5597, 5004],
        'kbt-2': [4149, 4662, 4512, 3729, 3435, 3223, 3148, 3507, 3542, 4226, 4422, 4843, 4391, 3926],
        'kbt-3': [39, 44, 43, 35, 32, 30, 30, 33, 34, 40, 42, 46, 42, 37]
    }

# split demand from kuf-4a to both kbt-2 and kbt-3
for idx in range(14):
    x = random.randint(0,intermediate_demand_dict_wholeday['kuf-4a'][idx])
    y = intermediate_demand_dict_wholeday['kuf-4a'][idx] - x 
    intermediate_demand_dict_wholeday['kuf-4a_to_kbt-2'][idx] = x
    intermediate_demand_dict_wholeday['kuf-4a_to_kbt-3'][idx] = y

#Source Nodes

#KA
ka1 = Source("ka-1", [])
ka1ab = Source("ka-1ab", [])
ka2a = Source("ka-2a", []) # edit this later
ka3 = Source("ka-3", [])
ka8 = Source ("ka-8", [])
ka9 = Source ("ka-9", [])
ka10 = Source("ka-10", [])
ka11 = Source("ka-11", [])
ka12 = Source("ka-12", []) # edit this later

#KX
#kx9 = Source("kx-9", []) # disregarded for now

#KUF
kuf7 = Source("kuf-7", []) # edit this later
kuf8 = Source("kuf-8", [])
kuf8a = Source("kuf-8a", [])
kuf9 = Source("kuf-9", []) # edit this later
kuf10b = Source("kuf-10b", []) # edit this later
kuf10c = Source("kuf-10c", []) # edit this later
kuf12a = Source("kuf-12a", []) # edit this later

#KBT
kbt4 = Source("kbt-4",[])
kbt4a = Source("kbt-4a",[])
kbt5 = Source("kbt-5",[]) # edit this later
kbt6 = Source("kbt-6", []) 
kbt7 = Source("kbt-7",[])
kbt8 = Source("kbt-8",[])
kbt9 = Source("kbt-9",[]) # edit this later
kbt10 = Source("kbt-10", []) # edit this later
kbt11 = Source("kbt-11", [])
kbt12 = Source("kbt-12",[])

sources = [ka1, ka1ab, ka3, ka8, ka9, ka10, ka11, ka12, kuf7, kuf8, kuf8a, kuf9, kuf10b, kuf10c, kuf12a, kbt4, kbt4a, kbt5, kbt6, kbt7, kbt8, kbt9, kbt10, kbt11, kbt12]

#Intermediate nodes

#KA
ka4 = Intermediate("kuf-4",[])
ka4ab_kuf2 = Intermediate("kuf-4ab_to_kuf-2", []) #edit this later
ka4ab_kuf3 = Intermediate("kuf-4ab_to_kuf-3",[]) #edit this later
ka4ab_kuf3a = Intermediate("ka-4ab_to_kuf-3a", []) #edit this later
ka5a = Intermediate("ka-5a", [])
ka6 = Intermediate("ka-6",[])

#KX
#kx6 = Intermediate("kx-6", []) #disregarded for now

#KUF
kuf2 = Intermediate("kuf-2",[]) # edit this later
kuf3 = Intermediate("kuf-3",[]) # edit this later
kuf3a = Intermediate("kuf-3a",[]) # edit this later
kuf4 = Intermediate("kuf-4",["kbt-5","kbt-9","kbt-10"])
kuf4a_kbt2 = Intermediate("kuf-4a_to_kbt-2", ["kbt-5","kbt-9","kbt-10"])
kuf4a_kbt3 = Intermediate("kuf-4a_to_kbt-3", ["kbt-5","kbt-9","kbt-10"])
kuf4b = Intermediate("kuf-4b", ["kbt-5","kbt-9","kbt-10"])
kuf5 = Intermediate("kuf-5", ["kbt-5","kbt-9","kbt-10"])

#KBT
kbt2 = Intermediate("kbt-2",[]) # edit this later
kbt3 = Intermediate("kbt-3",[]) # edit this later

intermediates = [ka4, ka4ab_kuf2, ka4ab_kuf3, ka4ab_kuf3a, ka5a, ka6, kuf2, kuf3, kuf3a, kuf4, kuf4a_kbt2, kuf4a_kbt3, kuf4b, kuf5, kbt2, kbt3]

route_dict = {}
route_name_list=[]

#distribute(0)
#createXML_hourly_profiled(route_dict, 0)

def sum_indices(dictionary):
    # Initialize a list to store sums for each index
    sums = [0] * 14
    
    # Iterate over the dictionary
    for key, value_list in dictionary.items():
        # Iterate over the list and sum the values at each index
        for i in range(14):
            sums[i] += value_list
    
    return sums

for idx in range(14):
   distribute(idx)
   swank = sum_indices(route_dict)
   print(swank)


   createXML_hourly_profiled(route_dict, idx)
   print(route_dict)
   print(sum(route_dict.values()))

createXML_wholeday_profiled(route_dict)
print


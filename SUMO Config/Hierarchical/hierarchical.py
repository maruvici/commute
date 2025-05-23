import math
import torch
from botorch.models import SingleTaskGP, ModelListGP
from gpytorch.mlls.exact_marginal_log_likelihood import ExactMarginalLogLikelihood
from botorch.fit import fit_gpytorch_mll
from botorch.acquisition.monte_carlo import qExpectedImprovement
from botorch.optim import optimize_acqf
from sumolib import checkBinary  # Checks for the binary in environ vars
import traci
import random
import warnings
import os
import sys
import optparse

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

class Vertex:
    def __init__(self, name, car_num, busy, speed, leng, source, dest):
        self.name = name  # Returns number of cars on path
        self.car_num = car_num  # Returns number of cars on path
        self.busy = busy  # Returns 1 if busy, 0 if free
        self.speed = speed  # Constant showing speed of cars in m/s
        self.leng = leng  # Constant showing length of path in meters
        self.source = source
        self.dest = dest

    def __str__(self):
        return f"{self.name}"

Cars_Passed = 0  # Number of Cars that have exited system
Cars_Passed_Up = 0
Time = float(0.0)  # Current Time

# generation of vertices 
KT = Vertex("KT", 0, 0, 14, 400, 0, 0)  # Katipunan Top Junc
BG = Vertex("BG", 0, 0, 14, 130,  0, 0)  # B.Gonzales Junc
TD = Vertex( "TD",0, 0, 14, 160, 0, 0)  # Thornton Drive Extension Junc
KL2 = Vertex("KL2", 0, 0, 17, 215, 0 , 0)  # Road b/w B.Gonzales and F. Dela Rosa
KR3 = Vertex("KR3", 0, 0, 17, 210, 0, 0)  # Road b/w T.Drive and Univ Road
FDR = Vertex("FDR", 0, 0, 14, 250, 0,0)  # F. Dela Rosa Junc
UR = Vertex("UR", 0, 0, 14, 140, 0,0)  # All 4 mini roads at Ateneo [Univ. Road]
KSX = Vertex("KSX", 0, 0, 17, 900, 0,0)  # Katipunan-Xavierville Soutbound [Left] (Long Katipunan Intermediate )
KNX = Vertex("KSX", 0, 0, 17, 900, 0,0)  # Katipunan-Xavierville Northbound [Right] (Long Katipunan Intermediate )
UTURN = Vertex("UTurn", 0, 0, 14, 10, 0,0) # For U-TURNs
AUR = Vertex("AUR", 0, 0, 14, 230, 0, 0) # Aurora Blvd. Right Side
AUL = Vertex("AUL", 0, 0, 14, 240, 0, 0) # Aurora Blvd. Left Side
KB = Vertex("KB", 0, 0, 14, 170, 0, 0) # Katipunan Bottom Junc

#Routes
""" ---KBT Intersection START--- """
# From (La Vista) [KT]
KT_BG = Vertex("K_Gonza",0, 0, 9, 7, KT, BG)  # to B. Gonzales [kbt-6]
KT_KL2 = Vertex("K_K2S",0, 0, 12, 7, KT, KL2)  # to KUF [kbt-5]
KT_TD = Vertex("KT_TD",0, 0, 14, 7, KT, TD)  # to Thornton Drive [kbt-4]
KT_UTURN = Vertex("K_UTURN",0, 0, 9, 7, KT, UTURN)  # to La Vista [kbt-4a]

# From B. Gonzales (C.Salvador) [BG]
BG_KT = Vertex("BG_KT",0, 0, 5, 7, BG, KT)  # to La Vista [kbt-7]
BG_TD = Vertex("BG_TD",0, 0, 5, 7, BG, TD)  # to Thornton Drive [kbt-8]
BG_KL2 = Vertex("BG_KL2 ",0, 0, 5, 7, BG, KL2)  # to KUF [kbt-9]

# From Thornton Drive (Miriam College) [TD]
TD_KT = Vertex("TD_KT",0, 0, 14, 7, TD, KT)  # to La Vista [kbt-12]
TD_BG = Vertex("TD_BG",0, 0, 9, 7, TD, BG)  # to B. Gonzales [kbt-11]
TD_KL2 = Vertex("TD_KL2",0, 0, 14, 7, TD, KL2)  # to KUF [kbt-10]

# From (Dela Rosa) [KR3]
KR3_KT = Vertex("KR3_KT",0, 0, 12, 7, KR3, KT)  #  to La Vista [kbt-2]
KR3_TD = Vertex("KR3_TD",0, 0, 14, 7, KR3, TD)  # to Thornton Drive [kbt-3]
""" ---KBT Intersection END--- """

""" ---KUF Intersection START--- """
# From (Gonzales St.) [KL2]
KL2_KSX = Vertex("KL2_K3",0, 0, 12, 7, KL2, KSX)  # to Aurora Blvd [kuf-5]
KL2_UR = Vertex("KL2_UR",0, 0, 14, 7, KL2, UR)  # to University Road [kuf-4 , kuf-4b]
KL2_KR3 = Vertex("K2S_K2N",0, 0, 5, 7, KL2, KR3)  # to Gonzales St. [kuf-4a]

# From F. Dela Rosa St. (E. Abada St.) [FDR]
FDR_KR3 = Vertex("FDR_KR3",0, 0, 9, 7, FDR, KR3)  # to Gonzales St. [kuf-7]
FDR_UR = Vertex("FDR_UR",0, 0, 9, 7, FDR, UR)  # to University Road [kuf-8, kuf-8a]
FDR_KSX = Vertex("FDR_K3",0, 0, 9, 7, FDR, KSX)  #  to Aurora Blvd. [kuf-9]

# From University Road (Ateneo Compound) [UR]
UR_KR3 = Vertex("UR_K2N",0, 0, 14, 7, UR, KR3) # to Gonzales St. [kuf-12a]
UR_KSX = Vertex("UR_KSX",0, 0, 14, 7, UR, KSX)  # to Aurora Blvd. [kuf-10c , kuf-10b]

# From (Aurora Blvd.) [KNX]
KNX_KR3 = Vertex("KNX_KR3",0, 0, 12, 7, KNX, KR3)  # to Gonzales St. [kuf-2]
KNX_UR = Vertex("K3_UR",0, 0, 14, 7, KR3, UR)  # to University Road [kuf-3, kuf-3a]
""" ---KUF Intersection END--- """

""" ---KA Intersection START--- """
# From (F. Dela Rosa) [KSX] 
KSX_AUL = Vertex("KSX_AUL",0, 0, 14, 7, KSX, AUL) # to J.P. Rizal [ka-6]
KSX_AUR = Vertex("KSX_AUR",0, 0, 14, 7, KSX, AUR) # to Major Dizon [ka-4]

# From Aurora Blvd. Left (J.P. Rizal) [AUL]
AUL_AUR = Vertex("KSX_AUL",0, 0, 14, 7, AUL, AUR) # to Major Dizon [ka-8]

# From Aurora Blvd. Right (Major Dizon) [AUR]
AUR_KNX = Vertex("AUR_KNX",0, 0, 14, 7, AUR, KNX) # to F. Dela Rosa [ka-12]
AUR_AUL = Vertex("AUR_AUL",0, 0, 14, 7, AUR, AUL) # to Major Dizon [ka-11]
AUR_KB = Vertex("AUR_KB",0, 0, 14, 7, AUR, KB) # to P. Tuazon [ka-10]

# From Katipunan Bottom (P. Tuazon) [KB]
KB_AUL = Vertex("KB_AUL",0, 0, 14, 7, KB, AUL) # to J.P. Rizal [ka-1]
""" ---KUF Intersection END--- """

# split original network list into two, then concatenate
Roads_SubA = [KT_BG, KT_KL2, KT_TD, KT_UTURN, BG_KT, BG_TD, BG_KL2, TD_KT, TD_BG, TD_BG, TD_KL2, KR3_KT, KR3_TD,
        KL2_KSX, KL2_UR, KL2_KR3, FDR_KR3, FDR_UR, FDR_KSX, UR_KR3, UR_KSX, KNX_KR3, KNX_UR]
Roads_SubB = [KSX_AUL, KSX_AUR, AUL_AUR, AUR_KNX, AUR_AUL, AUR_KB, KB_AUL]
Roads = Roads_SubA + Roads_SubB

Entrance_Nodes = [KT, BG, TD, FDR, UR, AUL, AUR, KB]
Exit_Nodes = [KT, BG, TD, UR, AUL, AUR, KB]

def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options

def Set_Busy(Vertex):
    if Vertex.busy == 0:
        Vertex.busy = 1
    else:
        pass

def Set_Stall(Vertex):
    if Vertex.busy == 1:
        Vertex.busy = 0
    else:
        pass

# modified evaluate function for specific subnet
def Evaluate_Busy_Lower(Subnet, Green_Time):
    Restore_Original_State()
    global Cars_Passed
    Cars_Passed = 0
    y = 0
    # select subnet
    if Subnet == 0:
        sub = Roads_SubA
    else:
        sub = Roads_SubB

    for i in range(len(sub)):  # go through all the lanes
        if sub[i].busy == 1:  # if the selected road is busy meaning green light
            y = torch.ceil(Green_Time / (sub[i].leng / sub[i].speed))[-1]# Number of Cars that can pass through in green time
            #print(f"y = {y}")
            if y > sub[i].car_num:
                y = sub[i].car_num
            sub[i].car_num = sub[i].car_num - y  # Remove from road
            Cars_Passed = Cars_Passed + y
        #print(f"Road {Roads[i].name} has {Roads[i].car_num} cars")
    #print(f"Total Cars Passed: {Cars_Passed}")
    global Time

# evaluate function for entire road network
def Evaluate_Busy_Upper(Green_Time):
    Restore_Original_State()
    global Cars_Passed_Up
    Cars_Passed_Up = 0
    y = 0   
    for i in range(len(Roads)):  # go through all the lanes
        if Roads[i].busy == 1:  # if the selected road is busy meaning green light
            y = torch.ceil(Green_Time / (Roads[i].leng / Roads[i].speed))[-1]# Number of Cars that can pass through in green time
            if y > Roads[i].car_num:
                y = Roads[i].car_num
            Cars_Passed_Up = Cars_Passed_Up + y
        #print(f"Road {Roads[i].name} has {Roads[i].car_num} cars")
    global Time

car_num_list = []

def Save_Original_State():
    for i in range(len(Roads)):
        car_num_list.append(Roads[i].car_num)
        
def Restore_Original_State():
    for i in range(len(Roads)):
        Roads[i].car_num = car_num_list[i]

def Phase_1_SubA():
    # kbt ok
    Set_Busy(KT_KL2) #kbt5
    Set_Busy(KR3_KT) #kbt2
    Set_Busy(KR3_TD) #kbt3
    # kuf ok
    Set_Busy(KL2_KSX) #kuf5
    Set_Busy(KNX_KR3) #kuf2
    Set_Busy(KNX_UR) #kuf3-3a

def Phase_1_SubB(): #ka
    Set_Busy(AUR_AUL) #ka11
    Set_Busy(AUL_AUR) #ka8

def Phase_2_SubA():
    # kbt ok
    Set_Busy(BG_KT) #kbt7
    Set_Busy(BG_KL2) #kbt9
    # kuf ok
    Set_Busy(UR_KSX) #kuf10b    
    Set_Busy(FDR_KR3) #kuf7
    Set_Busy(FDR_KSX) #kuf9
    Set_Busy(FDR_UR) #kuf8-8a

def Phase_2_SubB():
    Set_Busy(KSX_AUR) #ka4
    Set_Busy(KB_AUL) #ka1

def Phase_3_SubA():
    # kbt ok
    Set_Busy(KT_UTURN) #kbt4a
    Set_Busy(TD_KL2) #kbt10
    Set_Busy(TD_BG) #kbt11
    Set_Busy(KT_BG) #kbt6
    # kuf ok
    Set_Busy(UR_KSX) #kuf
    Set_Busy(UR_KR3) #kuf

def Phase_3_SubB():
    Set_Busy(AUR_KB) #ka10
    Set_Busy(AUR_AUL) #ka11

def Phase_4_SubA():
    # kbt ok
    Set_Busy(KT_UTURN) #kbt4a
    Set_Busy(KT_KL2) #kbt5
    Set_Busy(KT_TD) #kbt4
    # kuf ok
    Set_Busy(KL2_UR) #kuf4-4b
    Set_Busy(KL2_KR3) #kuf4a
    Set_Busy(KL2_KSX) #kuf5

def Unassert():
    for i in range(len(Roads)):
        Set_Stall(Roads[i])

""" !TO_DO: helper function """
for_helper_phase = "phase 4 - kuf-green"
for_helper_dictionary = {'kt_nb_0': 0,'kt_nb_1': 0,'kt_nb_2': 0,'kt_nb_3': 0,'kt_sb_0': 0,'kt_sb_1': 0,'kt_sb_2': 0,'kt_sb_3': 0,'kt_sb_4': 0,'thornton_drive-upper_in_0': 0,'thornton_drive-out_0': 0,
        'b.gonzales-road-out_0': 0,'b.gonzales-road-in_0': 0,'kr3_nb_0': 0,'kr3_nb_1': 0,'kr3_nb_2': 0,'kr3_nb_3': 0,   'kr4_nb_0': 0,'kr4_nb_1': 0,'kr4_nb_2': 0,'kl2_sb_0': 0,'kl2_sb_1': 0,'kl2_sb_2': 0,'kl2_sb_3': 0,'kl2_sb_4': 0,'univ_road-upper_out_0': 0,'univ_road-upper_in_0': 0,'univ_road-lower_out_0': 0,'univ_road-lower_in_0': 0,'f.dela_rosa-road_1': 0,'f.dela_rosa-road_0': 0,'ksx_l3_sb_0': 0,'ksx_l3_sb_1': 0,'ksx_l3_sb_2': 0,
        'ksx_l3_sb_3': 0,'ksx_l3_sb_4': 0,'ksx_l4_sb_0': 0,'ksx_l4_sb_1': 0,'ksx_l5_sb_0': 0,'ksx_l5_sb_1': 0,'ksx_l5_sb_2': 0,'knx_r5_nb_0': 0,'knx_r5_nb_1': 0,'knx_r5_nb_2': 0,'knx_r6_nb_0': 0,'knx_r6_nb_1': 0,'katip-aurora-curve_0': 0,'aul_out_0': 0,'aul_out_1': 0,'aul_out_2': 0,'aul_out_3': 0,'aul_in_0': 0,'aul_in_1': 0,'aul_in_2': 0,'aul_in_3': 0,'aur_out_0': 0,'aur_out_1': 0,'aur_out_2': 0,'aur_out_3': 0, 'aur_in_0': 0,'aur_in_1': 0,'aur_in_2': 0,'aur_in_3': 0,'kb_sb_0': 0,'kb_sb_1': 0,'kb_nb_0': 0}

past_phases = [0, 0, 0, 0, 0, 0, 0] # phases 1-4 for KUF-KBT, phases 1-3 for KA
def helper_function(phase_data,diksyonaryo):
    global past_phases
    print(phase_data)
    phase = phase_data.split(" - ")[0]
    intersection_type = phase_data.split(" - ")[1]

    if intersection_type == "kuf":
        intersec = 0 # for KUF, KBT
    else:
        intersec = 1 # for KA
    #print(f"PHASE IS COLLECTED: " + str(phase))
    #print(f"INTERSECTION IS COLLECTED: " + str(intersection_type) + " WITH INTERSEC OF: " + str(intersec))

    #Mid Katipunan to Top Katipunan
    KR3_KT.car_num  = diksyonaryo["kr3_nb_1_count"]
    KR3_KT.car_num += diksyonaryo["kr3_nb_2_count"]
    KR3_KT.car_num += diksyonaryo["kr3_nb_3_count"]
    KR3_KT.car_num += diksyonaryo["kr4_nb_1_count"]
    KR3_KT.car_num += diksyonaryo["kr4_nb_2_count"]
    KR3_KT.car_num += int(5*(int(diksyonaryo["kr3_nb_0_count"]/6)))
    KR3_KT.car_num += int(5*(int(diksyonaryo["kr4_nb_0_count"]/6)))
    # Mid Katipunan to Thornton
    KR3_TD.car_num += int(diksyonaryo["kr3_nb_0_count"]/6)
    KR3_TD.car_num += int(diksyonaryo["kr4_nb_0_count"]/6)
    # Top Katipunan to B. Gonzales
    KT_KL2.car_num = diksyonaryo["kt_sb_0_count"]
    #Top Katipunan to Mid Katipunan
    KT_KL2.car_num = diksyonaryo["kt_sb_1_count"]
    KT_KL2.car_num += diksyonaryo["kt_sb_2_count"]
    KT_KL2.car_num += diksyonaryo["kt_sb_3_count"]
    # Top Katipunan U-turn
    KT_UTURN.car_num  = int(diksyonaryo["kt_sb_4_count"] * 0.75)
    KT_TD.car_num = int(diksyonaryo["kt_sb_4_count"] * 0.25)
    
    #IMPROVE DISTRIBUTION
    
    # Thornton Drive (Divide divide)
    divide_thornton = int(diksyonaryo["thornton_drive-upper_in_0_count"] / 2)
    mod = diksyonaryo["thornton_drive-upper_in_0_count"] % 2
    TD_KT.car_num = divide_thornton
    TD_KL2.car_num = divide_thornton
    random_number = random.randint(1, 2)
    if random_number == 1:
        TD_KT.car_num += mod
    else:
        TD_KL2.car_num  += mod

    #B.Gonzales to Mid Katipunan
    ####B. Gonzales Divide2x
    # already based on demand
    going_top = int(diksyonaryo["b.gonzales-road-in_0_count"] * 0.9)
    mod = int(diksyonaryo["b.gonzales-road-in_0_count"] * 0.1) % 2
    BG_KT.car_num = going_top
    random_number = random.randint(1, 2)
    if random_number == 1:
        # B.Gonzales to Mid Katipunan
        BG_KL2.car_num += mod
    else:
        # B.Gonzales to Thornton Drive
        BG_TD.car_num += mod

    # From Mid-Top Katipunan to Mid-Bottom Katipunan
    KL2_KSX.car_num  = diksyonaryo["kl2_sb_0_count"]
    KL2_KSX.car_num += diksyonaryo["kl2_sb_1_count"]
    KL2_KSX.car_num += diksyonaryo["kl2_sb_2_count"]

    # From Mid-Top Katipunan to University Drive
    KL2_UR.car_num = diksyonaryo["kl2_sb_3_count"]
    # Mid-Top Katipunan U-turn
    KL2_KR3.car_num = diksyonaryo["kl2_sb_4_count"]
    
    ########University Road Upper Out Divide2x
    divide_urduo = int(diksyonaryo["univ_road-upper_in_0_count"] / 2)
    mod = diksyonaryo["univ_road-upper_in_0_count"] % 2
    UR_KR3.car_num = divide_urduo
    UR_KSX.car_num = divide_urduo
    random_number = random.randint(1, 2)
    if random_number == 1:
        # University Road Upper Out to Mid-Top Katipunan
        UR_KR3.car_num += mod
    else:
        # University Road Upper Out to Mid-Bottom Katipunan
        UR_KSX.car_num  += mod
    # University Road Lower Out
    UR_KSX.car_num += diksyonaryo["univ_road-lower_in_0_count"]

    # F.delaRosa to Mid-Top Katip
    FDR_KR3.car_num = diksyonaryo["f.dela_rosa-road_1_count"]
    ######## F.delaRosa Divide2x
    divide_frosa = int(diksyonaryo["f.dela_rosa-road_0_count"] / 2)
    mod = diksyonaryo["f.dela_rosa-road_0_count"] % 2
    FDR_UR.car_num = divide_frosa
    FDR_KSX.car_num = divide_frosa
    random_number = random.randint(1, 2)
    if random_number == 1:
        # F.delaRosa to University Road
        FDR_UR.car_num += mod
    else:
        # F.delaRosa to Bottom Katipunan
        FDR_KSX.car_num += mod
    #did not include these v since exit node
    #'katip_b_sb_0_count': 4, 'katip_b_sb_1_count': 3, 'katip_b_sb_2_count': 7, 'katip_b_sb_3_count': 0, 'katip_b_sb_4_count': 0,

    # Mid- Bottom Katipunan to Mid-Top Katipunan
    KNX_KR3.car_num = diksyonaryo["knx_r5_nb_1_count"]
    KNX_KR3.car_num += diksyonaryo["knx_r5_nb_2_count"]
    KNX_KR3.car_num += int(diksyonaryo["knx_r5_nb_0_count"] * 0.7)
    # Mid - Bottom Katipunan to UR
    KNX_UR.car_num = int(diksyonaryo["knx_r5_nb_0_count"] * 0.3)

    #Mid - Bottom Katipunan to Aurora Left
    KSX_AUL.car_num = diksyonaryo["ksx_l5_sb_0_count"]

    #Mid - Bottom Katipunan to Aurora Right
    KSX_AUR.car_num = diksyonaryo["ksx_l5_sb_1_count"]
    KSX_AUR.car_num += diksyonaryo["ksx_l5_sb_2_count"]

    #Aurora Right Divide
    divide_aur_0 = int(diksyonaryo["aur_in_0_count"] / 2)
    AUR_AUL.car_num = divide_aur_0
    AUR_KNX.car_num = divide_aur_0

    AUR_AUL.car_num += diksyonaryo["aur_in_1_count"]
    divide_aur_2= int( (diksyonaryo["aur_in_2_count"] + diksyonaryo["aur_in_3_count"]) /2)
    AUR_KB.car_num = divide_aur_2
    AUR_AUL.car_num += divide_aur_2

    #From AUL 
    AUL_AUR.car_num = diksyonaryo["aul_in_0_count"]
    AUL_AUR.car_num += diksyonaryo["aul_in_1_count"]
    AUL_AUR.car_num += diksyonaryo["aul_in_2_count"]
    AUL_AUR.car_num += diksyonaryo["aul_in_3_count"]

    #From KB 
    KB_AUL.car_num = diksyonaryo["kb_nb_0_count"]
    KB_AUL.car_num += diksyonaryo["kb_nb_1_count"]

    Unassert()  # This happens only once
    x = int(25) #This is the minimum green time
    car_num_list.clear()
    Save_Original_State()

    #print("[Vehicles in Network]")
    #for r in Roads:
        #print(f"Vehicles in {r.name}: {r.car_num}") 

    # Upper Level Controller
    # get phases of KUF-KBT and KA, assert relevant roads
    kuf_phase_temp = traci.trafficlight.getPhase("kuf")
    if kuf_phase_temp < 3:
        Phase_1_SubA()
    elif kuf_phase_temp < 6:
        Phase_2_SubA()
    elif kuf_phase_temp < 9:
        Phase_3_SubA()
    else:
        Phase_4_SubA()

    ka_phase_temp = traci.trafficlight.getPhase("ka")
    if ka_phase_temp < 3:
        Phase_1_SubB()
    elif ka_phase_temp < 6:
        Phase_2_SubB()
    else:
        Phase_3_SubB()
    
    # run optimization for upper layer, get tentative greentime
    print(f"Running upper level optimization!")

    upper_gt_list = []
    upper_fr_list = []

    init_gt_upper, init_fr_upper, best_fr_upper = generate_initial_data(10)
    upper_bnds = torch.tensor([[25.0], [180.0]], dtype=torch.float32)
    for i in range(3):
        print(f"Number of optimization run: {i+1}")
        # run Bayesian optimization to get greentime candidates
        new_gt_upper = optimize_upper(init_gt_upper, init_fr_upper, best_fr_upper, upper_bnds, 1)
        # append new candidates to original list of greentime candidates
        init_gt_upper = torch.cat([init_gt_upper, new_gt_upper])
        # calculate flowrates from the list of greentime candidates
        init_fr_upper = target_upper(init_gt_upper).squeeze(-1)
        # get best flowrate
        best_fr_upper = init_fr_upper.max().item()
        index_of_best = int(torch.isclose(init_fr_upper.max().float(), new_gt_upper))
        new_best = torch.index_select(new_gt_upper, 0, torch.LongTensor([index_of_best]))
        print(f"Upper-level greentime: {new_best}")
        print(f"Upper-level flowrate: {best_fr_upper}")
        upper_gt_list.append(torch.tensor([[new_best]]))
        upper_fr_list.append(torch.tensor([[best_fr_upper]]))

    # create data to use as parameters for lower-level optimization
    upper_gt = torch.cat(upper_gt_list).repeat(4, 1)
    upper_fr = torch.cat(upper_fr_list).repeat(4, 1)
    best_fr = upper_fr.max().item()
    
    # unassert layers
    Unassert()

    #print("[AFTER UPPER-LEVEL OPTIMIZATION]")
    #for r in Roads:
        #print(f"Vehicles in {r.name}: {r.car_num}") 

    if phase == "phase 1":

        if intersec == 0: # KUF-KBT
            Phase_1_SubA()
            print("P1 KUF-KBT")
            # print roads which will be affected
            for i in range(len(Roads)):
                if Roads[i].busy == 1: 
                    print(f"Number of cars in", Roads[i].name, ":", Roads[i].car_num)
            # if number of vehicles in road less than some value, set to minimum greentime 25s
            if (KT_KL2.car_num <= 20 and KR3_KT.car_num <= 20 and KR3_TD.car_num <= 20 and KL2_KSX.car_num <= 20 and KNX_KR3.car_num <= 40 and KNX_UR.car_num <= 20):
                past_phases[0] = x
                return x
            # run optimizer
            past_phases[0] = optloop_KUFBT_1(upper_gt, upper_fr, best_fr, 3)
            # if calculated greentime is less than set value 75s, automatically set to 75s
            if past_phases[0] < 75:
                past_phases[0] = 75
            return (past_phases[0])
        
        else: # KA
            Phase_1_SubB()
            print("P1 KA")
            # print roads which will be affected
            for i in range(len(Roads)):
                if Roads[i].busy == 1: 
                    print(f"Number of cars in", Roads[i].name, ":", Roads[i].car_num)
            # if number of vehicles in road less than some value, set to minimum greentime 25s
            if (AUR_AUL.car_num <= 15 and AUL_AUR.car_num <= 15):
                past_phases[4] = x
                return x
            # insert other conditions here
            
            # run optimizer
            past_phases[4] = optloop_KA_1(upper_gt, upper_fr, best_fr, 3)
            return (past_phases[4])

    if phase == "phase 2":

        if intersec == 0: # KUF-KBT
            Phase_2_SubA()
            print("P2 KUF-KBT")
            # print roads which will be affected
            for i in range(len(Roads)):
                if Roads[i].busy == 1: 
                    print(f"Number of cars in", Roads[i].name, ":", Roads[i].car_num)
            # if all other KUF-BT phases are minimum, set phase 2 greentime to 70s - why?
            if (past_phases[0] == 25 and past_phases[2] == 25 and past_phases[3] == 25):
                past_phases[1] = 70
                return past_phases[1]
            # if number of vehicles in road less than some value, set to minimum greentime 25s
            if (BG_KT.car_num <= 12) and (BG_KL2.car_num <= 12) and (UR_KSX.car_num <= 12) and (FDR_KR3.car_num <= 12) and (FDR_KSX.car_num <= 12) and (FDR_UR.car_num <= 12):                
                past_phases[1] = x
                return x
            # run optimizer
            past_phases[1] = optloop_KUFBT_2(upper_gt, upper_fr, best_fr, 3)
            return (past_phases[1])
        
        else: # KA
            Phase_2_SubB()
            print("P2 KA")
            # print roads which will be affected
            for i in range(len(Roads)):
                if Roads[i].busy == 1: 
                    print(f"Number of cars in", Roads[i].name, ":", Roads[i].car_num)
            # insert other conditions here

            # if number of vehicles in road less than some value, set to minimum greentime 25s
            if (KSX_AUR.car_num <= 15 and KB_AUL.car_num <= 15):
                past_phases[5] = x
                return x
            # run optimizer
            past_phases[5] = optloop_KA_2(upper_gt, upper_fr, best_fr, 3)
            return (past_phases[5])
        
    if phase == "phase 3":
        
        if intersec == 0: # KUF-KBT
            Phase_3_SubA()
            print("P3 KUF-KBT")
            # print roads which will be affected
            for i in range(len(Roads)):
                if Roads[i].busy == 1: 
                    print(f"Number of cars in", Roads[i].name, ":", Roads[i].car_num)
            # if all other KUF-BT phases are minimum, set phase 3 greentime to 75s - why?
            if (past_phases[0] == 25 and past_phases[1] == 25 and past_phases[3] == 25):
                past_phases[2] = 75
                return past_phases[2]
            # if number of vehicles in road less than some value, set to minimum greentime 25s
            if (TD_KL2.car_num <= 15 and TD_KT.car_num <= 15 and UR_KSX.car_num <= 15 and UR_KR3.car_num <= 15 and KT_BG.car_num <= 15):
                past_phases[2] = x
                return x
            # run optimizer
            past_phases[2] = optloop_KUFBT_3(upper_gt, upper_fr, best_fr, 3)
            return (past_phases[2])
        
        else: # KA
            Phase_3_SubB()
            print("P3 KA")
            # print roads which will be affected
            for i in range(len(Roads)):
                if Roads[i].busy == 1: 
                    print(f"Number of cars in", Roads[i].name, ":", Roads[i].car_num)
            # insert other conditions here

            # if number of vehicles in road less than some value, set to minimum greentime 25s
            if (AUR_KB.car_num <= 15 and AUR_AUL.car_num <= 15):
                past_phases[6] = x
                return x
            # run optimizer
            past_phases[6] = optloop_KA_3(upper_gt, upper_fr, best_fr, 3)
            return (past_phases[6])
        
    elif phase == "phase 4": # KUF-KBT only
        Phase_4_SubA()
        print("P4 KUF-KBT")
        # print roads which will be affected
        for i in range(len(Roads)):
            if Roads[i].busy == 1: 
                print(f"Number of cars in", Roads[i].name, ":", Roads[i].car_num)
        # if all other KUF-BT phases are minimum, set phase 3 greentime to 70s - why?
        if (past_phases[0] == 25 and past_phases[1] == 25 and past_phases[2] == 25):
            return int(70)
        # if number of vehicles in road less than some value, set to minimum greentime 25s
        if (KT_UTURN.car_num <= 25 and KT_KL2.car_num <= 100 and KT_TD.car_num <= 25 and KL2_UR.car_num <= 25 and KL2_KR3.car_num <= 25 and KL2_KSX.car_num <= 25):
            past_phases[3] = x
            return x
        past_phases[3] = optloop_KUFBT_4(upper_gt, upper_fr, best_fr, 3)
        return (past_phases[3])

# upper level controller target function
def target_upper(candidates):
    # Standardize the input data
    mu = candidates.mean()
    sigma = candidates.std()
    std_candidates = (candidates - mu) / sigma
    Evaluate_Busy_Upper(candidates)
    global Cars_Passed_Up
    try:
        flow_rate = (Cars_Passed_Up.item() / std_candidates) + (std_candidates/100)
    except:
        flow_rate = (Cars_Passed_Up / std_candidates) + (std_candidates/100)
    #print("Total Flow Rate:" + str(flow_rate))
    Cars_Passed_Up = 0
    return flow_rate.unsqueeze(-1)

# lower level controller target function
def target_lower(subnet, train_greentime):
    # Standardize the input data
    mu = train_greentime.mean()
    sigma = train_greentime.std()
    std_train_greentime = (train_greentime - mu) / sigma
    #print(train_greentime)
    #print(f"mu: {mu} \nsigma: {sigma} \nstd: {std_train_greentime}")
    Evaluate_Busy_Lower(subnet, train_greentime)
    global Cars_Passed
    try:
        flow_rate = (Cars_Passed.item() / std_train_greentime) + (std_train_greentime/100)
    except:
        flow_rate = (Cars_Passed / std_train_greentime) + (std_train_greentime/100)
    #print("Total Flow Rate:" + str(flow_rate))
    Cars_Passed = 0
    return flow_rate.unsqueeze(-1)

def optimize_upper(init_greentime, init_flowrate, best_flowrate, bnds, npts):
    single_model = SingleTaskGP(init_greentime, init_flowrate)
    mll = ExactMarginalLogLikelihood(single_model.likelihood, single_model)
    fit_gpytorch_mll(mll)
    EI = qExpectedImprovement(single_model, best_flowrate)
    candidates, _ = optimize_acqf(
        acq_function=EI,
        bounds=bnds,  # bounds
        q=npts,  # Number of points we times we want to be suggested
        num_restarts=50,  # Increase the number of restarts
        raw_samples=256,  # Increase the number of raw samples
        options={"batch_limit": 5, "maxiter": 50}
    )
    return candidates

# adapted from Smartlight
def optimize_function(init_greentime, init_flowrate, best_flowrate, bnds, npts):
    single_model = SingleTaskGP(init_greentime, init_flowrate)
    mll = ExactMarginalLogLikelihood(single_model.likelihood, single_model)
    fit_gpytorch_mll(mll)
    EI = qExpectedImprovement(single_model, best_flowrate)
    candidates, _ = optimize_acqf(
        acq_function=EI,
        bounds=bnds,  # bounds
        q=npts,  # Number of points we times we want to be suggested
        num_restarts=50,  # Increase the number of restarts - 500
        raw_samples=256,  # Increase the number of raw samples - 1024
        options={"batch_limit": 5, "maxiter": 100} # 200 max iter
    )
    return candidates

def generate_initial_data(n):  # This function generates the base data needed
    train_greentime = torch.rand((n, 1), dtype=torch.float64)  # for bayesian optimization
    exact_obj = target_upper(train_greentime)
    best_flowrate = exact_obj.max().item()
    return train_greentime, exact_obj.squeeze(-1), best_flowrate

def optloop_KUFBT_1(upper_gt, upper_fr, best_fr, loops):
    print(f"Optimizing greentime for KUF-KBT Phase 1!")
    # get initial data from inputs
    init_greentime, init_flowrate, best_flowrate = upper_gt, upper_fr, best_fr
    # greentime bounds 
    bnds = torch.tensor([[85.0], [160.0]], dtype=torch.float32)
    #optimization loop
    for i in range(loops):
        print(f"Number of optimization run: {i+1}")
        # run Bayesian optimization to get greentime candidates
        new_candidates = optimize_function(init_greentime, init_flowrate, best_flowrate, bnds, 1)
        # append new candidates to original list of greentime candidates
        init_greentime = torch.cat([init_greentime, new_candidates])
        # calculate flowrates from the list of greentime candidates
        init_flowrate = target_lower(0, init_greentime).squeeze(-1)
        # get best flowrate
        best_flowrate = init_flowrate.max().item()
        index_of_best = int(torch.isclose(init_flowrate.max().float(), new_candidates))
        new_best = torch.index_select(new_candidates, 0, torch.LongTensor([index_of_best]))
        print(f"The new best Green Time Candidate is: {new_best}")
        print(f"Best Flow Rate Is: {best_flowrate}")
    car_num_list.clear()
    return int(new_best)

def optloop_KUFBT_2(upper_gt, upper_fr, best_fr, loops):
    print(f"Optimizing greentime for KUF-KBT Phase 2!")
    # get initial data from inputs
    init_greentime, init_flowrate, best_flowrate = upper_gt, upper_fr, best_fr
    # greentime bounds 
    bnds = torch.tensor([[28.0], [65.0]], dtype=torch.float32)
    #optimization loop
    for i in range(loops):
        print(f"Number of optimization run: {i+1}")
        # run Bayesian optimization to get greentime candidates
        new_candidates = optimize_function(init_greentime, init_flowrate, best_flowrate, bnds, 1)
        # append new candidates to original list of greentime candidates
        init_greentime = torch.cat([init_greentime, new_candidates])
        # calculate flowrates from the list of greentime candidates
        init_flowrate = target_lower(0, init_greentime).squeeze(-1)
        # get best flowrate
        best_flowrate = init_flowrate.max().item()
        index_of_best = int(torch.isclose(init_flowrate.max().float(), new_candidates))
        new_best = torch.index_select(new_candidates, 0, torch.LongTensor([index_of_best]))
        print(f"The new best Green Time Candidate is: {new_best}")
        print(f"Best Flow Rate Is: {best_flowrate}")
    car_num_list.clear()
    return int(new_best)

def optloop_KUFBT_3(upper_gt, upper_fr, best_fr, loops):
    print(f"Optimizing greentime for KUF-KBT Phase 3!")
    # get initial data from inputs
    init_greentime, init_flowrate, best_flowrate = upper_gt, upper_fr, best_fr
    # greentime bounds 
    bnds = torch.tensor([[28.0], [60.0]], dtype=torch.float32)
    #optimization loop
    for i in range(loops):
        print(f"Number of optimization run: {i+1}")
        # run Bayesian optimization to get greentime candidates
        new_candidates = optimize_function(init_greentime, init_flowrate, best_flowrate, bnds, 1)
        # append new candidates to original list of greentime candidates
        init_greentime = torch.cat([init_greentime, new_candidates])
        # calculate flowrates from the list of greentime candidates
        init_flowrate = target_lower(0, init_greentime).squeeze(-1)
        # get best flowrate
        best_flowrate = init_flowrate.max().item()
        index_of_best = int(torch.isclose(init_flowrate.max().float(), new_candidates))
        new_best = torch.index_select(new_candidates, 0, torch.LongTensor([index_of_best]))
        print(f"The new best Green Time Candidate is: {new_best}")
        print(f"Best Flow Rate Is: {best_flowrate}")
    car_num_list.clear()
    return int(new_best)

def optloop_KUFBT_4(upper_gt, upper_fr, best_fr, loops):
    print(f"Optimizing greentime for KUF-KBT Phase 4!")
    # get initial data from inputs
    init_greentime, init_flowrate, best_flowrate = upper_gt, upper_fr, best_fr
    # greentime bounds 
    bnds = torch.tensor([[15.0], [60.0]], dtype=torch.float32)
    #optimization loop
    for i in range(loops):
        print(f"Number of optimization run: {i+1}")
        # run Bayesian optimization to get greentime candidates
        new_candidates = optimize_function(init_greentime, init_flowrate, best_flowrate, bnds, 1)
        # append new candidates to original list of greentime candidates
        init_greentime = torch.cat([init_greentime, new_candidates])
        # calculate flowrates from the list of greentime candidates
        init_flowrate = target_lower(0, init_greentime).squeeze(-1)
        # get best flowrate
        best_flowrate = init_flowrate.max().item()
        index_of_best = int(torch.isclose(init_flowrate.max().float(), new_candidates))
        new_best = torch.index_select(new_candidates, 0, torch.LongTensor([index_of_best]))
        print(f"The new best Green Time Candidate is: {new_best}")
        print(f"Best Flow Rate Is: {best_flowrate}")
    car_num_list.clear()
    return int(new_best)

def optloop_KA_1(upper_gt, upper_fr, best_fr, loops):
    print(f"Optimizing greentime for KA Phase 1!")
    # get initial data from inputs
    init_greentime, init_flowrate, best_flowrate = upper_gt, upper_fr, best_fr
    # greentime bounds 
    bnds = torch.tensor([[30.0], [90.0]], dtype=torch.float32) # base is 60s; change to 0.5x and 1.5x
    #optimization loop
    for i in range(loops):
        print(f"Number of optimization run: {i+1}")
        # run Bayesian optimization to get greentime candidates
        new_candidates = optimize_function(init_greentime, init_flowrate, best_flowrate, bnds, 1)
        # append new candidates to original list of greentime candidates
        init_greentime = torch.cat([init_greentime, new_candidates])
        # calculate flowrates from the list of greentime candidates
        init_flowrate = target_lower(1, init_greentime).squeeze(-1)
        # get best flowrate
        best_flowrate = init_flowrate.max().item()
        index_of_best = int(torch.isclose(init_flowrate.max().float(), new_candidates))
        new_best = torch.index_select(new_candidates, 0, torch.LongTensor([index_of_best]))
        print(f"The new best Green Time Candidate is: {new_best}")
        print(f"Best Flow Rate Is: {best_flowrate}")
    car_num_list.clear()
    return int(new_best)

def optloop_KA_2(upper_gt, upper_fr, best_fr, loops):
    print(f"Optimizing greentime for KA Phase 2!")
    # get initial data from inputs
    init_greentime, init_flowrate, best_flowrate = upper_gt, upper_fr, best_fr
    # greentime bounds 
    bnds = torch.tensor([[25.0], [75.0]], dtype=torch.float32) # base is 50s; change to 0.5x and 1.5x
    #optimization loop
    for i in range(loops):
        print(f"Number of optimization run: {i+1}")
        # run Bayesian optimization to get greentime candidates
        new_candidates = optimize_function(init_greentime, init_flowrate, best_flowrate, bnds, 1)
        # append new candidates to original list of greentime candidates
        init_greentime = torch.cat([init_greentime, new_candidates])
        # calculate flowrates from the list of greentime candidates
        init_flowrate = target_lower(1, init_greentime).squeeze(-1)
        # get best flowrate
        best_flowrate = init_flowrate.max().item()
        index_of_best = int(torch.isclose(init_flowrate.max().float(), new_candidates))
        new_best = torch.index_select(new_candidates, 0, torch.LongTensor([index_of_best]))
        print(f"The new best Green Time Candidate is: {new_best}")
        print(f"Best Flow Rate Is: {best_flowrate}")
    car_num_list.clear()
    return int(new_best)

def optloop_KA_3(upper_gt, upper_fr, best_fr, loops):
    print(f"Optimizing greentime for KA Phase 3!")
    # get initial data from inputs
    init_greentime, init_flowrate, best_flowrate = upper_gt, upper_fr, best_fr
    # greentime bounds 
    bnds = torch.tensor([[25.0], [75.0]], dtype=torch.float32) # base is 50s; change to 0.5x and 1.5x
    #optimization loop
    for i in range(loops):
        print(f"Number of optimization run: {i+1}")
        # run Bayesian optimization to get greentime candidates
        new_candidates = optimize_function(init_greentime, init_flowrate, best_flowrate, bnds, 1)
        # append new candidates to original list of greentime candidates
        init_greentime = torch.cat([init_greentime, new_candidates])
        # calculate flowrates from the list of greentime candidates
        init_flowrate = target_lower(1, init_greentime).squeeze(-1)
        # get best flowrate
        best_flowrate = init_flowrate.max().item()
        index_of_best = int(torch.isclose(init_flowrate.max().float(), new_candidates))
        new_best = torch.index_select(new_candidates, 0, torch.LongTensor([index_of_best]))
        print(f"The new best Green Time Candidate is: {new_best}")
        print(f"Best Flow Rate Is: {best_flowrate}")
    car_num_list.clear()
    return int(new_best)

def getLaneParams():
    edge_list = traci.edge.getIDList()
    lane_list = traci.lane.getIDList()
    output_list = []
    road_list = {
        #katip_t_nb -> kt_nb | R2 = R2+ R3
        "kt_nb": ['R1', 'R2'], 
        #katip_t_sb -> kt_sb 
        "kt_sb": ['L1'], 
        #thornton-drive-extension-outward -> thornton_drive-extension-in | thornton-drive-upper-out -> thornton_drive-lower_in        
        "td_nb": ['thornton_drive-extension-in', 'thornton_drive-lower_in'], #to-fix interchange upper_in and lower_in for td in network
        #thornton-drive-lower-out -> thornton_drive-upper_in
        "td_sb": ['thornton_drive-extension-in', 'thornton_drive-upper_in'],
        #thornton-drive-in -> thornton_drive-out | thornton-drive-extension-towards -> thornton_drive-extension-out
        "td_in": ['thornton_drive-out', 'thornton_drive-extension-out'],
        # split into bg_in and bg_out
        "bg_in": ['b.gonzales-road-in'],
        "bg_out": ['b.gonzales-road-out'],
        # katip_m_nb -> kr3_nb | R4 = R5 + R6
        "kr3_nb": ['R3', 'R4'],
        # katip_m_sb -> kl2_sb | L2 = L2 + L3 + L4 + L5 + L6
        "kl2_sb": ['L2'],
        # out and in are interchanged in SL, in = going in the network | out = exiting the network
        "ur_t_in": ['univ_road-upper_in'],
        "ur_t_out": ['univ_road-upper_out'],
        "ur_b_out": ['univ_road-lower_out'],
        "ur_b_in": ['univ_road-lower_in'],
        #extension are non existent in network
        "fdr": ['f.dela_rosa-road'],
        #katip_b_nb -> knx_nb | R5(3) + R6(2) = R7(3) 
        "knx_nb": ['R5', 'R6'],
        # L3(5) + L4(2) + L5(3) =  L7, L8, L9, L10, L11, L12
        "ksx_sb": ['L3', 'L4', 'L5'],
        #Note: (no.of lanes of the road)
        "aul_curve_out" : ['katip-aurora-curve', 'aurora-upper_out'],
        "aul_out" : ['aurora-mid_int', 'aurora-upper_out'],
        "aul_in" : ['aurora-lower_in'],
        "aur_out" :['aurora-lower_out'],
        'aur_in' : ['aurora-upper_in'],
        "kb_sb" : ['L6', 'L7'],
        "kb_nb" : ['R7']

    }
    # road_position_direction_lanenum : smaller lanes part of that lane
    lane_dict = {
        "kt_nb_0": ['R1_0'], "kt_nb_1": ['R1_1'], "kt_nb_2": ['R1_2'], "kt_nb_3": ['R1_3'],
        "kt_sb_0": ['L1_0'], "kt_sb_1": ['L1_1'], "kt_sb_2": ['L1_2'], "kt_sb_3": ['L1_3'], "kt_sb_4": ['L1_4'],
        #thornton-drive-lower-out_0 -> thornton_drive-upper_in_0
        "thornton_drive-upper_in_0": ['thornton_drive-upper_in_0'],
        # thornton-drive-in_0 - > thornton_drive-out_0
        "thornton_drive-out_0": ['thornton_drive-out_0'],
        "b.gonzales-road-out_0" : ['b.gonzales-road-out_0'], "b.gonzales-road-in_0" : ['b.gonzales-road-in_0'],
        "kr3_nb_0": ['R3_0'], "kr3_nb_1": ['R3_1'], "kr3_nb_2": ['R3_2'], "kr3_nb_3": ['R3_3'],   
        "kr4_nb_0": ['R4_0'], "kr4_nb_1": ['R4_1'], "kr4_nb_2": ['R4_2'],
        "kl2_sb_0": ['L2_0'], "kl2_sb_1": ['L2_1'], "kl2_sb_2": ['L2_2'], "kl2_sb_3": ['L2_3'], "kl2_sb_4": ['L2_4'],
        #Note: out and in is interchange in SL
        "univ_road-upper_out_0" : ['univ_road-upper_out_0'], "univ_road-upper_in_0" : ['univ_road-upper_in_0'],
        "univ_road-lower_out_0" : ['univ_road-lower_out_0'], "univ_road-lower_in_0" : ['univ_road-lower_in_0'],
        "f.dela_rosa-road_1" : ['f.dela_rosa-road_1'], "f.dela_rosa-road_0" : ['f.dela_rosa-road_0'],
        "ksx_l3_sb_0": ['L3_0'], "ksx_l3_sb_1": ['L3_1'], "ksx_l3_sb_2": ['L3_2'], "ksx_l3_sb_3": ['L3_3'], "ksx_l3_sb_4": ['L3_4'],
        "ksx_l4_sb_0": ['L4_0'], "ksx_l4_sb_1": ['L4_1'],
        "ksx_l5_sb_0": ['L5_0'], "ksx_l5_sb_1": ['L5_1'], "ksx_l5_sb_2": ['L5_2'],
        "knx_r5_nb_0": ['R5_0'], "knx_r5_nb_1": ['R5_1'], "knx_r5_nb_2": ['R5_2'],
        "knx_r6_nb_0": ['R6_0'], "knx_r6_nb_1": ['R6_1'],
        "katip-aurora-curve_0" : ['katip-aurora-curve_0'],
        "aul_out_0" : ['aurora-mid_int_0', 'aurora-upper_out_0'], "aul_out_1" : ['aurora-mid_int_1', 'aurora-upper_out_1'],
        "aul_out_2" : ['aurora-mid_int_2', 'aurora-upper_out_2'], "aul_out_3" : ['aurora-mid_int_3', 'aurora-upper_out_3'],
        "aul_in_0" : ['aurora-lower_in_0'], "aul_in_1" : ['aurora-lower_in_1'], "aul_in_2" : ['aurora-lower_in_2'], "aul_in_3" : ['aurora-lower_in_3'],
        "aur_out_0" :['aurora-lower_out_0'], "aur_out_1" :['aurora-lower_out_1'], "aur_out_2" :['aurora-lower_out_2'], "aur_out_3" :['aurora-lower_out_3'],
        "aur_in_0" : ['aurora-upper_in_0'], "aur_in_1" : ['aurora-upper_in_1'], "aur_in_2" : ['aurora-upper_in_2'], "aur_in_3": ['aurora-upper_in_3'],
        "kb_sb_0" : ['L6_0', 'L7_0'], "kb_sb_1" : ['L6_1', 'L7_1'],
        "kb_nb_0" : ['R7_0'], "kb_nb_1" : ['R7_1']
    }
    lane_veh_count_dict = {key + "_count": 0 for key in lane_dict}
    
    for lane in lane_list:
        lane_veh_count = traci.lane.getLastStepHaltingNumber(lane)
        for key, value in lane_dict.items():
            if lane in value:
                lane_veh_count_dict[str(key + "_count")] += lane_veh_count
                break
    #print(lane_veh_count_dict)
    
    return lane_veh_count_dict

# UPDATE!!!
def run():
    step = 0

    old_kuf_phase = 0
    old_kbt_phase = 0
    old_ka_phase = 0

    while traci.simulation.getMinExpectedNumber() > 0:

        # lower level controller for subnetwork A updates phase timings for KUF and KBT (upper level controller called in helper func)
        if(traci.trafficlight.getPhase("kuf") in [0,3,6,9]):
            kuf_phase = traci.trafficlight.getPhase("kuf")
            kuf_phase_name = traci.trafficlight.getPhaseName("kuf")
        if(kuf_phase != old_kuf_phase):
            print("CURRENT PHASE AND NAME FOR KUF: " + str(kuf_phase) + " : " + str(kuf_phase_name))    

            vehicle_count_dict = getLaneParams()
            print(f"Lower level controller for KUF-KBT active!")
            #print(vehicle_count_dict)
            kuf_phase_name = traci.trafficlight.getPhaseName("kuf")
            print(f"kuf_phase_name is: " + kuf_phase_name)
            print(f"calling helper function now!")
            greentime = helper_function(kuf_phase_name,vehicle_count_dict)
            print(f"greentime returned by helper_function! green time is: " + str(greentime) + str(type(greentime)))

            traci.trafficlight.setPhaseDuration("kuf", greentime)   
            traci.trafficlight.setPhaseDuration("kbt", greentime)   
            
            print(f"Phase and Duration for KUF: " + str(traci.trafficlight.getPhaseName("kuf"))+ ", "+str(traci.trafficlight.getPhaseDuration("kuf")) )
            print(f"Phase and Duration for KBT: " + str(traci.trafficlight.getPhaseName("kbt"))+ ", "+str(traci.trafficlight.getPhaseDuration("kbt")) )

        old_kuf_phase = kuf_phase

        # lower level controller for subnetwork B updates phase timings for KA
        if(traci.trafficlight.getPhase("ka") in [0,3,6]):
            ka_phase = traci.trafficlight.getPhase("ka")
            ka_phase_name = traci.trafficlight.getPhaseName("ka")
        if(ka_phase != old_ka_phase):
            print("CURRENT PHASE AND NAME FOR KA: " + str(ka_phase) + " : " + str(ka_phase_name))

            vehicle_count_dict = getLaneParams()
            print(f"Lower level controller for KA active!")
            ka_phase_name = traci.trafficlight.getPhaseName("ka")
            print(f"ka_phase_name is: " + ka_phase_name)
            print(f"calling helper function now!")
            greentime = helper_function(ka_phase_name,vehicle_count_dict)
            print(f"greentime returned by helper_function! green time is: " + str(greentime) + str(type(greentime)))

            traci.trafficlight.setPhaseDuration("ka", greentime)

            print(f"Phase and Duration for KA: " + str(traci.trafficlight.getPhaseName("ka"))+ ", "+str(traci.trafficlight.getPhaseDuration("ka")) )

        old_ka_phase = ka_phase

        traci.simulationStep() # move one second in simulation
    traci.close()
    sys.stdout.flush()

if __name__ == "__main__":
    options = get_options()

    # check binary
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo')

    # traci starts sumo as a subprocess and then this script connects and runs
    traci.start([sumoBinary, "-c", "osm.sumocfg",
                    "--tripinfo-output", "tripinfo.xml"]) 
    #getLaneParams()
    
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        run()
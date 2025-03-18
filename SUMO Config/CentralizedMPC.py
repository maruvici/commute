import math
import torch
from botorch.models import SingleTaskGP, ModelListGP
from gpytorch.mlls.exact_marginal_log_likelihood import ExactMarginalLogLikelihood
from botorch.fit import fit_gpytorch_mll
from botorch.acquisition.monte_carlo import qExpectedImprovement
from botorch.optim import optimize_acqf
import random

import warnings

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
K_UTURN = Vertex("K_UTURN",0, 0, 9, 7, KT, UTURN)  # to La Vista [kbt-4a]

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
FDR_K3 = Vertex("FDR_K3",0, 0, 9, 7, FDR, KSX)  #  to Aurora Blvd. [kuf-9]

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
Roads = [KT_BG, KT_KL2, KT_TD, K_UTURN, BG_KT, BG_TD, BG_KL2, TD_KT, TD_BG, TD_BG, TD_KL2, KR3_KT, KR3_TD,
        KL2_KSX, KL2_UR, KL2_KR3, FDR_KR3, FDR_UR, FDR_K3, UR_KR3, UR_KSX, KNX_KR3, KNX_UR,
        KSX_AUL, KSX_AUR, AUL_AUR, AUR_KNX, AUR_AUL, AUR_KB, KB_AUL ]

Entrance_Nodes = [KT, BG, TD, FDR, UR, AUL, AUR, KB]
Exit_Nodes = [KT, BG, TD, UR, AUL, AUR, KB]

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


def Evaluate_Busy(Green_Time):
    Restore_Original_State()
    global Cars_Passed
    Cars_Passed = 0
    y = 0   
    for i in range(len(Roads)):  # go through all the lanes
        if Roads[i].busy == 1:  # if the selected road is busy meaning there is a presence of car/s
            y = torch.ceil(Green_Time / (Roads[i].leng / Roads[i].speed))[-1]# Number of Cars that can pass through in green time
            if y > Roads[i].car_num:
                y = Roads[i].car_num
            Roads[i].car_num = Roads[i].car_num - y  # Remove from road
            Cars_Passed = Cars_Passed + y
        #print(f"Road {Roads[i].name} has {Roads[i].car_num} cars")
    global Time
    #print(f"Time: {Time} ")
    #print(f"Green_Time: {Green_Time} ")
    #Time = Time + Green_Time

def Phase_1():
    # kbt ok
    Set_Busy(KT_KL2) #kbt5
    Set_Busy(KR3_KT) #kbt2
    Set_Busy(KR3_TD) #kbt3

    # kuf ok
    Set_Busy(KL2_KSX) #kuf5
    Set_Busy(KNX_KR3) #kuf2
    Set_Busy(KR3_UR) #kuf3-3a

    # ka 


def Phase_2():
    # kbt ok
    Set_Busy(BG_KT) #kbt7
    Set_Busy(BG_KL2) #kbt9
    #Set_Busy(BG_TD) #kbt8
    #Set_Busy(KR3_TD) #kbt3

    # kuf ok
    Set_Busy(UR_KSX) #kuf10b    
    Set_Busy(FDR_KR3) #kuf7
    Set_Busy(FDR_KSX) #kuf9
    Set_Busy(FDR_UR) #kuf8-8a
 

def Phase_3():
    # kbt ok
    Set_Busy(KT_UTURN) #kbt4a
    Set_Busy(TD_KL2) #kbt10

    #Set_Busy(TD_BG) #kbt11
    #Set_Busy(TD_KT) #kbt12
    #Set_Busy(KR3_TD) #kbt3
    #Set_Busy(KT_BG) #kbt6

    # kuf ok
    Set_Busy(UR_KSX) #kuf
    Set_Busy(UR_KR3) #kuf
    
    #Set_Busy(KNX_UR) #kuf

    # ka


def Phase_4():
    # kbt ok
    Set_Busy(KT_UTURN) #kbt4a
    Set_Busy(KT_KL2) #kbt5
    Set_Busy(KT_TD) #kbt4
    #Set_Busy(KT_BG) #kbt6

    # kuf ok
    Set_Busy(KL2_UR) #kuf4-4b
    Set_Busy(KL2_KR3) #kuf4a
    #Set_Busy(KL2_UTURN) #kuf4a
    Set_Busy(KL2_KSX) #kuf5


def Unassert():
    for i in range(len(Roads)):
        Set_Stall(Roads[i])


""" !TO_DO: helper function """
""" !TO_COPY: target function """
""" !TO_COPY: optimize function and loops """
""" !TO_Update: getLanParams """
""" !TO_Update: run function """
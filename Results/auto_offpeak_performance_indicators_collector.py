import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import statistics

RESULTS_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(RESULTS_DIR, "all_performance_indicators.txt")

def run_performance_indicators(tripinfo_path, summary_path):
    output_lines = []

    # Load XMLs
    root = ET.parse(tripinfo_path).getroot()
    root2 = ET.parse(summary_path).getroot()

    def extract_tripinfo(attribute_name, flag=0):
        values = []
        for tripinfo in root.findall('tripinfo'):
            value = tripinfo.get(attribute_name)
            if value is not None:
                values.append(float(value))
            if value is not None and flag == 1 and float(tripinfo.get('depart')) >= 14400.00:
                return sum(values) / len(values)
        return sum(values) / len(values)

    def extract_summary(attribute_name, flag=0):
        values = []
        for step in root2.findall('step'):
            value = step.get(attribute_name)
            if value is not None:
                values.append(float(value))
            if value is not None and flag == 1 and float(step.get('time')) == 14400.00:
                return sum(values) / 14400
        return sum(values) / 14400

    def extract_tripinfo_vfr():
        count = 0.0
        for tripinfo in root.findall('tripinfo'):
            arrival = tripinfo.get('arrival')
            if arrival and float(arrival) <= 14440.0:
                count += classify_vehicle(tripinfo)
        return 3600 * count / 14400.0

    def serviced_4hr():
        for step in root2.findall('step'):
            if step.get('time') == "14400.00":
                return step.get('arrived')

    def classify_vehicle(tripinfo):
        departure = tripinfo.get('departLane')[:-2]
        arrival = tripinfo.get('arrivalLane')[:-2]
        if ((departure in depart_bottom and arrival in arrive_top) or
            (departure in depart_top and arrival in arrive_bottom)):
            return 3.0
        elif ((departure in depart_top and arrival in arrive_middle) or
              (departure in depart_bottom and arrival in arrive_middle) or
              (departure in depart_middle and arrival in arrive_top) or
              (departure in depart_middle and arrival in arrive_bottom)):
            return 2.0
        else:
            return 1.0

    def extract_summary_15min_ql(start, end):
        values = []
        for step in root2.findall('step'):
            if float(step.get('time')) >= float(start):
                values.append(float(step.get('halting')))
            if float(step.get('time')) == float(end):
                return sum(values) / 900.0
        return 0.0

    def extract_tripinfo_15min_qt(start, end):
        values = [float(trip.get('waitingTime')) for trip in root.findall('tripinfo')
                  if float(trip.get('depart')) >= float(start) and float(trip.get('depart')) <= float(end)]
        return sum(values) / len(values) if values else 0.0

    def extract_tripinfo_15min_fr(start, end):
        count = 0.0
        for tripinfo in root.findall('tripinfo'):
            arrival = tripinfo.get('arrival')
            if arrival and float(arrival) >= float(start) and float(arrival) <= float(end):
                count += classify_vehicle(tripinfo)
        return 3600 * count / 900.0

    # Predefined lanes
    global depart_bottom, arrive_bottom, depart_middle, arrive_middle, depart_top, arrive_top
    depart_bottom = ["R7", "aurora-lower_in", "aurora-upper_in"]
    arrive_bottom = ["L7", "aurora-lower_out", "aurora-upper_out"]
    depart_middle = ["f.dela_rosa-road", "univ_road-upper_in", "univ_road-lower_in"]
    arrive_middle = ["univ_road-upper_out", "univ_road-lower_out"]
    depart_top = ["L1", "thornton_drive-extension-in"]
    arrive_top = ["R1", "thornton_drive-extension-out", "b.gonzales-road-out", "b.gonzales-road-in"]

    # Whole and 4-hour summaries
    output_lines.append(f"(WHOLE) Average queue length (veh): {extract_summary('halting', 0)/24:.8f}")
    output_lines.append(f"(4 HR) Average queue length (veh) - 4 hour: {extract_summary('halting', 1)/24:.8f}")
    output_lines.append(f"(WHOLE) Average time in queue (s): {extract_tripinfo('waitingTime', 0):.8f}")
    output_lines.append(f"(4 HR) Average time in queue (s): {extract_tripinfo('waitingTime', 1):.8f}")
    vfr = extract_tripinfo_vfr()
    output_lines.append(f"(WHOLE) Average vehicular flow rate (veh/hr): {vfr:.2f}")
    output_lines.append(f"(4 HR) Average vehicular flow rate (veh/hr): {vfr:.2f}")
    output_lines.append(f"Cars serviced in 4 hours is:  {serviced_4hr()}")

    # 15-minute intervals
    intervals = [(str(x * 900), str((x + 1) * 900)) for x in range(16)]
    hour_blocks = [(6 + 0.25 * x, 6 + 0.25 * (x + 1)) for x in range(16)]

    output_lines.append(str(hour_blocks))
    output_lines.append("QUEUE LENGTHS  4-8PM - 15 MINUTE INTERVALS")
    output_lines.append(str([extract_summary_15min_ql(start, end)/24 for start, end in intervals]))
    output_lines.append("QUEUE TIMES  4-8PM - 15 MINUTE INTERVALS")
    output_lines.append(str([extract_tripinfo_15min_qt(start, end) for start, end in intervals]))
    output_lines.append("FLOW RATES  4-8PM - 15 MINUTE INTERVALS")
    output_lines.append(str([extract_tripinfo_15min_fr(start, end) for start, end in intervals]))

    return output_lines

def format_time(hour_float):
    total_minutes = int(hour_float * 60)
    hour = total_minutes // 60
    minute = total_minutes % 60
    return f"{hour:02}:{minute:02}"

# --- Main loop over subfolders ---
def main():
    all_q_len_4hr = []
    all_q_time_4hr = []
    all_vfr_4hr = []
    all_q_len_whole = []
    all_q_time_whole = []
    all_vfr_whole = []
    sum_cars_serviced = 0
    num_sims = 0

    interval_q_lengths = [[] for _ in range(16)]
    interval_q_times = [[] for _ in range(16)]
    interval_flow_rates = [[] for _ in range(16)]

    subdirs = sorted([
        d for d in os.listdir(RESULTS_DIR)
        if os.path.isdir(os.path.join(RESULTS_DIR, d)) and not d.startswith('.')
    ])

    with open(OUTPUT_FILE, 'w') as out_file:
        for idx, subdir in enumerate(subdirs, start=1):
            print(idx, subdir)
            timestamp = subdir
            tripinfo_path = os.path.join(RESULTS_DIR, subdir, f"tripinfo_out_{timestamp}.xml")
            summary_path = os.path.join(RESULTS_DIR, subdir, f"summary_out_{timestamp}.xml")

            if not os.path.exists(tripinfo_path) or not os.path.exists(summary_path):
                print(f"Skipping {timestamp} due to missing files.")
                continue

            out_file.write(f"Simulation {idx}\n")
            out_file.write(f"Timestamp {timestamp}\n")
            results = run_performance_indicators(tripinfo_path, summary_path)
            out_file.write("\n".join(results) + "\n\n")

            for line in results:
                if "(4 HR) Average queue length" in line:
                    all_q_len_4hr.append(float(line.split(":")[1]))
                elif "(4 HR) Average time in queue" in line:
                    all_q_time_4hr.append(float(line.split(":")[1]))
                elif "(4 HR) Average vehicular flow rate" in line:
                    all_vfr_4hr.append(float(line.split(":")[1]))
                elif "(WHOLE) Average queue length" in line:
                    all_q_len_whole.append(float(line.split(":")[1]))
                elif "(WHOLE) Average time in queue" in line:
                    all_q_time_whole.append(float(line.split(":")[1]))
                elif "(WHOLE) Average vehicular flow rate" in line:
                    all_vfr_whole.append(float(line.split(":")[1]))
                elif "Cars serviced" in line:
                    sum_cars_serviced += int(float(line.split(":")[1]))

            try:
                q_len_index = results.index("QUEUE LENGTHS  4-8PM - 15 MINUTE INTERVALS")
                q_time_index = results.index("QUEUE TIMES  4-8PM - 15 MINUTE INTERVALS")
                flow_rate_index = results.index("FLOW RATES  4-8PM - 15 MINUTE INTERVALS")

                sim_q_lengths = eval(results[q_len_index + 1])
                sim_q_times = eval(results[q_time_index + 1])
                sim_flow_rates = eval(results[flow_rate_index + 1])

                for i in range(16):
                    interval_q_lengths[i].append(sim_q_lengths[i])
                    interval_q_times[i].append(sim_q_times[i])
                    interval_flow_rates[i].append(sim_flow_rates[i])
            except Exception as e:
                print(f"Warning: Could not extract interval data for sim {idx} — {e}")

            num_sims += 1

        if num_sims > 0:
            out_file.write("- - - AVERAGED PERFORMANCE INDICATORS ACROSS ALL SIMULATIONS - - -\n")
            out_file.write(f"(WHOLE) Average Queue Length: {statistics.mean(all_q_len_whole):.4f}\n")
            out_file.write(f"(4 HR) Average Queue Length: {statistics.mean(all_q_len_4hr):.4f}\n")
            out_file.write(f"(WHOLE) Average Queue Time: {statistics.mean(all_q_time_whole):.4f}\n")
            out_file.write(f"(4 HR) Average Queue Time: {statistics.mean(all_q_time_4hr):.4f}\n")
            out_file.write(f"(WHOLE) Average Vehicular Flow Rate: {statistics.mean(all_vfr_whole):.2f}\n")
            out_file.write(f"(4 HR) Average Vehicular Flow Rate: {statistics.mean(all_vfr_4hr):.2f}\n")
            out_file.write(f"Cars Serviced on Average: {sum_cars_serviced / num_sims:.2f}\n")

            out_file.write("\n- - - STANDARD DEVIATIONS ACROSS ALL SIMULATIONS - - -\n")
            out_file.write(f"(WHOLE) Std Dev Queue Length: {statistics.stdev(all_q_len_whole):.4f}\n")
            out_file.write(f"(4 HR) Std Dev Queue Length: {statistics.stdev(all_q_len_4hr):.4f}\n")
            out_file.write(f"(WHOLE) Std Dev Queue Time: {statistics.stdev(all_q_time_whole):.4f}\n")
            out_file.write(f"(4 HR) Std Dev Queue Time: {statistics.stdev(all_q_time_4hr):.4f}\n")
            out_file.write(f"(WHOLE) Std Dev Vehicular Flow Rate: {statistics.stdev(all_vfr_whole):.2f}\n")
            out_file.write(f"(4 HR) Std Dev Vehicular Flow Rate: {statistics.stdev(all_vfr_4hr):.2f}\n")

            out_file.write("\n--- AVERAGE 15-MINUTE INTERVAL PERFORMANCE ---\n")
            out_file.write(f"{'Interval':<17}{'Avg Queue Length':>20}{'Avg Queue Time':>20}{'Avg Flow Rate':>20}\n")
            for i in range(16):
                avg_ql = sum(interval_q_lengths[i]) / len(interval_q_lengths[i])
                avg_qt = sum(interval_q_times[i]) / len(interval_q_times[i])
                avg_fr = sum(interval_flow_rates[i]) / len(interval_flow_rates[i])
                start_hr = 10 + 0.25 * i
                end_hr = 10 + 0.25 * (i + 1)
                interval_label = f"{format_time(start_hr)}-{format_time(end_hr)}"
                out_file.write(f"{interval_label:<17}{avg_ql:>20.4f}{avg_qt:>20.4f}{avg_fr:>20.2f}\n")

if __name__ == "__main__":
    main()

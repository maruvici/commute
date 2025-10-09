import os
import xml.etree.ElementTree as ET

# Define constants
RESULTS_DIR = os.path.dirname(os.path.abspath(__file__))  # Current directory (results/)
OUTPUT_FILE = os.path.join(RESULTS_DIR, "all_hourly_simulated_demand.txt")
first_four_hour_totals = []

# Lists to store per-hour demand across all simulations
hour_1_list = []
hour_2_list = []
hour_3_list = []
hour_4_list = []

def process_tripinfo_file(file_path):
    # Load and parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define the range increments
    increment = 3600
    counters = {}
    for i in range(0, 50400, increment):
        counters[f"count_{i+1}_{i+increment}"] = 0
    counters["count_50401_onwards"] = 0

    # Helper to update counters
    def check_and_increment(value):
        for i in range(0, 50400, increment):
            lower_bound = i + 1
            upper_bound = i + increment
            if lower_bound <= value <= upper_bound:
                counters[f"count_{lower_bound}_{upper_bound}"] += 1
                return
        if value > 50400:
            counters["count_50401_onwards"] += 1

    # Process each tripinfo entry
    for tripinfo in root.findall('tripinfo'):
        depart_time = tripinfo.get('depart')
        if depart_time is not None:
            check_and_increment(int(float(depart_time)))

    return counters

def main():
    with open(OUTPUT_FILE, 'w') as out_file:
        subdirs = sorted([
            d for d in os.listdir(RESULTS_DIR)
            if os.path.isdir(os.path.join(RESULTS_DIR, d)) and not d.startswith('.')
        ])
        
        for idx, subdir in enumerate(subdirs, start=1):
            print(idx, subdir)
            timestamp = subdir
            tripinfo_file = os.path.join(RESULTS_DIR, subdir, f"tripinfo.xml")
            if not os.path.exists(tripinfo_file):
                tripinfo_file = os.path.join(RESULTS_DIR, subdir, f"tripinfo_out_{timestamp}.xml")
                if not os.path.exists(tripinfo_file):
                    print(f"Warning: {tripinfo_file} not found, skipping.")
                    continue

            counters = process_tripinfo_file(tripinfo_file)

            out_file.write(f"Simulation {idx}\n")
            out_file.write(f"Timestamp {timestamp}\n")
            hour_number = 1
            hourly_counts = []

            for key in counters:
                if key == "count_50401_onwards":
                    continue
                count = counters[key]
                hourly_counts.append(count)
                out_file.write(f"Hour {hour_number}: {count}\n")
                hour_number += 1

            # Record per-hour data for averages
            if len(hourly_counts) >= 4:
                hour_1_list.append(hourly_counts[0])
                hour_2_list.append(hourly_counts[1])
                hour_3_list.append(hourly_counts[2])
                hour_4_list.append(hourly_counts[3])

                total_first_four_hours = sum(hourly_counts[:4])
                out_file.write(f"Total demand (Hour 1–4): {total_first_four_hours}\n")
                first_four_hour_totals.append(total_first_four_hours)

            out_file.write("\n")

        # Final averages
        
        if hour_1_list:
            out_file.write(f"Average demand Hour 1: {sum(hour_1_list)/len(hour_1_list):.2f}\n")
            out_file.write(f"Average demand Hour 2: {sum(hour_2_list)/len(hour_2_list):.2f}\n")
            out_file.write(f"Average demand Hour 3: {sum(hour_3_list)/len(hour_3_list):.2f}\n")
            out_file.write(f"Average demand Hour 4: {sum(hour_4_list)/len(hour_4_list):.2f}\n")
            
        if first_four_hour_totals:
            avg_total_first_four_hours = sum(first_four_hour_totals) / len(first_four_hour_totals)
            out_file.write(f"Average total demand (Hour 1–4) across all simulations: {avg_total_first_four_hours:.2f}\n")

if __name__ == "__main__":
    main()
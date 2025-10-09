import xml.etree.ElementTree as ET

# Load and parse the XML file
tree = ET.parse('tripinfo.xml')
root = tree.getroot()

def extract_tripinfo(attribute_name):
    for tripinfo in root.findall('tripinfo'):
        value = tripinfo.get(attribute_name)
        if value is not None:
            check_and_increment(int(float(value)))
            

# Define the range increments
increment = 3600

# Initialize counters for each range
counters = {}
for i in range(0, 50400, increment):
    counters[f"count_{i+1}_{i+increment}"] = 0
counters["count_50401_onwards"] = 0

# Function to check which range a value belongs to and increment the respective counter
def check_and_increment(value):
    for i in range(0, 50400, increment):
        lower_bound = i + 1
        upper_bound = i + increment
        if lower_bound <= value <= upper_bound:
            counters[f"count_{lower_bound}_{upper_bound}"] += 1
            break
    if value > 50400:
        counters["count_50401_onwards"] += 1


attribute_wt = 'depart'
average_wt = extract_tripinfo(attribute_wt)

for key, count in counters.items():
    print(count)
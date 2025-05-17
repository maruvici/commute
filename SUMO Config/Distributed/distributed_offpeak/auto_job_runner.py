import subprocess
import time

script_name = "DistributedMPC.py"

while True:
    try:
        print(f"Starting {script_name}...")
        # Run the script as a subprocess
        result = subprocess.run(["python3", script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"{script_name} crashed with error code {e.returncode}. Restarting in 5 seconds...")
        time.sleep(10)  # Optional delay before restart
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
        break

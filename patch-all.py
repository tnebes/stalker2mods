import os
import subprocess
import sys

def run_script(script_name):
    print(f"--- Running {script_name} ---")
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")

def main():
    print("Starting all patching tasks...")
    
    # 1. LessSway (Inheritance based)
    run_script("patch_weapons.py")
    run_script("patch_attach.py")
    
    # 2. RewardingHeadshots
    run_script("patch_rewarding_headshots.py")
    
    # 3. LongRangeCombat
    run_script("patch_long_range_combat.py")
    
    print("All patching tasks completed.")

if __name__ == "__main__":
    main()

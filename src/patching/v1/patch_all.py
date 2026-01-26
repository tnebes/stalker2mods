import os
import sys

# Ensure the current directory is in sys.path so submodules can find each other
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import lrc, sway, headshots, LessShotgunRecoil

def main():
    print("Starting all patching tasks...")
    
    # 1. LessSway (Refactored Module)
    sway.run()
    
    # 2. RewardingHeadshots (Refactored Module)
    headshots.run()
    
    # 3. LongRangeCombat (Refactored Module)
    lrc.run()

    # 4. LessShotgunRecoil
    LessShotgunRecoil.run()
    
    print("All patching tasks completed.")

if __name__ == "__main__":
    main()

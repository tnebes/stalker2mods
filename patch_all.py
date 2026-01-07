import os
import sys
from patching import lrc, sway, headshots

def main():
    print("Starting all patching tasks...")
    
    # 1. LessSway (Refactored Module)
    sway.run()
    
    # 2. RewardingHeadshots (Refactored Module)
    headshots.run()
    
    # 3. LongRangeCombat (Refactored Module)
    lrc.run()
    
    print("All patching tasks completed.")

if __name__ == "__main__":
    main()

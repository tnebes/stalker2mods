import math

def sigmoid(x, L, k, x0):
    return L / (1 + math.exp(-k * (x - x0)))

def get_rank_configs():
    ranks = ["Newbie", "Experienced", "Veteran", "Master", "Zombie"]
    brackets = ["Short", "Medium", "Long"]
    
    # Sigmoid parameters for Max Curve
    L_max = 0.7     # Max multiplier plateau
    k_max = 2.5     # Sharp rise
    x0_max = 1.4    # Shift left for earlier effectiveness
    C_max = 0.01    # Small baseline shift
    
    # Sigmoid parameters for Min Curve
    L_min = 0.5     # Min multiplier plateau
    k_min = 1.8    
    x0_min = 1.8   
    C_min = 0.05   
    
    rank_map = {
        "Newbie": 0.5,
        "Experienced": 2,
        "Veteran": 3,
        "Master": 4,
        "Zombie": 1
    }
    
    # Distance penalties
    dist_penalty = {
        "Short": 0.0,
        "Medium": 1.0,
        "Long": 2.2
    }
 
    # Range multipliers
    range_mults = {
        "Newbie": 0.8,
        "Experienced": 1.5,
        "Veteran": 1.5,
        "Master": 1.5,
        "Zombie": 1.0
    }
 
    # Hardcoded floors
    floors_min = {
        "Newbie": {"Short": 0, "Medium": 0, "Long": 0},
        "Experienced": {"Short": 1, "Medium": 0, "Long": 0},
        "Veteran": {"Short": 1, "Medium": 0, "Long": 0},
        "Master": {"Short": 1, "Medium": 1, "Long": 0},
        "Zombie": {"Short": 0, "Medium": 0, "Long": 0}
    }
    floors_max = {
        "Newbie": {"Short": 1, "Medium": 1, "Long": 0},
        "Experienced": {"Short": 1, "Medium": 1, "Long": 0},
        "Veteran": {"Short": 1, "Medium": 1, "Long": 0},
        "Master": {"Short": 1, "Medium": 1, "Long": 1},
        "Zombie": {"Short": 1, "Medium": 0, "Long": 0}
    }
 
    # Burst size and Guaranteed hit parameters
    burst_logic = {
        "Newbie": {
            "burst_mult": 1.25,
            "min_add": 0,
            "max_add": 0,
            "guaranteed_add_long": 0,
            "guaranteed_add_medium": 0,
            "guaranteed_add_short": 0
        },
        "Experienced": {
            "burst_mult": 1.0, 
            "long_burst_mult": 0.9,
            "min_add": 0,
            "max_add": 0,
            "guaranteed_add_long": 0,
            "guaranteed_add_medium": 0,
            "guaranteed_add_short": 0,
            "ignore_disp_max_inc_if_small": 1
        },
        "Veteran": {
            "burst_mult": 1.0,
            "long_burst_mult": 0.75,
            "medium_burst_mult": 0.85,
            "short_burst_mult": 1.1,
            "min_add": 0,
            "max_add": 1
        },
        "Master": {
            "burst_mult": 1.0,
            "long_burst_mult": 0.4,
            "medium_burst_mult": 0.75,
            "short_burst_mult": 1.25,
            "min_add": 0,
            "max_add": 0,
            "guaranteed_add_long_min": 0,
            "guaranteed_add_long_max": -1,
            "guaranteed_add_medium_min": 0,
            "guaranteed_add_medium_max": 1,
            "guaranteed_add_short_mag_pct": 0.04
        },
        "Zombie": {
            "burst_mult": 1.5,
            "min_add": 0,
            "max_add": 0
        }
    }
 
    results = {}
    for r_name in ranks:
        r_val = rank_map[r_name]
        chance_min = {}
        chance_max = {}
        for b in brackets:
            x = r_val - dist_penalty[b]
            val_max = sigmoid(x, L_max, k_max, x0_max) - C_max
            val_min = sigmoid(x, L_min, k_min, x0_min) - C_min
            chance_max[b] = round(max(0, val_max), 4)
            chance_min[b] = round(max(0, val_min), 4)
 
        results[r_name] = {
            "range_mult": range_mults[r_name],
            "ignore_disp_min": floors_min[r_name],
            "ignore_disp_max": floors_max[r_name],
            "ignore_disp_chance_min": chance_min,
            "ignore_disp_chance_max": chance_max,
            "burst_logic": burst_logic.get(r_name, {})
        }
    return results

def print_burst_projections(output_to_file=False):
    data = get_rank_configs()
    burst_scenarios = [
        (3, 6),
        (4, 14),
        (8, 16)
    ]
    brackets = ["Short", "Medium", "Long"]
    output = []

    output.append("# Burst Accuracy Projections")
    output.append("Logic: `max(Floor, int(MinShots * Chance))`")
    output.append("")

    for min_shots, max_shots in burst_scenarios:
        output.append(f"## Scenario: MinShots={min_shots}, MaxShots={max_shots}")
        output.append("| Rank | Short (Min/Max) | Medium (Min/Max) | Long (Min/Max) |")
        output.append("| :--- | :--- | :--- | :--- |")
        for r_name, r_data in data.items():
            row = [f"**{r_name}**"]
            for b in brackets:
                f_min = r_data["ignore_disp_min"][b]
                f_max = r_data["ignore_disp_max"][b]
                c_min = r_data["ignore_disp_chance_min"][b]
                c_max = r_data["ignore_disp_chance_max"][b]

                calc_min = max(f_min, int(min_shots * c_min))
                calc_max = max(f_max, int(min_shots * c_max))
                row.append(f"{calc_min} / {calc_max}")
            output.append(f"| {' | '.join(row)} |")
        output.append("")

    final_output = "\n".join(output)
    if output_to_file:
        import os
        # Path relative to the script
        target = os.path.join(os.path.dirname(__file__), "../../../curves.md")
        with open(target, "w") as f:
            f.write(final_output)
        print(f"Burst projections (Markdown) written to {os.path.abspath(target)}")
    else:
        print(final_output)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NPC Rank Curve Inspection Tool")
    parser.add_argument("-i", "--inspect", action="store_true", help="Print burst projections to curves.md for inspection.")
    args = parser.parse_args()
    
    if args.inspect:
        print_burst_projections(output_to_file=True)
    else:
        data = get_rank_configs()
        # Just print the config as a sanity check
        import pprint
        pprint.pprint(data)

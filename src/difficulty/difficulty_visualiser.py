import os
import re
import argparse
from typing import Dict, Any, List

# Configuration and Paths
DEFAULT_CFG_PATH = r"C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData\DifficultyPrototypes.cfg"
OUTPUT_HTML = "difficulty_comparison.html"

# Attribute Classification
# Higher values = Better for player
POSITIVE_ATTRIBUTES = {
    "Weapon_BaseDamage",
    "Regen_HP",
    "Armor_Durability",
    "Reward_MainLine_Money",
    "Reward_SideLine_Money",
    "BuyCondition",
    "PlayerWeapon_HeadshotMultiplier",
    "Armor_Strike_Add",
    "Armor_Anomaly",
    "Armor_Radiation",
    "Armor_PSY",
    "Weapon_Durability",
    "Weapon_Rank_Add",
    "NPC_AttackCooldown",
    "Mutant_AttackCooldown",
    "Effect_Degen_Bleeding", # Bleeding degradation (healing), higher is better
}

# Higher values = Worse for player
NEGATIVE_ATTRIBUTES = {
    "NPC_Weapon_BaseDamage",
    "Explosion_BaseDamage",
    "Effect_Bleeding",
    "Mutant_BaseDamage",
    "Weapon_DurabilityDamage",
    "Radiation_AccumulationSpeed",
    "Anomaly_Damage",
    "Upgrade_Cost",
    "Effect_Satiety",
    "Weapon_JammingMultiplier",
    "SellCondition",
    "NPC_HP",
    "NPC_Armor_Strike_Add",
    "NPC_Weapon_Rank_Add",
    "Effect_Sleepiness",
    "Consumable_Cost",
    "Ammo_Cost",
    "Armor_Cost",
    "Weapon_Cost",
    "Artifact_Cost",
    "NightVisionGoggles_Cost",
    "Repair_Cost",
    "Radiation_AccumulationSpeed",
    "Anomaly_Damage"
}

# Attributes to ignore or treat as neutral (reduced to show more)
NEUTRAL_ATTRIBUTES = {
    "SID", "TitleSID", "DescriptionSID"
}

# Attribute Descriptions for Tooltips
ATTRIBUTE_DESCRIPTIONS = {
    "NPC_HP": "Multiplier for NPC Health. Lower means enemies die faster.",
    "Weapon_BaseDamage": "Your weapon damage output. Higher is more lethal for enemies.",
    "NPC_Weapon_BaseDamage": "Damage you take from NPC guns. Lower is easier.",
    "Explosion_BaseDamage": "Damage taken from grenades and barrels.",
    "Effect_Sleepiness": "How fast you get tired. Higher = faster fatigue.",
    "Effect_Bleeding": "Severity of bleeding. Higher = faster HP loss when wounded.",
    "Regen_HP": "Passive health regeneration speed.",
    "Armor_Durability": "Resistance of armor to damage. Higher = armor lasts longer.",
    "Weapon_DurabilityDamage": "How fast your guns break. Lower is better.",
    "Radiation_AccumulationSpeed": "Rate of radiation buildup in zones.",
    "Anomaly_Damage": "Damage taken from anomalies like burners or electros.",
    "Reward_MainLine_Money": "Money earned from main quests.",
    "Reward_SideLine_Money": "Money earned from side quests.",
    "Upgrade_Cost": "Price of gear upgrades.",
    "Effect_Satiety": "How fast you get hungry. Higher = faster starvation.",
    "Weapon_JammingMultiplier": "Chance for guns to jam as they degrade.",
    "SellCondition": "Minimum item condition required to sell to traders.",
    "BuyCondition": "Condition of items sold by traders.",
    "PlayerWeapon_HeadshotMultiplier": "Damage bonus for headshots.",
    "Mutant_BaseDamage": "Damage from mutant attacks.",
    "Mutant_AttackCooldown": "Time between mutant attacks (higher = safer).",
    "NPC_AttackCooldown": "Time between NPC attacks (higher = safer).",
    "Armor_Strike_Add": "Resistance to physical blunt force.",
    "Armor_Anomaly": "Resistance to anomaly effects.",
    "Armor_Radiation": "Resistance to radiation.",
    "Armor_PSY": "Resistance to psychic attacks.",
    "Weapon_Durability": "Baseline weapon durability multiplier.",
    "Weapon_Rank_Add": "Damage bonus based on weapon rank.",
    "Effect_Degen_Bleeding": "Speed at which bleeding stops naturally.",
    "NPC_Armor_Strike_Add": "NPC resistance to physical damage.",
    "NPC_Weapon_Rank_Add": "Damage bonus NPCs get from their rank.",
    "Consumable_Cost": "Cost of food and medicine.",
    "Ammo_Cost": "Cost of bullets.",
    "Armor_Cost": "Cost of buying suits.",
    "Weapon_Cost": "Cost of buying guns.",
    "Artifact_Cost": "Selling price of artifacts.",
    "NightVisionGoggles_Cost": "Cost of NVGs.",
    "Repair_Cost": "Cost of fixing equipment.",
    "AccumulatedDamageReductionCurveWeightMax": "Max multiplier for the distance-based damage reduction curve.",
    "AccumulatedDamageReductionCurveWeightMin": "Min multiplier for the distance-based damage reduction curve.",
    "AccumulatedDamageReductionCurveWeightMaxDistance": "Distance where damage reduction is at its maximum.",
    "AccumulatedDamageReductionIncludesHealedHealth": "Whether healed HP counts toward accumulated damage history.",
    "HipAccuracyMultiplier": "Multiplier for weapon dispersion when firing without aiming (hip fire).",
    "Weather_Emission_Weight": "Multiplier for the frequency/probability of Blowouts (Emissions).",
    "Weather_Storm_Weight": "Multiplier for the frequency/probability of Storm events.",
}

def parse_cfg(file_path: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return {}

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    prototypes = {}
    current_proto = None
    stack = []

    # Regex to catch: Key : struct.begin {refkey=...} or Key : struct.begin
    struct_start_re = re.compile(r'^(\w+)\s*:\s*struct\.begin(?:\s*\{refkey=(\w+)\})?')
    # Regex to catch: Key = Value
    kv_re = re.compile(r'^\s*(\w+)\s*=\s*(.*)$')
    # Regex to catch end
    struct_end_re = re.compile(r'^\s*struct\.end')

    for line in lines:
        line = line.strip()
        if not line or line.startswith("//"):
            continue

        # Check for struct start
        match = struct_start_re.match(line)
        if match:
            proto_name = match.group(1)
            ref_key = match.group(2)
            
            if not stack:
                current_proto = {
                    "name": proto_name,
                    "refkey": ref_key,
                    "values": {}
                }
                prototypes[proto_name] = current_proto
            
            stack.append(proto_name)
            continue

        # Check for struct end
        if struct_end_re.match(line):
            if stack:
                stack.pop()
            if not stack:
                current_proto = None
            continue

        # Check for KV pair (only top level for now, or simplify)
        if current_proto and len(stack) == 1:
            kv_match = kv_re.match(line)
            if kv_match:
                key = kv_match.group(1)
                value = kv_match.group(2).strip()
                # Simple cleanup of value
                if value.endswith(','): value = value[:-1]
                
                # Conversion
                try:
                    if '.' in value:
                        current_proto["values"][key] = float(value)
                    else:
                        current_proto["values"][key] = int(value)
                except ValueError:
                    # Keep as string (e.g. booleans, enums)
                    if value.lower() == 'true': current_proto["values"][key] = True
                    elif value.lower() == 'false': current_proto["values"][key] = False
                    else: current_proto["values"][key] = value

    # Resolve inheritance
    resolved_prototypes = {}
    
    def get_resolved_values(name, visited=None):
        if visited is None: visited = set()
        if name in visited: return {} # Circular dependency
        visited.add(name)

        if name not in prototypes: return {}
        
        proto = prototypes[name]
        parent_values = {}
        if proto["refkey"]:
            parent_values = get_resolved_values(proto["refkey"], visited)
        
        # Merge current into parent (current overrides)
        merged = parent_values.copy()
        merged.update(proto["values"])
        return merged

    for name in prototypes:
        resolved_prototypes[name] = get_resolved_values(name)

    return resolved_prototypes

def generate_comparison_html(data: Dict[str, Dict[str, Any]], baseline_key: str = "Medium"):
    if baseline_key not in data:
        print(f"Error: Baseline '{baseline_key}' not found in data.")
        return

    baseline = data[baseline_key]
    # Filter out entries that aren't real difficulties or are empty/xbox
    diff_keys = [k for k in data.keys() if k not in ["Empty", "Default"] and "xbox" not in k.lower()]
    # Sort them in a logical order
    order = ["Easy", "Medium", "Hard", "Stalker"]
    diff_keys = [k for k in order if k in diff_keys] + [k for k in diff_keys if k not in order]

    # Get all unique keys across all difficulties
    all_keys = set()
    for d in data.values():
        all_keys.update(d.keys())
    
    # Filter keys to only those that have numeric values or are interesting
    display_keys = sorted([k for k in all_keys if k not in NEUTRAL_ATTRIBUTES])

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>S.T.A.L.K.E.R. 2 Difficulty Visualiser</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #0a0a0c;
                --card-bg: #141418;
                --text: #e0e0e0;
                --text-dim: #a0a0a0;
                --accent: #f39c12;
                --green: #2ecc71;
                --red: #e74c3c;
                --grey: #444;
                --border: #2a2a2e;
                --tooltip-bg: #222;
            }
            body {
                background-color: var(--bg);
                color: var(--text);
                font-family: 'Outfit', sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
            }
            header {
                text-align: center;
                margin-bottom: 30px;
                width: 100%;
                max-width: 1200px;
            }
            h1 {
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 2px;
                margin: 0 0 10px 0;
                background: linear-gradient(90deg, #f39c12, #e67e22);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 2.5rem;
            }
            .subtitle {
                color: var(--text-dim);
                font-size: 1.1rem;
            }
            .table-container {
                width: 98vw;
                max-width: 100%;
                overflow-x: auto;
                background: var(--card-bg);
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                border: 1px solid var(--border);
                margin-bottom: 40px;
                scrollbar-width: thin;
                scrollbar-color: var(--accent) var(--card-bg);
            }
            table {
                border-collapse: separate;
                border-spacing: 0;
                width: 100%;
                min-width: 1200px; /* Ensure enough space for 5 columns including names */
            }
            th, td {
                padding: 16px 20px;
                text-align: left;
                border-bottom: 1px solid var(--border);
            }
            th {
                background: #1c1c22;
                font-weight: 600;
                color: var(--accent);
                text-transform: uppercase;
                font-size: 0.85rem;
                letter-spacing: 1px;
                position: sticky;
                top: 0;
                z-index: 10;
            }
            .attr-name-cell {
                display: flex;
                align-items: center;
                gap: 10px;
                position: sticky;
                left: 0;
                background: #1c1c22;
                z-index: 5;
                min-width: 250px;
            }
            .attr-name {
                font-weight: 500;
                color: var(--text);
            }
            .info-icon {
                cursor: help;
                opacity: 0.4;
                transition: opacity 0.2s, transform 0.2s;
                position: relative;
            }
            .info-icon:hover {
                opacity: 1;
                transform: scale(1.1);
            }
            /* Tooltip Style */
            .info-icon::after {
                content: attr(data-tooltip);
                position: absolute;
                left: 25px;
                top: 50%;
                transform: translateY(-50%);
                background: var(--tooltip-bg);
                color: white;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 0.8rem;
                width: 220px;
                visibility: hidden;
                opacity: 0;
                transition: opacity 0.3s;
                z-index: 100;
                pointer-events: none;
                text-transform: none;
                font-weight: 400;
                border: 1px solid var(--border);
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }
            .info-icon:hover::after {
                visibility: visible;
                opacity: 1;
            }
            .val-diff {
                display: flex;
                flex-direction: column;
            }
            .val-main {
                font-size: 1.1rem;
                font-weight: 600;
            }
            .val-perc {
                font-size: 0.75rem;
                opacity: 0.8;
            }
            .benefit { color: var(--green); }
            .detriment { color: var(--red); }
            .neutral { color: var(--text-dim); }
            .baseline-cell {
                background: rgba(243, 156, 18, 0.05) !important;
            }
            tr:last-child td {
                border-bottom: none;
            }
            tr:hover td {
                background: rgba(255, 255, 255, 0.02);
            }
            @media (max-width: 768px) {
                body { padding: 10px; }
                header h1 { font-size: 1.8rem; }
            }
        </style>
    </head>
    <body>
        <header>
            <h1>Difficulty Visualiser</h1>
            <p class="subtitle">Comparing all difficulties against <b>Medium</b> baseline</p>
        </header>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="position: sticky; left: 0; z-index: 11;">Parameter</th>
    """

    for k in diff_keys:
        html += f"<th>{k}</th>"
    
    html += "</tr></thead><tbody>"

    for attr in display_keys:
        desc = ATTRIBUTE_DESCRIPTIONS.get(attr, "No description available.")
        info_svg = f'<span class="info-icon" data-tooltip="{desc}"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg></span>'
        
        html += f"<tr><td class='attr-name-cell'><span class='attr-name'>{attr}</span> {info_svg}</td>"
        
        base_val = baseline.get(attr)
        
        for k in diff_keys:
            val = data[k].get(attr)
            
            status_class = "neutral"
            perc_str = ""
            
            if val is None:
                display_val = "-"
            else:
                display_val = str(val)
                if isinstance(val, (int, float)) and isinstance(base_val, (int, float)):
                    if base_val != 0:
                        diff_perc = (val / base_val - 1) * 100
                        if abs(diff_perc) < 0.01:
                            status_class = "neutral"
                            perc_str = "(0%)"
                        else:
                            is_increase = val > base_val
                            is_positive_attr = attr in POSITIVE_ATTRIBUTES
                            is_negative_attr = attr in NEGATIVE_ATTRIBUTES
                            
                            if (is_increase and is_positive_attr) or (not is_increase and is_negative_attr):
                                status_class = "benefit"
                            elif (is_increase and is_negative_attr) or (not is_increase and is_positive_attr):
                                status_class = "detriment"
                            
                            perc_str = f"({'+' if diff_perc > 0 else ''}{diff_perc:.1f}%)"
                    else:
                        if val > base_val: status_class = "benefit" if attr in POSITIVE_ATTRIBUTES else "detriment"
                        elif val < base_val: status_class = "detriment" if attr in POSITIVE_ATTRIBUTES else "benefit"

                elif isinstance(val, bool) and isinstance(base_val, bool):
                    if val != base_val:
                        if "Disable" in attr or "Limit" in attr:
                            status_class = "detriment" if val else "benefit"
                        else:
                            status_class = "neutral"

            is_baseline = (k == baseline_key)
            cell_style = "baseline-cell" if is_baseline else ""
            
            html += f"<td class='{cell_style}'><div class='val-diff'>"
            html += f"<span class='val-main {status_class}'>{display_val}</span>"
            html += f"<span class='val-perc {status_class}'>{perc_str}</span>"
            html += "</div></td>"
        
        html += "</tr>"

    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated {OUTPUT_HTML}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stalker 2 Difficulty Visualiser")
    parser.add_argument("--file", default=DEFAULT_CFG_PATH, help="Path to DifficultyPrototypes.cfg")
    args = parser.parse_args()

    data = parse_cfg(args.file)
    if data:
        generate_comparison_html(data)

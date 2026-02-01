import os
import re
from typing import Dict, Any, List

# Values where INCREASING is GOOD for the player (Buff)
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
    "Effect_Degen_Bleeding",
}

# Values where INCREASING is BAD for the player (Nerf)
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
    "AccumulatedDamageReductionCurveWeightMax",
    "AccumulatedDamageReductionCurveWeightMin",
}

NEUTRAL_ATTRIBUTES = {"SID", "TitleSID", "DescriptionSID"}

# Descriptions
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
    "Radiation_AccumulationSpeed": "Rate of radiation buildup",
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
    "Armor_PSY": "Resistance to psychotronic attacks.",
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
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    prototypes = {}
    current_proto = None
    stack = []
    
    # Improved regex: catch any name followed by : struct.begin
    struct_start_re = re.compile(r'^\s*([^:\s]+)\s*:\s*struct\.begin')
    kv_re = re.compile(r'^\s*(\w+)\s*=\s*(.*)$')
    struct_end_re = re.compile(r'^\s*struct\.end')
    refkey_re = re.compile(r'refkey=([^;\}]+)')

    for line in lines:
        line = line.strip()
        if not line or line.startswith("//"): continue
        
        match = struct_start_re.match(line)
        if match:
            name = match.group(1)
            ref_match = refkey_re.search(line)
            ref_key = ref_match.group(1) if ref_match else None
            
            if not stack:
                current_proto = {"name": name, "refkey": ref_key, "values": {}}
                prototypes[name] = current_proto
            
            stack.append(name)
            continue
            
        if struct_end_re.match(line):
            if stack: stack.pop()
            if not stack: current_proto = None
            continue
            
        if current_proto and len(stack) == 1:
            kv_match = kv_re.match(line)
            if kv_match:
                key = kv_match.group(1)
                value = kv_match.group(2).strip().rstrip(',')
                try:
                    if '.' in value: current_proto["values"][key] = float(value)
                    else: current_proto["values"][key] = int(value)
                except ValueError:
                    if value.lower() == 'true': current_proto["values"][key] = True
                    elif value.lower() == 'false': current_proto["values"][key] = False
                    else: current_proto["values"][key] = value
    return prototypes

def resolve_inheritance(prototypes: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    resolved = {}
    def get_val(name, visited=None):
        if visited is None: visited = set()
        if name in visited or name not in prototypes: return {}
        visited.add(name)
        ref = prototypes[name].get("refkey")
        merged = get_val(ref, visited).copy() if ref else {}
        merged.update(prototypes[name]["values"])
        return merged
    for name in prototypes:
        resolved[name] = get_val(name)
    return resolved

def generate_mod_comparison_html(orig_resolved: Dict[str, Dict[str, Any]], patch_data: Dict[str, Dict[str, Any]], mod_name: str, output_path: str):
    diff_keys = ["Easy", "Medium", "Hard", "Stalker"]
    
    # Merge patch into original to get "Modded" state
    modded_resolved = {}
    for diff in diff_keys:
        modded_resolved[diff] = orig_resolved.get(diff, {}).copy()
        if diff in patch_data:
            modded_resolved[diff].update(patch_data[diff]["values"])

    # Get all potential parameters
    all_keys = set()
    for diff in diff_keys:
        all_keys.update(orig_resolved.get(diff, {}).keys())
        if diff in modded_resolved:
            all_keys.update(modded_resolved[diff].keys())

    # Filter keys: Keep only if they were changed in at least one difficulty
    display_keys = []
    for attr in sorted(all_keys):
        if attr in NEUTRAL_ATTRIBUTES: continue
        
        has_change = False
        for diff in diff_keys:
            orig_val = orig_resolved.get(diff, {}).get(attr)
            mod_val = modded_resolved.get(diff, {}).get(attr)
            if orig_val != mod_val:
                has_change = True
                break
        
        if has_change:
            display_keys.append(attr)

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{mod_name} Comparison</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #0a0a0c;
                --card-bg: #141418;
                --text: #e0e0e0;
                --text-dim: #a0a0a0;
                --accent: #b1621d;
                --green: #2ecc71;
                --red: #e74c3c;
                --blue: #3498db;
                --grey: #444;
                --border: #2a2a2e;
                --tooltip-bg: #222;
            }}
            body {{
                background-color: var(--bg); color: var(--text);
                font-family: 'Outfit', sans-serif; margin: 0; padding: 20px;
                display: flex; flex-direction: column; align-items: center; min-height: 100vh;
            }}
            header {{ text-align: center; margin-bottom: 30px; width: 100%; max-width: 1200px; }}
            h1 {{
                font-weight: 800; text-transform: uppercase; letter-spacing: 2px;
                margin: 0 0 10px 0; background: linear-gradient(90deg, #b1621d, #3a5b54);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem;
            }}
            .subtitle {{ color: var(--text-dim); font-size: 1.1rem; }}
            .legend {{ display: flex; gap: 20px; margin-bottom: 20px; font-size: 0.9rem; }}
            .legend-item {{ display: flex; align-items: center; gap: 8px; }}
            .box {{ width: 14px; height: 14px; border-radius: 3px; }}
            .table-container {{
                width: 98vw; max-width: 100%; overflow-x: auto;
                background: var(--card-bg); border-radius: 16px; border: 1px solid var(--border);
                box-shadow: 0 20px 40px rgba(0,0,0,0.5); margin-bottom: 40px;
            }}
            table {{ border-collapse: separate; border-spacing: 0; width: 100%; min-width: 1200px; }}
            th, td {{ padding: 16px 20px; text-align: left; border-bottom: 1px solid var(--border); box-sizing: border-box; }}
            th {{
                background: #1c1c22; font-weight: 600; color: var(--blue);
                text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1px;
                position: sticky; top: 0; z-index: 10;
            }}
            .sticky-col {{
                position: sticky; left: 0; background: #1c1c22; z-index: 5;
                min-width: 350px; max-width: 350px;
                border-right: 2px solid var(--border);
            }}
            th.sticky-col {{ z-index: 11; }}
            .attr-content {{ display: flex; align-items: center; justify-content: space-between; gap: 10px; width: 100%; }}
            .attr-name {{ font-weight: 500; color: var(--text); flex: 1; }}
            .info-icon {{ cursor: help; opacity: 0.4; transition: opacity 0.2s; position: relative; flex-shrink: 0; }}
            .info-icon:hover {{ opacity: 1; }}
            .info-icon::after {{
                content: attr(data-tooltip); position: absolute; left: 25px; top: 50%; transform: translateY(-50%);
                background: var(--tooltip-bg); color: white; padding: 8px 12px;
                border-radius: 8px; font-size: 0.8rem; width: 220px;
                visibility: hidden; opacity: 0; transition: opacity 0.3s;
                z-index: 100; pointer-events: none; text-transform: none;
                font-weight: 400; border: 1px solid var(--border);
            }}
            .info-icon:hover::after {{ visibility: visible; opacity: 1; }}
            .val-diff {{ display: flex; align-items: center; gap: 10px; }}
            .val-orig {{ font-size: 0.85rem; color: var(--text-dim); text-decoration: line-through; }}
            .val-mod {{ font-size: 1.1rem; font-weight: 600; }}
            .val-perc {{ font-size: 0.75rem; font-weight: 400; padding: 2px 6px; border-radius: 4px; }}
            .buff-text {{ color: var(--green); }}
            .nerf-text {{ color: var(--red); }}
            .buff-bg {{ background: rgba(46, 204, 113, 0.1); border: 1px solid rgba(46, 204, 113, 0.2); color: var(--green); }}
            .nerf-bg {{ background: rgba(231, 76, 60, 0.1); border: 1px solid rgba(231, 76, 60, 0.2); color: var(--red); }}
            .neutral-bg {{ background: rgba(255, 255, 255, 0.05); color: var(--text-dim); }}
            tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}
        </style>
    </head>
    <body>
        <header>
            <h1>{mod_name}: Mod Comparison</h1>
            <p class="subtitle">Showcasing Buffs and Nerfs relative to Original Stalker 2 Difficulty</p>
        </header>

        <div class="legend">
            <div class="legend-item"><div class="box" style="background: var(--green);"></div> <span><b>Buff:</b> Player is stronger / Game is easier</span></div>
            <div class="legend-item"><div class="box" style="background: var(--red);"></div> <span><b>Nerf:</b> Player is weaker / Game is harder</span></div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="sticky-col">Description</th>
                        {"".join(f"<th>{k}</th>" for k in diff_keys)}
                    </tr>
                </thead>
                <tbody>
    """

    for attr in display_keys:
        desc = ATTRIBUTE_DESCRIPTIONS.get(attr)
        display_text = desc if desc else attr
        info_svg = f'<span class="info-icon" data-tooltip="{attr}"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg></span>'
        
        html += f"<tr><td class='sticky-col'><div class='attr-content'><span class='attr-name'>{display_text}</span> {info_svg}</div></td>"
        
        for diff in diff_keys:
            orig_val = orig_resolved.get(diff, {}).get(attr)
            mod_val = modded_resolved.get(diff, {}).get(attr)
            
            is_changed = (orig_val != mod_val)
            
            if mod_val is None:
                html += "<td>-</td>"
                continue

            display_orig = str(orig_val) if orig_val is not None else "?"
            display_mod = str(mod_val)
            
            status_class = "neutral-bg"
            perc_str = ""

            if is_changed and isinstance(orig_val, (int, float)) and isinstance(mod_val, (int, float)):
                if orig_val != 0:
                    diff_perc = (mod_val / orig_val - 1) * 100
                    is_increase = mod_val > orig_val
                    is_pos = attr in POSITIVE_ATTRIBUTES
                    is_neg = attr in NEGATIVE_ATTRIBUTES
                    
                    is_buff = (is_increase and is_pos) or (not is_increase and is_neg)
                    is_nerf = (is_increase and is_neg) or (not is_increase and is_pos)
                    
                    if is_buff: status_class = "buff-bg"
                    elif is_nerf: status_class = "nerf-bg"
                    
                    icon = "↑" if is_increase else "↓"
                    perc_str = f"{icon} {abs(diff_perc):.1f}%"
                else:
                    status_class = "buff-bg" if attr in POSITIVE_ATTRIBUTES else "nerf-bg"
                    perc_str = "NEW"

            elif is_changed and isinstance(mod_val, bool):
                if "Disable" in attr or "Limit" in attr: is_buff = not mod_val
                else: is_buff = mod_val
                status_class = "buff-bg" if is_buff else "nerf-bg"
                perc_str = "CHANGED"

            html += "<td><div class='val-diff'>"
            if is_changed:
                html += f"<span class='val-orig'>{display_orig}</span>"
                html += f"<span class='val-mod {('buff-text' if 'buff' in status_class else 'nerf-text')}'>{display_mod}</span>"
                html += f"<span class='val-perc {status_class}'>{perc_str}</span>"
            else:
                html += f"<span class='val-mod' style='color: var(--text-dim)'>{display_mod}</span>"
            html += "</div></td>"
        html += "</tr>"

    html += """</tbody></table></div></body></html>"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated {output_path}")

def run_visualisation(orig_cfg_path: str, patch_cfg_path: str, mod_name: str, output_path: str):
    orig_prototypes = parse_cfg(orig_cfg_path)
    orig_resolved = resolve_inheritance(orig_prototypes)
    patch_prototypes = parse_cfg(patch_cfg_path)
    generate_mod_comparison_html(orig_resolved, patch_prototypes, mod_name, output_path)

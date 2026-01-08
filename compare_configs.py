import os
import re
import argparse
from patching_script_general import get_struct_content, get_value

# --- PRESETS ---
PRESETS = {
    "all": [
        "weaponSettings"
    ],
    "weaponSettings": {
        "orig": r"c:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData\WeaponData\CharacterWeaponSettingsPrototypes\NPCWeaponSettingsPrototypes.cfg",
        "patch": r"c:\dev\stalker2\mods\mods\LongRangeCombat\LongRangeCombat_P\Stalker2\Content\GameLite\GameData\WeaponData\CharacterWeaponSettingsPrototypes\NPCWeaponSettingsPrototypes\NPCWeaponSettingsPrototypes_patch_LongRangeCombat.cfg",
        "type": "npc_weapon_settings"
    }
}

# --- PARSERS ---

def parse_weapons_attributes(content):
    """Parses NPCWeaponAttributesPrototypes.cfg into a nested dictionary."""
    results = {}
    # Find all top-level SIDs
    sids = re.findall(r'^(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)
    
    for sid in sids:
        sid_content = get_struct_content(content, sid)
        if not sid_content: continue
        
        results[sid] = {}
        
        bt_content = get_struct_content(sid_content, "BehaviorTypes")
        if not bt_content: continue
        
        ranks = ["Newbie", "Experienced", "Veteran", "Master", "Zombie"]
        
        for rank in ranks:
            rank_content = get_struct_content(bt_content, rank)
            if not rank_content: 
                # Ensure rank key exists even if empty, for matrix completeness
                results[sid][rank] = {}
                continue
            
            results[sid][rank] = {}
            
            brackets = ["Short", "Medium", "Long"]
            for bracket in brackets:
                br_content = get_struct_content(rank_content, bracket)
                if not br_content: 
                    results[sid][rank][bracket] = {}
                    continue
                
                results[sid][rank][bracket] = {
                    "MinShots": get_value(br_content, "MinShots"),
                    "MaxShots": get_value(br_content, "MaxShots"),
                    "IgnoreDispersionMinShots": get_value(br_content, "IgnoreDispersionMinShots"),
                    "IgnoreDispersionMaxShots": get_value(br_content, "IgnoreDispersionMaxShots")
                }
    return results

def parse_npc_weapon_settings(content):
    """
    Parses NPCWeaponSettingsPrototypes.cfg.
    Extracts: DispersionRadius, BaseBleeding, ChanceBleedingPerShot
    """
    results = {}
    sids = re.findall(r'^(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)
    
    for sid in sids:
        sid_content = get_struct_content(content, sid)
        if not sid_content: continue
        
        results[sid] = {
            "DispersionRadius": get_value(sid_content, "DispersionRadius"),
            "BaseBleeding": get_value(sid_content, "BaseBleeding"),
            "ChanceBleedingPerShot": get_value(sid_content, "ChanceBleedingPerShot")
        }
    return results


# --- COMPARATORS ---

def get_attributes_comparison_data(orig_data, patch_data, limit=None):
    """
    Identifies SIDs with changes for NPCWeaponAttributesPrototypes.
    """
    comparisons = []
    count = 0
    
    # We only care about SIDs present in the patch
    for sid, patch_ranks in patch_data.items():
        if limit and count >= limit: break
        
        orig_ranks = orig_data.get(sid, {})
        has_changes = False
        
        # Structure: sid_data[rank][bracket][property] = {orig: X, patch: Y, is_changed: Bool}
        sid_data = {}

        ranks = ["Newbie", "Experienced", "Veteran", "Master", "Zombie"]
        brackets = ["Short", "Medium", "Long"]
        properties = ["MinShots", "MaxShots", "IgnoreDispersionMinShots", "IgnoreDispersionMaxShots"]

        for rank in ranks:
            sid_data[rank] = {}
            for bracket in brackets:
                sid_data[rank][bracket] = {}
                
                patch_vals = patch_ranks.get(rank, {}).get(bracket, {})
                orig_vals = orig_ranks.get(rank, {}).get(bracket, {})
                
                for prop in properties:
                    v_patch = patch_vals.get(prop)
                    v_orig = orig_vals.get(prop)
                    
                    is_changed = False
                    if v_patch is not None:
                        if v_orig is None: 
                            is_changed = False 
                        elif str(v_patch) != str(v_orig):
                            is_changed = True
                    
                    if is_changed:
                        has_changes = True

                    sid_data[rank][bracket][prop] = {
                        "orig": v_orig,
                        "patch": v_patch,
                        "is_changed": is_changed
                    }

        if has_changes:
            comparisons.append({
                "sid": sid,
                "data": sid_data,
                "type": "attributes"
            })
            count += 1
            
    return comparisons

def get_settings_comparison_data(orig_data, patch_data, limit=None):
    """
    Identifies SIDs with changes for NPCWeaponSettingsPrototypes.
    """
    comparisons = []
    count = 0
    
    properties = ["DispersionRadius", "BaseBleeding", "ChanceBleedingPerShot"]
    
    for sid, patch_props in patch_data.items():
        if limit and count >= limit: break
        
        orig_props = orig_data.get(sid, {})
        has_changes = False
        sid_data = {}
        
        for prop in properties:
            v_patch = patch_props.get(prop)
            v_orig = orig_props.get(prop)
            
            is_changed = False
            if v_patch is not None:
                # Special handling for percentage strings if needed, but string comparison works for now
                if v_orig is None:
                    is_changed = False # Inherited or missing in orig, assume no change if not explicit override
                elif str(v_patch) != str(v_orig):
                    is_changed = True
            
            if is_changed:
                has_changes = True
                
            sid_data[prop] = {
                "orig": v_orig,
                "patch": v_patch,
                "is_changed": is_changed
            }
            
        if has_changes:
            comparisons.append({
                "sid": sid,
                "data": sid_data,
                "type": "settings"
            })
            count += 1
            
    return comparisons

# --- HTML FORMATTERS ---

def format_html_report(comparisons, output_file):
    html = ["""<!DOCTYPE html>
<html>
<head>
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f0f2f5; color: #333; }
    .sid-block { background: white; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }
    .sid-header { background: #2c3e50; color: white; padding: 15px 20px; font-weight: 600; font-size: 1.25em; border-bottom: 3px solid #34495e; }
    
    table { width: 100%; border-collapse: collapse; font-size: 0.9em; table-layout: fixed; }
    th, td { padding: 10px 15px; text-align: center; border-bottom: 1px solid #f0f0f0; border-right: 1px solid #f0f0f0; }
    th { background-color: #f8f9fa; color: #6c757d; font-weight: 600; }
    
    .val-increased { background-color: #d4edda; color: #155724; font-weight: bold; border-left: 3px solid #28a745; }
    .val-decreased { background-color: #f8d7da; color: #721c24; font-weight: bold; border-left: 3px solid #dc3545; }
    .val-changed { background-color: #fff3cd; color: #856404; font-weight: bold; border-left: 3px solid #ffc107; }
    .val-new { background-color: #e2e3e5; color: #383d41; font-weight: bold; border-left: 3px solid #383d41; }
    
    .old-val { display: block; font-size: 0.75em; color: #999; text-decoration: line-through; }
    .new-val { display: block; font-size: 1.1em; }
    .unchanged-val { color: #555; }
    .badge { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; margin-left: 5px; }
</style>
</head>
<body>
<h1>Config Comparison Report</h1>
"""]

    for comp in comparisons:
        sid = comp["sid"]
        data = comp["data"]
        ctype = comp["type"]
        
        html.append(f'<div class="sid-block">')
        html.append(f'<div class="sid-header">{sid} <span style="font-size:0.8em; opacity:0.8">({ctype})</span></div>')
        
        if ctype == "attributes":
            # Existing matrix logic
            ranks = ["Newbie", "Experienced", "Veteran", "Master", "Zombie"]
            brackets = ["Short", "Medium", "Long"]
            prop_groups = [
                ("Burst", ["MinShots", "MaxShots"]),
                ("Dispersion", ["IgnoreDispersionMinShots", "IgnoreDispersionMaxShots"])
            ]
            
            for bracket in brackets:
                html.append(f'<div style="padding:10px;"><div style="font-weight:bold; margin-bottom:5px;">{bracket} Range</div>')
                html.append('<table><thead><tr><th>Group</th><th>Property</th>')
                for rank in ranks:
                    html.append(f'<th>{rank}</th>')
                html.append('</tr></thead><tbody>')
                
                for group_name, props in prop_groups:
                    first = True
                    for prop in props:
                        html.append('<tr>')
                        if first:
                            html.append(f'<td rowspan="{len(props)}" style="vertical-align:middle; background:#eef2f7;">{group_name}</td>')
                            first = False
                        html.append(f'<td style="text-align:left;">{prop}</td>')
                        
                        for rank in ranks:
                            cell_data = data[rank][bracket][prop]
                            html.append(render_cell(cell_data["orig"], cell_data["patch"], cell_data["is_changed"]))
                        html.append('</tr>')
                html.append('</tbody></table></div>')
                
        elif ctype == "settings":
            # Flat property list
            html.append('<table style="margin:0;"><thead><tr><th style="text-align:left;">Property</th><th>Original</th><th>Patch</th></tr></thead><tbody>')
            for prop, cell_data in data.items():
                html.append('<tr>')
                html.append(f'<td style="text-align:left; font-weight:bold;">{prop}</td>')
                # For this simple table, we can just render orig and patch columns separately or combine them
                # Let's combine to reuse the style logic or split them
                # Actually, the render_cell logic expects a single cell
                html.append(render_cell(cell_data["orig"], cell_data["patch"], cell_data["is_changed"], combine=False))
                html.append('</tr>')
            html.append('</tbody></table>')
            
        html.append('</div>')
    
    html.append("</body></html>")
    return "\n".join(html)

def render_cell(orig_val, patch_val, is_changed, combine=True):
    cell_class = ""
    content = ""
    
    if patch_val is None:
        content = '<span style="color:#ddd">-</span>'
    elif is_changed:
        if orig_val is not None:
            try:
                # Handle % signs for numbers
                p_clean = str(patch_val).replace('%', '')
                o_clean = str(orig_val).replace('%', '')
                p_num = float(p_clean)
                o_num = float(o_clean)
                
                if p_num > o_num: cell_class = "val-increased"
                elif p_num < o_num: cell_class = "val-decreased"
                else: cell_class = "val-changed"
            except (ValueError, TypeError):
                cell_class = "val-changed"
            
            if combine:
                content = f'<span class="old-val">{orig_val}</span><span class="new-val">{patch_val}</span>'
            else:
                # If not combining, we return two tds... wait, this function returns a single td string usually
                # To support splitting, we'd need to change structure. 
                # Let's just stick to combined for consistency with the other report style
                content = f'<span class="old-val">{orig_val}</span><span class="new-val">{patch_val}</span>'
        else:
            cell_class = "val-new"
            content = f'<span class="new-val">{patch_val}</span>'
    else:
        content = f'<span class="unchanged-val">{patch_val}</span>'

    if not combine:
        # Split mode for key-value table
        c1 = f'<td>{orig_val if orig_val is not None else "-"}</td>'
        c2 = f'<td class="{cell_class}">{patch_val if patch_val is not None else "-"}</td>'
        return c1 + c2
        
    return f'<td class="{cell_class}">{content}</td>'


def process_comparison(orig_path, patch_path, type_hint, limit=None):
    if not os.path.exists(orig_path):
        print(f"Error: Original file not found: {orig_path}")
        return []
    if not os.path.exists(patch_path):
        print(f"Error: Patch file not found: {patch_path}")
        return []

    print(f"Reading {os.path.basename(orig_path)}...")
    with open(orig_path, 'r', encoding='utf-8-sig') as f:
        orig_content = f.read()
        
    print(f"Reading {os.path.basename(patch_path)}...")
    with open(patch_path, 'r', encoding='utf-8-sig') as f:
        patch_content = f.read()

    if type_hint == "npc_weapon_settings":
        orig_data = parse_npc_weapon_settings(orig_content)
        patch_data = parse_npc_weapon_settings(patch_content)
        return get_settings_comparison_data(orig_data, patch_data, limit)
    
    elif type_hint == "npc_weapon_attributes":  
        # Default or inferred
        orig_data = parse_weapons_attributes(orig_content)
        patch_data = parse_weapons_attributes(patch_content)
        return get_attributes_comparison_data(orig_data, patch_data, limit)
        
    else:
        print(f"Unknown type: {type_hint}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Compare STALKER 2 config files.")
    parser.add_argument("preset", nargs="?", help="Preset name (e.g., 'weaponSettings') or 'all'")
    parser.add_argument("--orig", type=str, help="Path to original .cfg")
    parser.add_argument("--patch", type=str, help="Path to patched .cfg")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of compared nodes")
    parser.add_argument("--out", type=str, default="comparison_report.html", help="Output file")
    
    args = parser.parse_args()
    
    comparisons = []
    
    tasks = []
    
    if args.preset:
        if args.preset == "all":
             for p in PRESETS["all"]:
                 if p in PRESETS:
                     tasks.append(PRESETS[p])
        elif args.preset in PRESETS:
            tasks.append(PRESETS[args.preset])
        else:
            print(f"Error: Preset '{args.preset}' not found.")
            return
    elif args.orig and args.patch:
        # Try to infer type
        ctype = "npc_weapon_attributes"
        if "NPCWeaponSettings" in args.orig:
            ctype = "npc_weapon_settings"
            
        tasks.append({
            "orig": args.orig,
            "patch": args.patch,
            "type": ctype
        })
    else:
        parser.print_help()
        return

    for task in tasks:
        comps = process_comparison(task["orig"], task["patch"], task["type"], limit=args.limit)
        comparisons.extend(comps)
    
    print(f"Found differences in {len(comparisons)} items.")
    
    report = format_html_report(comparisons, args.out)
    
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"Report written to {args.out}")

if __name__ == "__main__":
    main()

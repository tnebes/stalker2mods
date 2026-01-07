import os
import re
import argparse
from patching_script_general import get_struct_content, get_value

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

def get_full_comparison_data(orig_data, patch_data, limit=None):
    """
    Identifies SIDs with changes and returns their FULL data (orig + patch)
    for all ranks/ranges/properties, to allow context visualization.
    """
    comparisons = []
    count = 0
    
    # We only care about SIDs present in the patch
    for sid, patch_ranks in patch_data.items():
        if limit and count >= limit: break
        
        orig_ranks = orig_data.get(sid, {})
        has_changes = False
        
        # Structure to hold full comparison data
        # sid_data[rank][bracket][property] = {orig: X, patch: Y, is_changed: Bool}
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
                    # Only consider it a change if we have values and they differ
                    if v_patch is not None:
                        if v_orig is None: 
                            # User Request: If original is missing, assume it hasn't changed (inherited)
                            is_changed = False 
                        elif str(v_patch) != str(v_orig): # Modified value
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
                "data": sid_data
            })
            count += 1
            
    return comparisons

def format_html_matrix_report(comparisons):
    html = ["""<!DOCTYPE html>
<html>
<head>
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f0f2f5; color: #333; }
    .sid-block { background: white; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }
    .sid-header { background: #2c3e50; color: white; padding: 15px 20px; font-weight: 600; font-size: 1.25em; border-bottom: 3px solid #34495e; }
    
    .range-section { padding: 0; }
    .range-header { background: #e9ecef; color: #495057; padding: 8px 15px; font-weight: bold; text-transform: uppercase; font-size: 0.85em; letter-spacing: 1px; border-top: 1px solid #dee2e6; border-bottom: 1px solid #dee2e6; }
    .range-header:first-child { border-top: none; }
    
    table { width: 100%; border-collapse: collapse; font-size: 0.9em; table-layout: fixed; }
    th, td { padding: 10px 15px; text-align: center; border-bottom: 1px solid #f0f0f0; border-right: 1px solid #f0f0f0; }
    th:last-child, td:last-child { border-right: none; }
    tr:last-child td { border-bottom: none; }
    
    th { background-color: #f8f9fa; color: #6c757d; font-weight: 600; }
    .group-col { width: 12%; text-align: center; font-weight: bold; color: #444; background: #eef2f7; vertical-align: middle; border-right: 2px solid #dde1e6; }
    .prop-col { width: 18%; text-align: left; font-weight: bold; color: #2c3e50; background: #fafafa; }
    
    .val-cell { position: relative; }
    .val-increased { background-color: #d4edda; color: #155724; font-weight: bold; border-left: 3px solid #28a745; }
    .val-decreased { background-color: #f8d7da; color: #721c24; font-weight: bold; border-left: 3px solid #dc3545; }
    .val-changed { background-color: #fff3cd; color: #856404; font-weight: bold; border-left: 3px solid #ffc107; }
    .val-new { background-color: #e2e3e5; color: #383d41; font-weight: bold; border-left: 3px solid #383d41; }
    
    .old-val { display: block; font-size: 0.75em; color: #999; text-decoration: line-through; margin-bottom: 2px; }
    .new-val { display: block; font-size: 1.1em; }
    .unchanged-val { color: #555; }
    .no-val { color: #ddd; font-style: italic; font-size: 0.8em; }
    
    .badge { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; margin-left: 5px; }

</style>
</head>
<body>
<h1>Config Comparison Matrix</h1>
<p style="color: #666; margin-bottom: 30px;">Comparison of NPC Weapon Attributes (Original vs Patch)</p>
<p style="font-size: 0.9em; margin-bottom: 20px;">
    <span class="badge" style="background: #d4edda; color: #155724; border: 1px solid #c3e6cb; padding: 2px 5px; border-radius: 3px;">Increased</span>
    <span class="badge" style="background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; padding: 2px 5px; border-radius: 3px;">Decreased</span>
    <span class="badge" style="background: #fff3cd; color: #856404; border: 1px solid #ffeeba; padding: 2px 5px; border-radius: 3px;">Changed</span>
</p>
"""]

    ranks = ["Newbie", "Experienced", "Veteran", "Master", "Zombie"]
    brackets = ["Short", "Medium", "Long"]
    
    # Groups for new layout
    prop_groups = [
        ("Burst", ["MinShots", "MaxShots"]),
        ("Dispersion", ["IgnoreDispersionMinShots", "IgnoreDispersionMaxShots"])
    ]

    for comp in comparisons:
        sid = comp["sid"]
        data = comp["data"]
        
        html.append(f'<div class="sid-block">')
        html.append(f'<div class="sid-header">{sid}</div>')
        
        for bracket in brackets:
            html.append(f'<div class="range-section">')
            html.append(f'<div class="range-header">{bracket} Range</div>')
            html.append('<table>')
            
            # Header Row
            html.append('<thead><tr><th>Group</th><th class="prop-col">Property</th>')
            for rank in ranks:
                html.append(f'<th>{rank}</th>')
            html.append('</tr></thead>')
            
            html.append('<tbody>')
            
            for group_name, props in prop_groups:
                first_in_group = True
                for prop in props:
                    html.append('<tr>')
                    if first_in_group:
                        html.append(f'<td class="group-col" rowspan="{len(props)}">{group_name}</td>')
                        first_in_group = False
                        
                    html.append(f'<td class="prop-col">{prop}</td>')
                    for rank in ranks:
                        cell_data = data[rank][bracket][prop]
                        patch_val = cell_data["patch"]
                        orig_val = cell_data["orig"]
                        is_changed = cell_data["is_changed"]
                        
                        cell_class = "val-cell"
                        content = ""
                        
                        if patch_val is None:
                             content = '<span class="no-val">-</span>'
                        elif is_changed:
                            if orig_val is not None:
                                # Determine direction
                                try:
                                    p_num = float(patch_val)
                                    o_num = float(orig_val)
                                    if p_num > o_num:
                                        cell_class += " val-increased"
                                    elif p_num < o_num:
                                        cell_class += " val-decreased"
                                    else:
                                        cell_class += " val-changed"
                                except (ValueError, TypeError):
                                    cell_class += " val-changed"
                                    
                                content = f'<span class="old-val">{orig_val}</span><span class="new-val">{patch_val}</span>'
                            else:
                                cell_class += " val-new"
                                content = f'<span class="new-val">{patch_val}</span>'
                        else:
                            content = f'<span class="unchanged-val">{patch_val}</span>'
                            
                        html.append(f'<td class="{cell_class}">{content}</td>')
                    html.append('</tr>')
            html.append('</tbody></table></div>')
            
        html.append('</div>') # End sid-block
    
    html.append("</body></html>")
    return "\n".join(html)

def main():
    parser = argparse.ArgumentParser(description="Compare STALKER 2 config files.")
    parser.add_argument("--orig", type=str, required=True, help="Path to original .cfg")
    parser.add_argument("--patch", type=str, required=True, help="Path to patched .cfg")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of compared nodes")
    parser.add_argument("--out", type=str, default="comparison_report.html", help="Output file")
    
    args = parser.parse_args()
    
    if "NPCWeaponAttributesPrototypes" not in args.orig:
        print("Error: Comparison for this file type is not implemented.")
        return

    print("Parsing original...")
    with open(args.orig, 'r', encoding='utf-8-sig') as f:
        orig_data = parse_weapons_attributes(f.read())
        
    print("Parsing patch...")
    with open(args.patch, 'r', encoding='utf-8-sig') as f:
        patch_data = parse_weapons_attributes(f.read())
    
    print("Comparing...")
    comparisons = get_full_comparison_data(orig_data, patch_data, limit=args.limit)
    print(f"Found differences in {len(comparisons)} items.")
    
    report = format_html_matrix_report(comparisons)
    
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"Report written to {args.out}")

if __name__ == "__main__":
    main()

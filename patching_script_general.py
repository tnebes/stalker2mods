import os
import re
import math

def round_to_nearest(val, nearest=0.5):
    """Rounds a value to the nearest increment (default 0.5)."""
    return round(val / nearest) * nearest

def is_special_npc(name):
    """Checks if an NPC/SID should be excluded based on common special names."""
    exclusions = ['Guard', 'Korshunov', 'Strelok', 'Scar', 'Duga']
    for exc in exclusions:
        if exc.lower() in name.lower():
            return True
    return False

def get_value(content, key):
    """Extracts a numerical or string value from a config block."""
    match = re.search(rf'{key}\s*=\s*([\d\.\w\-%\'\/]+)', content, re.IGNORECASE)
    if not match:
        return None
    val_str = match.group(1).lower().replace('f', '')
    
    # Handle percentages
    if '%' in val_str:
        try:
            return float(val_str.replace('%', '')) / 100.0
        except ValueError:
            return val_str
            
    # Handle floats/ints
    try:
        if '.' in val_str:
            return float(val_str)
        return int(val_str)
    except ValueError:
        return val_str

def get_inheritance_tree(file_path):
    """Builds a child -> parent mapping from a .cfg file."""
    tree = {}
    # Matches struct name and captures the refkey value if present within braces
    pattern = re.compile(r'^\s*(\w+)\s*:\s*struct\.begin(?:\s*\{.*refkey\s*=\s*(\w+).*\})?', re.MULTILINE | re.IGNORECASE)
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
        for match in pattern.finditer(content):
            struct_name = match.group(1)
            parent_name = match.group(2)
            tree[struct_name] = parent_name
    return tree

def find_all_inheritors(tree, base_struct):
    """Recursively finds all structs that inherit from base_struct."""
    inheritors = set()
    memo = {}

    def inherits_from(struct, target):
        if struct in memo: return memo[struct]
        if struct == target: return True
        parent = tree.get(struct)
        if not parent:
            res = False
        else:
            res = inherits_from(parent, target)
        memo[struct] = res
        return res

    for struct in tree:
        if struct != base_struct and inherits_from(struct, base_struct):
            inheritors.add(struct)
            
    return inheritors

def get_struct_content(file_content, struct_name):
    """Returns the full string content of a struct definition, handling indentation."""
    pattern = re.compile(rf'^\s*{struct_name}\s*:\s*struct\.begin', re.MULTILINE | re.IGNORECASE)
    match = pattern.search(file_content)
    if not match:
        return None
    
    start_pos = match.start()
    brace_level = 0
    content_slice = file_content[start_pos:]
    
    markers = re.finditer(r'struct\.begin|struct\.end', content_slice, re.IGNORECASE)
    for m in markers:
        if m.group().lower() == 'struct.begin':
            brace_level += 1
        else:
            brace_level -= 1
        
        if brace_level == 0:
            return content_slice[:m.end()]
            
    return None

def has_nested_node(file_content, struct_name, node_path):
    """Checks if a struct contains a nested node path."""
    current_content = get_struct_content(file_content, struct_name)
    if not current_content:
        return False
    
    for node in node_path:
        node_pattern = re.compile(rf'^\s*{node}\s*:\s*struct\.begin', re.MULTILINE | re.IGNORECASE)
        match = node_pattern.search(current_content)
        if not match:
            return False
        
        brace_level = 0
        markers = re.finditer(r'struct\.begin|struct\.end', current_content[match.start():], re.IGNORECASE)
        found_end = False
        for m in markers:
            if m.group().lower() == 'struct.begin':
                brace_level += 1
            else:
                brace_level -= 1
            if brace_level == 0:
                current_content = current_content[match.start() : match.start() + m.end()]
                found_end = True
                break
        if not found_end: return False
        
    return True

def generate_bpatch(struct_name, nested_path=None, values=None, direct_properties=None, root_properties=None):
    """
    Generates a {bpatch} block.
    If nested_path is provided, direct_properties and values apply at the end of that path.
    root_properties always apply at the first level of the struct.
    """
    lines = [f"{struct_name} : struct.begin {{bpatch}}"]
    
    # Add root properties first
    if root_properties:
        for k, v in root_properties.items():
            lines.append(f"   {k} = {v}")

    indent = "   "
    
    # Traverse nested path
    if nested_path:
        for node in nested_path:
            # Check if node already has {bpatch} or struct.begin in it, otherwise add it
            if "struct.begin" not in node:
                lines.append(f"{indent}{node} : struct.begin {{bpatch}}")
            else:
                lines.append(f"{indent}{node}")
            indent += "   "

    # Add properties at current (possibly nested) indentation
    if direct_properties:
        for k, v in direct_properties.items():
            lines.append(f"{indent}{k} = {v}")

    # Add array elements at current indentation
    if values:
        for val in values:
            if val.strip().startswith("[*]"):
                lines.append(f"{indent}{val.strip()}")
            else:
                lines.append(f"{indent}[*] = {val}")
    
    # Close nested blocks
    if nested_path:
        for i in range(len(nested_path), 0, -1):
            close_indent = "   " * i
            lines.append(f"{close_indent}struct.end")
        
    lines.append("struct.end")
    return "\n".join(lines)

class ModPatcher:
    def __init__(self, source_dump_dir, mod_output_dir):
        self.source_dump = source_dump_dir
        self.mod_root = mod_output_dir
        self.global_tree = {}
        self.file_contents = {}
        self.struct_to_file = {}
        self.patches = {} # filename -> list of patch strings

    def load_files(self, relative_paths):
        """Loads files, builds inheritance tree, and maps structs."""
        for rel_path in relative_paths:
            abs_path = os.path.join(self.source_dump, rel_path)
            if not os.path.exists(abs_path):
                print(f"Warning: {abs_path} not found.")
                continue
            
            filename = os.path.basename(rel_path)
            tree = get_inheritance_tree(abs_path)
            self.global_tree.update(tree)
            
            with open(abs_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                self.file_contents[filename] = content
                for struct_name in tree.keys():
                    self.struct_to_file[struct_name] = (filename, rel_path)

    def get_all_inheritors(self, base_struct):
        inheritors = find_all_inheritors(self.global_tree, base_struct)
        inheritors.add(base_struct)
        return sorted(list(inheritors))

    def add_patch(self, filename, patch_text):
        if filename not in self.patches:
            self.patches[filename] = []
        self.patches[filename].append(patch_text)

    def save_all(self, mod_name_suffix):
        if not self.patches:
            print("No patches generated.")
            return

        for filename, patches in self.patches.items():
            base_name = os.path.splitext(filename)[0]
            
            # Find the relative path from struct_to_file mapping or use first match
            rel_dir = ""
            for s, (fname, fpath) in self.struct_to_file.items():
                if fname == filename:
                    rel_dir = os.path.dirname(fpath)
                    break
            
            target_dir = os.path.join(self.mod_root, rel_dir, base_name)
            os.makedirs(target_dir, exist_ok=True)
            
            target_file = os.path.join(target_dir, f"{base_name}_patch_{mod_name_suffix}.cfg")
            print(f"Writing {len(patches)} patches to {target_file}...")
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write("\n\n".join(patches))
        print("Success.")

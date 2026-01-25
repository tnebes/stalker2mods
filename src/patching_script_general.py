import os
import re
import math
import cfg_ast

def round_to_nearest(val, nearest=0.5):
    """Rounds a value to the nearest increment (default 0.5)."""
    return round(val / nearest) * nearest

def parse_cfg_value(val_str, preserve_case=True):
    """Parses a CFG value string into float, int, or string."""
    if val_str is None: return None
    # Strip inline comments
    s = val_str.split("//")[0].strip()
    if not s: return val_str # If nothing left, return original
    
    # Handle percentages
    if '%' in s:
        try:
            return float(s.replace('%', '').replace('f', '')) / 100.0
        except ValueError:
            pass
            
    # Handle floats/ints
    try:
        clean_val = s.lower().replace('f', '')
        if '.' in clean_val:
            return float(clean_val)
        return int(clean_val)
    except ValueError:
        return val_str if preserve_case else val_str.lower()

def get_value(content, key, preserve_case=True):
    """Compatibility wrapper: Parses content as AST and extracts a value."""
    # This is slightly inefficient but ensures compatibility
    nodes = cfg_ast.parse_cfg(content)
    # Search top-level properties and recursively nested ones
    for node in nodes:
        if isinstance(node, cfg_ast.PropertyNode) and node.key.lower() == key.lower():
            val_str = node.value
            try:
                clean_val = val_str.lower().replace('f', '')
                if '%' in clean_val:
                    return float(clean_val.replace('%', '')) / 100.0
                if '.' in clean_val:
                    return float(clean_val)
                return int(clean_val)
            except ValueError:
                return val_str if preserve_case else val_str.lower()
        if isinstance(node, cfg_ast.StructNode):
            prop = node.find_child(key, recursive=True)
            if prop and isinstance(prop, cfg_ast.PropertyNode):
                val_str = prop.value
                try:
                    clean_val = val_str.lower().replace('f', '')
                    # ... (same logic as above)
                    if '%' in clean_val:
                        return float(clean_val.replace('%', '')) / 100.0
                    if '.' in clean_val:
                        return float(clean_val)
                    return int(clean_val)
                except ValueError:
                    return val_str if preserve_case else val_str.lower()
    return None

def get_struct_content(file_content, struct_name):
    """Compatibility wrapper: Extracts a struct's serialized CFG string."""
    nodes = cfg_ast.parse_cfg(file_content)
    for node in nodes:
        if isinstance(node, cfg_ast.StructNode) and node.name.lower() == struct_name.lower():
            return node.to_cfg()
        if isinstance(node, cfg_ast.StructNode):
            child = node.find_child(struct_name, recursive=True)
            if child and isinstance(child, cfg_ast.StructNode):
                return child.to_cfg()
    return None

def has_nested_node(file_content, struct_name, node_path):
    """Compatibility wrapper: Checks for nested path in a struct's content."""
    content = get_struct_content(file_content, struct_name)
    if not content: return False
    
    # We can use the logic from our node hierarchy
    nodes = cfg_ast.parse_cfg(content)
    if not nodes: return False
    root = nodes[0] if isinstance(nodes[0], cfg_ast.StructNode) else None
    if not root: return False
    
    curr = root
    for node_name in node_path:
        found = False
        for child in curr.children:
            if isinstance(child, cfg_ast.StructNode) and child.name.lower() == node_name.lower():
                curr = child
                found = True
                break
        if not found: return False
    return True

def is_special_npc(name):
    """Checks if an NPC/SID should be excluded based on common special names."""
    exclusions = ['Guard', 'Korshunov', 'Strelok', 'Scar', 'Duga']
    for exc in exclusions:
        if exc.lower() in name.lower():
            return True
    return False

def get_value(content, key, preserve_case=True):
    """Extracts a numerical or string value from a config block."""
    match = re.search(rf'{key}\s*=\s*([\d\.\w\-%\'\/]+)', content, re.IGNORECASE)
    if not match:
        return None
    val_str = match.group(1)
    
    # Handle percentages
    if '%' in val_str:
        try:
            return float(val_str.lower().replace('%', '').replace('f', '')) / 100.0
        except ValueError:
            return val_str
            
    # Handle floats/ints
    try:
        clean_val = val_str.lower().replace('f', '')
        if '.' in clean_val:
            return float(clean_val)
        return int(clean_val)
    except ValueError:
        return val_str if preserve_case else val_str.lower()

def get_inheritance_tree(file_path):
    """Builds a child -> parent mapping from a .cfg file."""
    tree = {}
    # Matches struct name and captures the refkey value if present within braces
    # Uses a more robust pattern to find refkey regardless of other attributes like refurl
    pattern = re.compile(r'^\s*(\w+)\s*:\s*struct\.begin(?:\s*\{[^{}]*?refkey\s*=\s*(\w+)[^{}]*\})?', re.MULTILINE | re.IGNORECASE)
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
        for match in pattern.finditer(content):
            struct_name = match.group(1)
            parent_name = match.group(2)
            if parent_name:
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

def find_node_path(struct_content, target_key, target_parent=None):
    """
    Finds the hierarchical path (list of node names) to a target key within a struct.
    If target_parent is specified, it returns the path where target_key is under that parent.
    """
    # Find all struct.begin, struct.end, and key= markers
    begin_pat = re.compile(r'^\s*(\w+)\s*:\s*struct\.begin', re.MULTILINE | re.IGNORECASE)
    end_pat = re.compile(r'^\s*struct\.end', re.MULTILINE | re.IGNORECASE)
    key_pat = re.compile(r'^\s*(\w+)\s*=', re.MULTILINE | re.IGNORECASE)

    all_markers = []
    for m in begin_pat.finditer(struct_content):
        all_markers.append({'type': 'begin', 'name': m.group(1), 'pos': m.start()})
    for m in end_pat.finditer(struct_content):
        all_markers.append({'type': 'end', 'pos': m.start()})
    for m in key_pat.finditer(struct_content):
        all_markers.append({'type': 'key', 'name': m.group(1), 'pos': m.start()})

    all_markers.sort(key=lambda x: x['pos'])

    current_path = []
    found_paths = []

    for marker in all_markers:
        if marker['type'] == 'begin':
            current_path.append(marker['name'])
        elif marker['type'] == 'end':
            if current_path:
                current_path.pop()
        elif marker['type'] == 'key':
            if marker['name'].lower() == target_key.lower():
                if target_parent:
                    # Check if target_parent is anywhere in the stack
                    if any(p.lower() == target_parent.lower() for p in current_path):
                        found_paths.append(list(current_path))
                else:
                    found_paths.append(list(current_path))

    if not found_paths:
        return None

    # Return the first matching path
    return found_paths[0]

def generate_bpatch(struct_name, nested_path=None, values=None, direct_properties=None, root_properties=None, bpatch_until=None):
    """
    Generates a {bpatch} block string.
    bpatch_until: Number of levels (including root) that should have {bpatch}.
    """
    total_levels = 1 + (len(nested_path) if nested_path else 0)
    limit = bpatch_until if bpatch_until is not None else total_levels
    
    root_bpatch = " {bpatch}" if limit >= 1 else ""
    lines = [f"{struct_name} : struct.begin{root_bpatch}"]
    
    if root_properties:
        for k, v in root_properties.items():
            lines.append(f"   {k} = {v}")

    indent = "   "
    if nested_path:
        for i, node in enumerate(nested_path):
            # level index is i+2 (root is 1, first nested is 2)
            level = i + 2
            bpatch_str = " {bpatch}" if level <= limit else ""
            lines.append(f"{indent}{node} : struct.begin{bpatch_str}")
            indent += "   "

    if direct_properties:
        for k, v in direct_properties.items():
            lines.append(f"{indent}{k} = {v}")

    if values:
        for val in values:
            if val.strip().startswith("[*]"):
                lines.append(f"{indent}{val.strip()}")
            else:
                lines.append(f"{indent}[*] = {val}")
    
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
        self.file_asts = {} # filename -> list of Nodes
        self.struct_to_file = {}
        self.filename_to_rel_path = {}
        self.patches = {} # filename -> list of patch strings

    def load_files(self, relative_paths):
        """Loads files as ASTs, builds inheritance tree, and maps structs."""
        for rel_path in relative_paths:
            abs_path = os.path.join(self.source_dump, rel_path)
            if not os.path.exists(abs_path):
                print(f"Warning: {abs_path} not found.")
                continue
            
            filename = os.path.basename(rel_path)
            self.global_tree.update(get_inheritance_tree(abs_path))
            
            with open(abs_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                self.file_asts[filename] = cfg_ast.parse_cfg(content)
                self.filename_to_rel_path[filename] = rel_path
                for node in self.file_asts[filename]:
                    if isinstance(node, cfg_ast.StructNode):
                        self.struct_to_file[node.name] = (filename, rel_path)

    def get_struct(self, struct_name, filename_hint=None):
        """Finds a struct node by name. Uses filename_hint for faster lookup if provided."""
        if filename_hint and filename_hint in self.file_asts:
            for node in self.file_asts[filename_hint]:
                if isinstance(node, cfg_ast.StructNode) and node.name.lower() == struct_name.lower():
                    return node
        
        # Global search
        for f in self.file_asts.keys():
            if f == filename_hint: continue
            for node in self.file_asts[f]:
                if isinstance(node, cfg_ast.StructNode) and node.name.lower() == struct_name.lower():
                    return node
        return None

    def get_property_value(self, struct_name, key, filename_hint=None):
        """Finds a property value in a struct, searching inheritance tree globaly."""
        curr = struct_name
        visited = set()
        while curr and curr not in visited:
            visited.add(curr)
            # Search globally for the struct
            node = self.get_struct(curr, filename_hint if curr == struct_name else None)
            if node:
                # Find child recursively handles nested properties
                prop = node.find_child(key, recursive=True)
                if prop and isinstance(prop, cfg_ast.PropertyNode):
                    return parse_cfg_value(prop.value)
            
            parent_name = self.global_tree.get(curr)
            if not parent_name: break
            curr = parent_name
        return None

    def get_all_inheritors(self, base_struct):
        inheritors = find_all_inheritors(self.global_tree, base_struct)
        inheritors.add(base_struct)
        return sorted(list(inheritors))

    def add_patch(self, filename, patch_text):
        if filename not in self.patches:
            self.patches[filename] = []
        self.patches[filename].append(patch_text)

    def has_property_path(self, struct_name, path, filename=None):
        """Checks if a struct contains a specific nested path."""
        root = self.get_struct(struct_name, filename)
        if not root: return False
        
        curr = root
        for node_name in path:
            found = False
            for child in curr.children:
                if isinstance(child, cfg_ast.StructNode) and child.name.lower() == node_name.lower():
                    curr = child
                    found = True
                    break
            if not found: return False
        return True

    def smart_add_patch(self, filename, struct_name, key, value, parent_node=None):
        """
        Automatically finds the path to the key within the struct and generates a {bpatch}.
        """
        root_struct = self.get_struct(struct_name, filename)
        if not root_struct:
            return False
            
        # Recursive search for the key, optionally under a specific parent
        def find_path(node, target_key, target_parent=None, current_path=None):
            if current_path is None: current_path = []
            
            # Check properties in this node
            for child in node.children:
                if isinstance(child, cfg_ast.PropertyNode) and child.key.lower() == target_key.lower():
                    if target_parent:
                        if any(p.lower() == target_parent.lower() for p in current_path):
                            return current_path
                    else:
                        return current_path
                
                if isinstance(child, cfg_ast.StructNode):
                    res = find_path(child, target_key, target_parent, current_path + [child.name])
                    if res is not None:
                        return res
            return None

        path = find_path(root_struct, key, parent_node)
        if path is None:
            # If not found directly, check inheritance tree for the key's location
            curr = struct_name
            visited = set()
            while curr and curr not in visited:
                visited.add(curr)
                parent_name = self.global_tree.get(curr)
                if not parent_name: break
                parent_struct = self.get_struct(parent_name)
                if parent_struct:
                    path = find_path(parent_struct, key, parent_node)
                    if path is not None:
                        break
                curr = parent_name

        if path is None:
            return False

        # Generate the patch using the discovered path
        # Note: we use our existing generate_bpatch for simplicity, 
        # but it could also be done via AST nodes if we wanted to be 100% AST.
        patch_text = generate_bpatch(struct_name, nested_path=path, direct_properties={key: value})
        self.add_patch(filename, patch_text)
        return True

    def save_all(self, mod_name_suffix):
        if not self.patches:
            print("No patches generated.")
            return

        for filename, patches in self.patches.items():
            base_name = os.path.splitext(filename)[0]
            rel_path = self.filename_to_rel_path.get(filename, "")
            rel_dir = os.path.dirname(rel_path) if rel_path else ""
            
            target_dir = os.path.join(self.mod_root, rel_dir, base_name)
            os.makedirs(target_dir, exist_ok=True)
            
            target_file = os.path.join(target_dir, f"{base_name}_patch_{mod_name_suffix}.cfg")
            print(f"Writing {len(patches)} patches to {target_file}...")
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write("\n\n".join(patches))
        print("Success.")

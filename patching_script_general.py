import os
import re

def get_inheritance_tree(file_path):
    """
    Builds a child -> parent mapping from a .cfg file.
    Handles {refkey=...} as parent within the same file.
    """
    tree = {}
    pattern = re.compile(r'^(\w+)\s*:\s*struct\.begin(?:\s*\{.*refkey=(\w+)\})?', re.MULTILINE | re.IGNORECASE)
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
        for match in pattern.finditer(content):
            struct_name = match.group(1)
            parent_name = match.group(2)
            tree[struct_name] = parent_name
    return tree

def find_all_inheritors(tree, base_struct):
    """
    Recursively finds all structs that inherit from base_struct.
    """
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
    """
    Returns the full string content of a struct definition from SID start to struct.end.
    """
    pattern = re.compile(rf'^{struct_name}\s*:\s*struct\.begin', re.MULTILINE | re.IGNORECASE)
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
    """
    Checks if a struct contains a nested node path.
    """
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

def has_property(file_content, struct_name, property_name):
    """
    Checks if a struct contains a specific property (key = value).
    """
    current_content = get_struct_content(file_content, struct_name)
    if not current_content:
        return False
    
    pattern = re.compile(rf'^\s*{property_name}\s*=', re.MULTILINE | re.IGNORECASE)
    return pattern.search(current_content) is not None

def check_node_in_chain(tree, file_content, struct_name, node_path):
    """
    Checks if a nested node path exists in the struct or any of its parents.
    """
    current = struct_name
    visited = set()
    while current and current not in visited:
        visited.add(current)
        if has_nested_node(file_content, current, node_path):
            return True
        current = tree.get(current)
    return False

def check_property_in_chain(tree, file_content, struct_name, property_name):
    """
    Checks if a property exists in the struct or any of its parents.
    """
    current = struct_name
    visited = set()
    while current and current not in visited:
        visited.add(current)
        if has_property(file_content, current, property_name):
            return True
        current = tree.get(current)
    return False

def generate_bpatch(struct_name, nested_path=None, values=None, direct_properties=None):
    """
    Generates a {bpatch} block.
    """
    lines = [f"{struct_name} : struct.begin {{bpatch}}"]
    
    if direct_properties:
        for k, v in direct_properties.items():
            lines.append(f"   {k} = {v}")

    if nested_path and values:
        indent = "   "
        for node in nested_path:
            lines.append(f"{indent}{node} : struct.begin {{bpatch}}")
            indent += "   "
        
        for val in values:
            lines.append(f"{indent}[*] = {val}")
        
        for i in range(len(nested_path)):
            close_indent = "   " * (len(nested_path) - i)
            lines.append(f"{close_indent}struct.end")
        
    lines.append("struct.end")
    return "\n".join(lines) + "\n"

def already_patched(patch_file_path, struct_name, values=None, properties=None):
    """
    Checks if a struct is already patched with values or properties.
    """
    if not os.path.exists(patch_file_path):
        return False
    
    with open(patch_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    struct_content = get_struct_content(content, struct_name)
    if not struct_content:
        return False
    
    if values:
        for val in values:
            if val not in struct_content:
                return False
    
    if properties:
        for k, v in properties.items():
            prop_pattern = re.compile(rf'^\s*{k}\s*=\s*{v}', re.MULTILINE | re.IGNORECASE)
            if not prop_pattern.search(struct_content):
                return False
                
    return True

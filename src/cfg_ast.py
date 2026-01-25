import re

class Node:
    def to_cfg(self, indent=0):
        raise NotImplementedError()

class PropertyNode(Node):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def to_cfg(self, indent=0):
        return f"{'   ' * indent}{self.key} = {self.value}"

class StructNode(Node):
    def __init__(self, name, attributes=None, children=None):
        self.name = name
        self.attributes = attributes or "" # e.g. "{bpatch}" or "{refkey=...}"
        self.children = children or []

    def to_cfg(self, indent=0):
        lines = []
        attr_str = f" {self.attributes}" if self.attributes else ""
        lines.append(f"{'   ' * indent}{self.name} : struct.begin{attr_str}")
        for child in self.children:
            lines.append(child.to_cfg(indent + 1))
        lines.append(f"{'   ' * indent}struct.end")
        return "\n".join(lines)

    def find_child(self, name, recursive=False):
        for child in self.children:
            if isinstance(child, StructNode) and child.name.lower() == name.lower():
                return child
            if isinstance(child, PropertyNode) and child.key.lower() == name.lower():
                return child
            if recursive and isinstance(child, StructNode):
                res = child.find_child(name, recursive=True)
                if res: return res
        return None

    def set_property(self, key, value):
        node = self.find_child(key)
        if node and isinstance(node, PropertyNode):
            node.value = value
        else:
            self.children.append(PropertyNode(key, value))

    def get_struct(self, name, create_if_missing=False, attrs_if_created=None):
        node = self.find_child(name)
        if node and isinstance(node, StructNode):
            return node
        if create_if_missing:
            new_struct = StructNode(name, attributes=attrs_if_created)
            self.children.append(new_struct)
            return new_struct
        return None

class ArrayNode(Node):
    def __init__(self, key, elements=None):
        self.key = key
        self.elements = elements or [] # List of (index_str, value)

    def to_cfg(self, indent=0):
        lines = []
        lines.append(f"{'   ' * indent}{self.key} : struct.begin")
        for idx, val in self.elements:
            lines.append(f"{'   ' * (indent + 1)}[{idx}] = {val}")
        lines.append(f"{'   ' * indent}struct.end")
        return "\n".join(lines)

class CommentNode(Node):
    def __init__(self, text):
        self.text = text

    def to_cfg(self, indent=0):
        return f"{'   ' * indent}{self.text}"

class CFGParser:
    def __init__(self, text):
        self.lines = text.splitlines()
        self.current_line_idx = 0

    def parse(self):
        nodes = []
        while self.current_line_idx < len(self.lines):
            node = self._parse_line()
            if node:
                nodes.append(node)
        return nodes

    def _parse_line(self):
        line = self.lines[self.current_line_idx].rstrip()
        self.current_line_idx += 1
        
        stripped = line.strip()
        if not stripped:
            return None
        
        if stripped.startswith("//"):
            return CommentNode(line)

        # Struct begin
        struct_match = re.match(r'^\s*([\w\[\]\*]+)\s*:\s*struct\.begin\s*(.*)', line, re.IGNORECASE)
        if struct_match:
            name = struct_match.group(1)
            attrs = struct_match.group(2).strip()
            children = []
            while self.current_line_idx < len(self.lines):
                next_line = self.lines[self.current_line_idx].strip()
                if next_line.lower() == "struct.end":
                    self.current_line_idx += 1
                    break
                child = self._parse_line()
                if child:
                    children.append(child)
            return StructNode(name, attrs, children)

        # Property
        prop_match = re.match(r'^\s*(\w+)\s*=\s*(.*)', line, re.IGNORECASE)
        if prop_match:
            return PropertyNode(prop_match.group(1), prop_match.group(2).strip())

        # Array element (if not caught by struct or property)
        # Actually, arrays in this game are often structs with [0] = ...
        # Let's see if we can just treat them as generic properties if they start with [
        if stripped.startswith("["):
            idx_match = re.match(r'^\s*\[(.*)\]\s*=\s*(.*)', line, re.IGNORECASE)
            if idx_match:
                return PropertyNode(f"[{idx_match.group(1)}]", idx_match.group(2).strip())

        return CommentNode(line) # Fallback

def parse_cfg(text):
    parser = CFGParser(text)
    return parser.parse()

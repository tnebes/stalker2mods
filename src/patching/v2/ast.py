import re

class Value:
    """Represents a value in a CFG file, preserving its original string representation if needed."""
    def __init__(self, raw_value):
        self.raw = str(raw_value)
    
    @property
    def is_float(self):
        return 'f' in self.raw.lower() or '.' in self.raw

    @property
    def is_percent(self):
        return '%' in self.raw

    def to_float(self):
        clean = self.raw.lower().replace('f', '').replace('%', '')
        try:
            val = float(clean)
            if self.is_percent:
                return val / 100.0
            return val
        except ValueError:
            return None

    def scale(self, factor):
        """Scales the numeric part of the value by a factor, preserving format."""
        val = self.to_float()
        if val is None:
            return self
        
        new_val = val * factor
        
        # Format back to string
        if self.is_percent:
            self.raw = f"{int(new_val * 100)}%"
        elif 'f' in self.raw.lower():
            # Try to preserve decimal precision if original had it, otherwise use .1f
            self.raw = f"{new_val:g}f"
            if '.' not in self.raw:
                self.raw = self.raw.replace('f', '.0f')
        elif '.' in self.raw:
            self.raw = f"{new_val:g}"
            if '.' not in self.raw:
                self.raw += ".0"
        else:
            self.raw = str(int(new_val))
        return self

    def __str__(self):
        return self.raw

    def __repr__(self):
        return f"Value({self.raw!r})"

class Node:
    def __init__(self):
        self.parent = None

    def to_cfg(self, indent=0):
        raise NotImplementedError()

class CommentNode(Node):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def to_cfg(self, indent=0):
        return f"{'   ' * indent}{self.text}"

class PropertyNode(Node):
    def __init__(self, key, value):
        super().__init__()
        self.key = key
        self.value = Value(value) if not isinstance(value, Value) else value

    @property
    def key_or_name(self):
        return self.key

    def scale(self, factor):
        return self.value.scale(factor)

    def to_cfg(self, indent=0):
        return f"{'   ' * indent}{self.key} = {self.value}"

class StructNode(Node):
    def __init__(self, name, attributes=None, children=None):
        super().__init__()
        self.name = name
        self.attributes = attributes or "" # e.g. "{bpatch}"
        self.children = children or []
        for child in self.children:
            child.parent = self

    def __getitem__(self, key):
        """Allows access via struct['KeyName']"""
        # First check for properties/structs by name
        for child in self.children:
            if isinstance(child, (PropertyNode, StructNode)) and child.key_or_name == key:
                return child
            if isinstance(child, ArrayNode) and child.key == key:
                return child
        raise KeyError(f"Node '{key}' not found in struct '{self.name}'")

    def __setitem__(self, key, value):
        """Allows assignment via struct['KeyName'] = node"""
        existing = self.find_child(key)
        if isinstance(value, (StructNode, PropertyNode, ArrayNode)):
            if existing:
                idx = self.children.index(existing)
                self.children[idx] = value
            else:
                self.children.append(value)
            value.parent = self
            # Ensure the name matches the key if it's a named node
            if hasattr(value, 'name'):
                value.name = key
            elif hasattr(value, 'key'):
                value.key = key
        else:
            # Assume it's a simple value assignment to a property
            self.set_property(key, value)

    def __delitem__(self, key):
        """Allows removal via del struct['KeyName']"""
        existing = self.find_child(key)
        if existing:
            # Instead of just removing, we might want to mark it as removenode
            # for the diff engine. But for the local tree, we just remove it.
            self.children.remove(existing)
        else:
            raise KeyError(f"Node '{key}' not found in struct '{self.name}'")

    def __iter__(self):
        """Allows iterating over children"""
        return iter(self.children)

    def __contains__(self, key):
        """Allows checking if a child exists via 'Key' in struct"""
        return self.find_child(key) is not None

    @property
    def key_or_name(self):
        return self.name

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
            if isinstance(child, (StructNode, PropertyNode, ArrayNode)):
                curr_name = getattr(child, 'name', getattr(child, 'key', None))
                if curr_name and curr_name.lower() == name.lower():
                    return child
            if recursive and isinstance(child, StructNode):
                res = child.find_child(name, recursive=True)
                if res: return res
        return None

    def set_property(self, key, value):
        existing = self.find_child(key)
        if existing and isinstance(existing, PropertyNode):
            existing.value = Value(value) if not isinstance(value, Value) else value
        else:
            new_node = PropertyNode(key, value)
            new_node.parent = self
            self.children.append(new_node)

class ArrayNode(Node):
    """Note: In STALKER 2, arrays are often just structs where keys are [0], [1], [*]."""
    def __init__(self, key, elements=None):
        super().__init__()
        self.key = key
        self.elements = elements or [] # List of ArrayElementNode
        for el in self.elements:
            el.parent = self

    def to_cfg(self, indent=0):
        lines = []
        lines.append(f"{'   ' * indent}{self.key} : struct.begin")
        for el in self.elements:
            lines.append(el.to_cfg(indent + 1))
        lines.append(f"{'   ' * indent}struct.end")
        return "\n".join(lines)

class ArrayElementNode(Node):
    def __init__(self, index, value):
        super().__init__()
        self.index = index # e.g. "0" or "*"
        self.value = Value(value) if not isinstance(value, Value) else value

    def to_cfg(self, indent=0):
        return f"{'   ' * indent}[{self.index}] = {self.value}"

class CFGDocument:
    def __init__(self, nodes=None, original_rel_path=None):
        self.nodes = nodes or []
        self.original_rel_path = original_rel_path
        for node in self.nodes:
            node.parent = self

    def to_cfg(self):
        return "\n".join(node.to_cfg(0) for node in self.nodes)

    def get_struct(self, name):
        for node in self.nodes:
            if isinstance(node, StructNode) and node.name.lower() == name.lower():
                return node
        return None

import os
from .parser import parse_cfg
from .ast import CFGDocument, StructNode, PropertyNode, ArrayNode, ArrayElementNode, Value

DEFAULT_DUMP_DIR = r"C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData"

class NodeFactory:
    """Helper to create nodes easily."""
    @staticmethod
    def create(name, content, attributes="", format_hint=None):
        if isinstance(content, list):
            # Assume it's an array if content is a list of tuples or values
            elements = []
            for item in content:
                if isinstance(item, tuple) and len(item) == 2:
                    elements.append(ArrayElementNode(item[0], item[1]))
                else:
                    elements.append(ArrayElementNode("*", item))
            return ArrayNode(name, elements)
        elif isinstance(content, dict):
            # Assume it's a struct
            children = []
            for k, v in content.items():
                if isinstance(v, (StructNode, PropertyNode, ArrayNode)):
                    children.append(v)
                else:
                    children.append(PropertyNode(k, Value(v, format_hint)))
            return StructNode(name, attributes, children)
        else:
            # Property
            return PropertyNode(name, Value(content, format_hint))

def load_configuration(path, base_dump_path=DEFAULT_DUMP_DIR):
    """
    Loads a configuration file. 
    If path is relative, it tries to find it within base_dump_path.
    """
    original_rel_path = path
    if not os.path.isabs(path):
        # Try to find it in the dump
        abs_path = os.path.join(base_dump_path, path)
        if not os.path.exists(abs_path):
            # Try stripping common prefixes if provided in the rel path
            alt_path = path
            for prefix in ["Content/GameLite/GameData/", "Stalker2/Content/GameLite/GameData/"]:
                if alt_path.replace("\\", "/").startswith(prefix):
                    alt_path = alt_path[len(prefix):]
                    break
            
            abs_path = os.path.join(base_dump_path, alt_path)
            if not os.path.exists(abs_path):
                raise FileNotFoundError(
                    f"Configuration file not found at '{path}' or '{abs_path}'.\n"
                    f"Please ensure your CFG dump is located at '{base_dump_path}' "
                    "or provide the absolute path to the file."
                )
            original_rel_path = alt_path
    else:
        abs_path = path
        # Try to calculate a relative path for help in patching later
        if abs_path.lower().startswith(base_dump_path.lower()):
            original_rel_path = abs_path[len(base_dump_path):].lstrip("\\/")

    with open(abs_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    doc = parse_cfg(content)
    doc.original_rel_path = original_rel_path
    
    return CFGWrapper(doc)

class CFGWrapper:
    def __init__(self, doc):
        self.doc = doc

    def getNodeByName(self, name):
        node = self.doc.get_struct(name)
        if node:
            return NodeWrapper(node, self.doc)
        return None

    def to_cfg(self):
        return self.doc.to_cfg()

class NodeWrapper:
    def __init__(self, nodes, doc=None):
        if not isinstance(nodes, list):
            self.nodes = [nodes]
        else:
            self.nodes = nodes
        self.doc = doc

    @property
    def node(self):
        return self.nodes

    def to_float(self):
        """Returns the float value of the first node if possible."""
        n = self.nodes[0]
        if isinstance(n, PropertyNode):
            return n.value.to_float()
        if isinstance(n, ArrayElementNode):
            return n.value.to_float()
        return None

    def get_effective_node(self, key, resolve_doc=None):
        """
        Attempts to find a child node by key. 
        If not found in the current struct, follows 'refkey' inheritance.
        resolve_doc: Optional CFGDocument to use for inheritance resolution.
                     Highly recommended when scaling values to avoid cascading.
        """
        n = self.nodes[0]
        if not isinstance(n, StructNode):
            return None
        
        # 1. Try local
        if key in n:
            res = n[key]
            return NodeWrapper(res, self.doc)
        
        # 2. Try inherited
        parent_sid = n.get_parent_sid()
        doc_to_use = resolve_doc or self.doc
        if parent_sid and doc_to_use:
            parent_struct = doc_to_use.get_struct(parent_sid)
            if parent_struct:
                return NodeWrapper(parent_struct, doc_to_use).get_effective_node(key, resolve_doc=doc_to_use)
        
        return None

    def __getitem__(self, key):
        # Delegate to the first node in the list for simplicity in most cases
        res = self.nodes[0][key]
        if isinstance(res, (StructNode, PropertyNode, ArrayNode)):
            return NodeWrapper(res, self.doc)
        return res

    def __setitem__(self, key, value):
        target = self.nodes[0]
        if isinstance(value, (StructNode, PropertyNode, ArrayNode)):
            target[key] = value
        else:
            # Assume it's a value assignment to a property
            target.set_property(key, value)

    def set_property(self, key, value, format_hint=None):
        """Sets a property with an optional format hint."""
        for n in self.nodes:
            if isinstance(n, StructNode):
                n.set_property(key, Value(value, format_hint))

    def set_effective_property(self, key, value, original_node=None):
        """
        Sets a property, inheriting the format from original_node if provided.
        original_node can be another NodeWrapper or a raw Node.
        """
        hint = None
        if original_node:
            if isinstance(original_node, NodeWrapper):
                n = original_node.nodes[0]
            else:
                n = original_node
            
            # Extract format hint if we have a PropertyNode or ArrayElementNode
            if hasattr(n, 'value') and hasattr(n.value, 'format_hint'):
                hint = n.value.format_hint
        
        self.set_property(key, value, hint)

    def scale(self, factor):
        """Scales the value(s) in the wrapper if possible."""
        for n in self.nodes:
            if isinstance(n, PropertyNode):
                n.value.scale(factor)
            elif isinstance(n, ArrayElementNode):
                n.value.scale(factor)

    def __delitem__(self, key):
        for n in self.nodes:
            if isinstance(n, StructNode):
                del n[key]

    def __iter__(self):
        # If we have multiple nodes (like from a search), this might be ambiguous.
        # But for a single node wrapper, it iterates over children.
        if len(self.nodes) == 1 and isinstance(self.nodes[0], StructNode):
            return iter(NodeWrapper(child, self.doc) for child in self.nodes[0])
        return iter([])

    def __contains__(self, key):
        for n in self.nodes:
            if isinstance(n, StructNode) and key in n:
                return True
        return False

    @property
    def key_or_name(self):
        # Convenience to get the name of the first node
        return getattr(self.nodes[0], 'name', getattr(self.nodes[0], 'key', None))

    def to_cfg(self, indent=0):
        return "\n".join(n.to_cfg(indent) for n in self.nodes)

# Alias for user's convenience
Node = NodeFactory.create
BPATCH = "{bpatch}"

# Value formats
FLOAT = "float"
FLOAT_F = "float_f"
INT = "int"
PERCENT = "percent"
STRING = "string"

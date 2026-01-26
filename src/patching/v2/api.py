import os
from .parser import parse_cfg
from .ast import CFGDocument, StructNode, PropertyNode, ArrayNode, ArrayElementNode, Value

DEFAULT_DUMP_DIR = r"C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData"

class NodeFactory:
    """Helper to create nodes easily."""
    @staticmethod
    def create(name, content, attributes=""):
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
                    children.append(PropertyNode(k, v))
            return StructNode(name, attributes, children)
        else:
            # Property
            return PropertyNode(name, content)

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
            return NodeWrapper(node)
        return None

    def to_cfg(self):
        return self.doc.to_cfg()

class NodeWrapper:
    def __init__(self, nodes):
        if not isinstance(nodes, list):
            self.nodes = [nodes]
        else:
            self.nodes = nodes

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

    def __getitem__(self, key):
        # Delegate to the first node in the list for simplicity in most cases
        res = self.nodes[0][key]
        if isinstance(res, (StructNode, PropertyNode, ArrayNode)):
            return NodeWrapper(res)
        return res

    def __setitem__(self, key, value):
        target = self.nodes[0]
        if isinstance(value, (StructNode, PropertyNode, ArrayNode)):
            target[key] = value
        else:
            # Assume it's a value assignment to a property
            # If the property exists, we can use the value's scale if it's a multiplier
            # but usually it's just a direct set.
            target.set_property(key, value)

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
            return iter(NodeWrapper(child) for child in self.nodes[0])
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

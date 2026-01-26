import re
from .ast import CFGDocument, StructNode, PropertyNode, ArrayNode, ArrayElementNode, CommentNode

class CFGParser:
    def __init__(self, text):
        self.lines = text.splitlines()
        self.current_line_idx = 0

    def parse(self):
        nodes = []
        while self.current_line_idx < len(self.lines):
            node = self._parse_next()
            if node:
                nodes.append(node)
        return CFGDocument(nodes)

    def _parse_next(self):
        if self.current_line_idx >= len(self.lines):
            return None

        line = self.lines[self.current_line_idx]
        stripped = line.strip()
        self.current_line_idx += 1

        if not stripped:
            return CommentNode(line) # Keep empty lines as comments or empty strings

        if stripped.startswith("//"):
            return CommentNode(line)

        # Struct begin: Name : struct.begin {attributes}
        struct_match = re.match(r'^\s*([\w\[\]\*]+)\s*:\s*struct\.begin\s*(.*)', line, re.IGNORECASE)
        if struct_match:
            name = struct_match.group(1)
            attrs = struct_match.group(2).strip()
            children = []
            
            # Check if it's an array-like struct (starts with [)
            is_array = False
            
            while self.current_line_idx < len(self.lines):
                next_line = self.lines[self.current_line_idx].strip()
                if next_line.lower() == "struct.end":
                    self.current_line_idx += 1
                    break
                
                # Peek for array elements
                if re.match(r'^\s*\[([\w\*]+)\]\s*=', self.lines[self.current_line_idx], re.IGNORECASE):
                    is_array = True

                child = self._parse_next()
                if child:
                    children.append(child)
            
            if is_array:
                # Convert children to ArrayElementNodes if they look like [idx] = val
                elements = []
                for child in children:
                    if isinstance(child, PropertyNode) and child.key.startswith("[") and child.key.endswith("]"):
                        idx = child.key[1:-1]
                        elements.append(ArrayElementNode(idx, child.value))
                    else:
                        # Keep other things (comments) if possible? 
                        # For simplicity, we just take the elements for now.
                        pass
                return ArrayNode(name, elements)
            
            return StructNode(name, attrs, children)

        # Property: Key = Value
        prop_match = re.match(r'^\s*([\w\[\]\*]+)\s*=\s*(.*)', line, re.IGNORECASE)
        if prop_match:
            key = prop_match.group(1)
            value = prop_match.group(2).strip()
            # If value contains a comment, we should ideally separate it, but let's keep it simple for now
            if "//" in value:
                value = value.split("//")[0].strip()
            
            return PropertyNode(key, value)

        return CommentNode(line) # Fallback

def parse_cfg(text):
    return CFGParser(text).parse()

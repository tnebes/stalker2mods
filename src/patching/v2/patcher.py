import os
from .api import load_configuration, DEFAULT_DUMP_DIR
from .ast import CFGDocument, StructNode, PropertyNode, ArrayNode, ArrayElementNode

def diff_nodes(base_node, modified_node):
    """
    Compares two nodes and returns a new node containing only the differences,
    marked with {bpatch} if it's a struct.
    Returns None if there is no difference.
    """
    if type(base_node) != type(modified_node):
        # If type changed, we replace entirely (no bpatch here usually, or treat as new)
        return modified_node

    if isinstance(modified_node, PropertyNode):
        if str(base_node.value) != str(modified_node.value):
            return modified_node
        return None

    if isinstance(modified_node, ArrayNode):
        # Arrays are tricky. For now, if they differ at all, we might want to output the whole array
        # or use [*] if the user used it. 
        # STALKER 2 bpatching for arrays often involves [*] or specific indices.
        # If we take the approach of "if modified, keep it", let's compare elements.
        if len(base_node.elements) != len(modified_node.elements):
            return modified_node
        for b_el, m_el in zip(base_node.elements, modified_node.elements):
            if b_el.index != m_el.index or str(b_el.value) != str(m_el.value):
                return modified_node
        return None

    if isinstance(modified_node, StructNode):
        diff_children = []
        for m_child in modified_node.children:
            if not isinstance(m_child, (StructNode, PropertyNode, ArrayNode)):
                # Keep comments or other nodes if they exist? Maybe not for diff.
                continue
            
            # Find matching child in base
            b_child = base_node.find_child(getattr(m_child, 'name', getattr(m_child, 'key', None)))
            
            if not b_child:
                # New node
                diff_children.append(m_child)
            else:
                child_diff = diff_nodes(b_child, m_child)
                if child_diff:
                    diff_children.append(child_diff)
        
        if diff_children:
            # We have differences. Return a NEW struct node with {bpatch}.
            # As per user guidance, when patching we strip refkey/refurl as they are redundant.
            new_attrs = "{bpatch}"
            
            return StructNode(modified_node.name, new_attrs, diff_children)
        
        return None

    return None

class Patcher:
    def __init__(self, base_path=DEFAULT_DUMP_DIR):
        if not os.path.exists(base_path):
             raise FileNotFoundError(
                f"Base resources not found at '{base_path}'.\n"
                "Please specify the correct path to your config dump in the Patcher constructor."
            )
        self.base_path = base_path

    def generate_patch(self, rel_path, modified_doc):
        """
        Compares the modified_doc with the base file at rel_path.
        Returns a CFGDocument containing only the BPATCHed changes.
        """
        abs_base_path = os.path.join(self.base_path, rel_path)
        if not os.path.exists(abs_base_path):
            # If no base file, everything is new.
            return modified_doc

        base_cfg = load_configuration(abs_base_path, base_dump_path=self.base_path).doc
        patch_nodes = []

        for m_node in modified_doc.nodes:
            if isinstance(m_node, StructNode):
                b_node = base_cfg.get_struct(m_node.name)
                if b_node:
                    diff = diff_nodes(b_node, m_node)
                    if diff:
                        patch_nodes.append(diff)
                else:
                    # New top-level struct
                    patch_nodes.append(m_node)
            else:
                # For non-struct top level nodes (if any), just keep them for now
                patch_nodes.append(m_node)

        patch_doc = CFGDocument(patch_nodes)
        patch_doc.original_rel_path = rel_path
        return patch_doc

    def save_patch(self, mod_root, mod_name, rel_path=None, patch_doc=None, is_prototype=True):
        """
        Saves a patch document following the hierarchy rules in GUIDE.md.
        
        mod_root: Base path for the mod (e.g., 'C:\\dev\\stalker2\\mods\\mods\\SunnierZone\\SunnierZone_P')
        rel_path: Optional. If not provided, it tries to get it from patch_doc.
        """
        if rel_path is None:
            if hasattr(patch_doc, "original_rel_path") and patch_doc.original_rel_path:
                rel_path = patch_doc.original_rel_path
            else:
                raise ValueError(
                    "Relative path (rel_path) must be provided if patch_doc does not specify one."
                )

        # Stalker 2 mods usually root at 'Stalker2' inside the pak folder
        # We also need the full path starting from Content/
        
        game_data_marker = "GameData/"
        if game_data_marker in rel_path.replace("\\", "/"):
            parts = rel_path.replace("\\", "/").split(game_data_marker)
            internal_rel_path = os.path.join("Content/GameLite/GameData", parts[1])
        elif rel_path.replace("\\", "/").startswith("Content/"):
            internal_rel_path = rel_path
        else:
            # If it's just a filename or local path, assume it belongs in GameData
            internal_rel_path = os.path.join("Content/GameLite/GameData", rel_path)

        base_dir = os.path.join(mod_root, "Stalker2")
        
        rel_dir = os.path.dirname(internal_rel_path)
        filename = os.path.basename(internal_rel_path)
        base_name = os.path.splitext(filename)[0]
        
        if is_prototype:
            # Prototype CFGs go in a sub-folder named after the file
            target_dir = os.path.join(base_dir, rel_dir, base_name)
            target_file = f"{base_name}_patch_{mod_name}.cfg"
        else:
            # Standard CFGs go in the same directory
            target_dir = os.path.join(base_dir, rel_dir)
            target_file = f"{filename}_patch_{mod_name}"
            
        abs_target_dir = os.path.abspath(target_dir)
        os.makedirs(abs_target_dir, exist_ok=True)
        
        abs_target_path = os.path.join(abs_target_dir, target_file)
        
        print(f"Saving patch to: {abs_target_path}")
        with open(abs_target_path, 'w', encoding='utf-8') as f:
            f.write(patch_doc.to_cfg())
        
        return abs_target_path

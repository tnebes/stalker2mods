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
        
        # We need to handle duplicate child names (like [*]) correctly.
        # Simple name-based matching fails here.
        m_children = [c for c in modified_node.children if isinstance(c, (StructNode, PropertyNode, ArrayNode))]
        b_children = [c for c in base_node.children if isinstance(c, (StructNode, PropertyNode, ArrayNode))]

        # Map base children by name to detect duplicates
        from collections import Counter
        b_name_counts = Counter(getattr(c, 'name', getattr(c, 'key', None)) for c in b_children)
        
        # Track our current index for each name to match duplicates sequentially
        name_match_index = {}

        for m_child in m_children:
            name = getattr(m_child, 'name', getattr(m_child, 'key', None))
            
            # If this name appears multiple times in base, or it's a known anonymous key
            is_ambiguous = b_name_counts[name] > 1 or name == "[*]"
            
            b_child = None
            if is_ambiguous:
                # Find the N-th occurrence of this name
                start_idx = name_match_index.get(name, 0)
                for i in range(start_idx, len(b_children)):
                    curr_b = b_children[i]
                    if getattr(curr_b, 'name', getattr(curr_b, 'key', None)) == name:
                        b_child = curr_b
                        name_match_index[name] = i + 1
                        break
            else:
                # Unique name, use standard lookup
                b_child = base_node.find_child(name)

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

    def save_patch(self, mod_root, mod_name, rel_path=None, patch_doc=None, is_prototype=None, flatten=False):
        """
        Saves a patch document following the hierarchy rules in GUIDE.md.
        
        mod_root: Base path for the mod (e.g., 'C:\\dev\\stalker2\\mods\\mods\\SunnierZone\\SunnierZone_P')
        rel_path: Optional. If not provided, it tries to get it from patch_doc.
        is_prototype: If None (default), auto-detects based on filename. 
                      True if it ends with 'Prototype' or 'Prototypes'.
        flatten: If True, do not create a subfolder for prototype patches.
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
        
        # Auto-detect prototype status if not explicitly provided
        if is_prototype is None:
            is_prototype = any(base_name.endswith(suffix) for suffix in ["Prototype", "Prototypes"])

        if is_prototype:
            if flatten:
                # Prototype but flattened (stays in rel_dir)
                target_dir = os.path.join(base_dir, rel_dir)
            else:
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

    def save_override(self, mod_root, rel_path, doc):
        """
        Saves the FULL configuration document to the exact location and filename as the original.
        Used for 'bruteforce' overriding when standard patching fails.
        """
        # Determine internal path (Content/GameLite/GameData/...)
        game_data_marker = "GameData/"
        if game_data_marker in rel_path.replace("\\", "/"):
            parts = rel_path.replace("\\", "/").split(game_data_marker)
            internal_rel_path = os.path.join("Content/GameLite/GameData", parts[1])
        elif rel_path.replace("\\", "/").startswith("Content/"):
            internal_rel_path = rel_path
        else:
            internal_rel_path = os.path.join("Content/GameLite/GameData", rel_path)

        base_dir = os.path.join(mod_root, "Stalker2")
        target_path = os.path.join(base_dir, internal_rel_path)
        
        abs_target_dir = os.path.dirname(os.path.abspath(target_path))
        os.makedirs(abs_target_dir, exist_ok=True)
        
        print(f"OVERRIDING: {target_path}")
        with open(target_path, 'w', encoding='utf-8-sig') as f:
            f.write(doc.to_cfg())
        
        return target_path

    def inject_guardian(self, mod_root, mod_name, jump_stamina="100"):
        """
        Injects a 'Guardian' patch (blatant changes for testing) to confirm the mod is loading.
        Sets SprintSpeed and JumpSpeedCoef for the 'Player' SID in ObjPrototypes.cfg.
        """
        print(f"Injecting Guardian into ObjPrototypes (Player SID) for {mod_name}...")
        config_path = "ObjPrototypes.cfg"
        cfg = load_configuration(config_path, base_dump_path=self.base_path)
        player = cfg.getNodeByName("Player")
        if player:
            player['StaminaPerAction']['Jump'] = jump_stamina
            
            patch = self.generate_patch(config_path, cfg.doc)
            return self.save_patch(mod_root, mod_name, patch_doc=patch, is_prototype=True)
        else:
            print("WARNING: Player node not found for Guardian injection.")
            return None

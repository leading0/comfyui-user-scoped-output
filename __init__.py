import os
import nodes as _nodes
import folder_paths as _fp

# --- config: where to read the username from ---
ENV_KEYS = ("COMFY_USER", "REMOTE_USER", "X_FORWARDED_USER")

def _username_from_env():
    for k in ENV_KEYS:
        v = os.environ.get(k)
        if v:
            # basic sanitization to keep paths safe
            return v.strip().replace("\\", "_").replace("/", "_")
    return "Bob"

# Keep original __init__
_orig_init = _nodes.SaveImage.__init__

def _patched_init(self, *args, **kwargs):
    # run the real init first (sets output_dir, type, prefix_append, etc.)
    _orig_init(self, *args, **kwargs)

    user = _username_from_env()
    if not user:
        return

    # Determine the base output directory
    base = getattr(self, "output_dir", None) or _fp.get_output_directory()

    # Point this instance to a user-scoped directory
    user_dir = os.path.join(base, user)
    os.makedirs(user_dir, exist_ok=True)
    self.output_dir = user_dir  # SaveImage uses this when building paths

# Assign directly; DO NOT wrap with MethodType
# _nodes.SaveImage.__init__ = _patched_init

# OPTIONAL: globally scope the output directory for this process
_orig_get_out = _fp.get_output_directory

def _patched_get_output_directory(*args, **kwargs):
    base = _orig_get_out(*args, **kwargs)
    user = _username_from_env()
    if not user:
        return base
    path = os.path.join(base, user)
    os.makedirs(path, exist_ok=True)
    return path

_fp.get_output_directory = _patched_get_output_directory

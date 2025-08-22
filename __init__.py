import os
import types

# ComfyUI core SaveImage node lives in nodes.py
import nodes as _nodes

# Grab original method
_orig = _nodes.SaveImage.save_images

def _username_from_env():
    # Pick what makes sense in your setup:
    # - COMFY_USER: set by your launcher (recommended)
    # - REMOTE_USER / X-Forwarded-User: set by your proxy / SSO
    for key in ("COMFY_USER", "REMOTE_USER", "X_FORWARDED_USER"):
        v = os.environ.get(key)
        if v:
            return v.strip().replace("\\", "_").replace("/", "_")
    return None

def _prefixed_save_images(self, *args, **kwargs):
    user = _username_from_env()
    if user:
        # Normalize subfolder; ensure we nest under "<user>"
        sub = kwargs.get("subfolder")
        if sub:
            sub = str(sub).lstrip("/\\")
            kwargs["subfolder"] = f"{user}/{sub}"
        else:
            kwargs["subfolder"] = user
    return _orig(self, *args, **kwargs)

# Monkey-patch at import time
_nodes.SaveImage.save_images = types.MethodType(_prefixed_save_images, _nodes.SaveImage)

import os
import types
import nodes as _nodes

# Keep the original
_orig_save_images = _nodes.SaveImage.save_images

def _username_from_env():
    for key in ("COMFY_USER", "REMOTE_USER", "X_FORWARDED_USER"):
        v = os.environ.get(key)
        if v:
            return v.strip().replace("\\", "_").replace("/", "_")
    return None

def _scoped_save_images(self, images, filename_prefix, prompt=None, extra_pnginfo=None, **kwargs):
    user = _username_from_env()
    if user:
        sub = kwargs.get("subfolder")
        if sub:
            sub = str(sub).lstrip("/\\")
            kwargs["subfolder"] = f"{user}/{sub}"
        else:
            kwargs["subfolder"] = user
    return _orig_save_images(self, images, filename_prefix, prompt=prompt, extra_pnginfo=extra_pnginfo, **kwargs)

# Patch it
_nodes.SaveImage.save_images = types.MethodType(_scoped_save_images, _nodes.SaveImage)

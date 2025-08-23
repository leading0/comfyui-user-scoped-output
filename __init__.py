# custom_nodes/current_username/__init__.py
import json
from aiohttp import web

# ------------------------
# Custom Node Definition
# ------------------------
class CurrentUsernameNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_username"
    CATEGORY = "utils"

    def get_username(self):
        # Default fallback if middleware didn’t inject
        return ("anonymous",)

NODE_CLASS_MAPPINGS = {
    "CurrentUsername": CurrentUsernameNode
}

# ------------------------
# Middleware Definition
# ------------------------
class ModifiedBodyRequest:
    def __init__(self, original_request, modified_body):
        self._original_request = original_request
        self._modified_body = modified_body
        
    def __getattr__(self, name):
        # Delegate everything else to the original request
        return getattr(self._original_request, name)
        
    async def json(self):
        # Return the modified body instead of the original
        return self._modified_body

@web.middleware
async def inject_user_into_prompt(request, handler):
    # print(f"[CurrentUsername middleware] Incoming request: {request.path} {request.method}")
    if request.path == "/api/prompt" and request.method == "POST":
        try:
            body = await request.json()
            # comfy-user header be like "Stefan_9636034e-8762-4345-aed7-edd747c2feaf"
            raw_username = request.headers.get("comfy-user", "anonymous")
            username = raw_username.rsplit('_', 1)[0]
            print(f"[CurrentUsername middleware] Detected username: {username}")


            for v in body["prompt"].values():
                print(f"testing {v}")
                if "_meta" in v:
                    meta = v["_meta"]
                    if "title" in meta and meta["title"] == "CurrentUser":
                        v["inputs"] = { "value": username }
                        v["widgets_values"] = [ username ]

            # print(f"{json.dumps(body, indent=2)}")
            # Replace the request payload with our modified version
            modified_request = ModifiedBodyRequest(request, body)            
            return await handler(modified_request)

        except Exception as e:
            print(f"[CurrentUsername middleware] Error injecting user: {e}")

    return await handler(request)

# ------------------------
# Monkeypatch web.Application
# ------------------------
_orig_init = web.Application.__init__

def _patched_init(self, *args, **kwargs):
    middlewares = list(kwargs.get("middlewares", []))
    print(f"[CurrentUsername] Auto-registering middleware {middlewares}")
    middlewares.append(inject_user_into_prompt)
    kwargs["middlewares"] = middlewares
    _orig_init(self, *args, **kwargs)
    print(f"[CurrentUsername] Middleware auto-registered {kwargs}")

web.Application.__init__ = _patched_init

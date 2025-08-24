# custom_nodes/current_username/__init__.py
import json
from aiohttp import web
from comfy.comfy_types.node_typing import ComfyNodeABC, InputTypeDict, IO

class CurrentUsernameNode(ComfyNodeABC):
    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        return {
            "required": {"value": (IO.STRING, {})},
        }

    RETURN_TYPES = (IO.STRING,)
    FUNCTION = "execute"
    CATEGORY = "utils/primitive"

    def execute(self, value: str) -> tuple[str]:
        return (value or "anonymous",)

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
                #print(f"testing {v}")
                if "class_type" in v and v["class_type"] == "CurrentUsername":
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
    if "middlewares" in kwargs:
        middlewares = list(kwargs.get("middlewares", []))
        print(f"[CurrentUsername] Auto-registering middleware {middlewares}")
        middlewares.append(inject_user_into_prompt)
        kwargs["middlewares"] = middlewares
        print(f"[CurrentUsername] Middleware auto-registered.")
    else:
        print(f"[CurrentUsername] Middleware not auto-registered. {kwargs.keys()}")

    _orig_init(self, *args, **kwargs)
    
# does not work, disabled
#web.Application.__init__ = _patched_init
""" 
# you need to add this to server.py before "self.app = web.Application(client_max_size=max_upload_size, middlewares=middlewares)" is called 
from custom_nodes.current_username import inject_user_into_prompt
middlewares.append(inject_user_into_prompt) """

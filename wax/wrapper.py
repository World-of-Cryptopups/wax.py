from json import JSONDecodeError
from aioeos.rpc import ERROR_NAME_MAP, EosJsonRpc
from aioeos.exceptions import EosRpcException

from aiohttp import ClientSession


class EosJsonRpcWrapper(EosJsonRpc):
    """Wrapper class for EosJsonRpc to reuse an aiohttp session which is good practice."""

    def __init__(self, url: str, ses: ClientSession = None) -> None:
        self.ses = ses
        super().__init__(url)

    async def post(self, endpoint: str, json=None) -> dict:
        if json is None:
            json = {}
        if self.ses is not None:
            async with self.ses.post(f"{self.URL}/v1{endpoint}", json=json) as res:
                try:
                    resp_dict = await res.json(content_type=None)
                except JSONDecodeError:
                    resp_dict = {"code": 500, "error": {"name": "JSONDecodeError"}}
                # Poor coding practice, but this is what the lib uses. I've added use of status but kept code too as
                # it is what the lib uses.
                if res.status == 500 or resp_dict.get("code") == 500:
                    error = resp_dict.get("error", {})
                    raise ERROR_NAME_MAP.get(error.get("name"), EosRpcException)(error)
                return resp_dict
        # If self has no session, just use super.post which creates a session and cleans up each time. This is done
        # instead of making a self.ses if one isn't provided in order to ensure proper cleanup without requiring use
        # of a context manager to invoke this object.
        return await super().post(endpoint, json=json)

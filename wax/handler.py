from __future__ import annotations

import asyncio
import binascii
import hashlib
import json
from typing import List

from aioeos import EosAccount, EosTransaction, serializer
from aioeos.exceptions import EosAssertMessageException
from aioeos.types.transaction import EosAction
from aiohttp import ClientSession
from wax.exceptions import FailedSend, FailedToGetBlock

from wax.wrapper import EosJsonRpcWrapper


class WaxHandler:
    def __init__(
        self,
        account: EosAccount,
        endpoints: List[str],
        session: ClientSession | None = None,
    ) -> None:
        self.rpcs = [EosJsonRpcWrapper(i, ses=session) for i in endpoints]
        self.account = account

    async def transact(
        self, actions: EosAction | List[EosAction], context_free_bytes=bytes(32)
    ):
        if not isinstance(actions, list):
            actions = [actions]

        block, chain_id = None, None

        for rpc in self.rpcs:
            try:
                # print(f"Attempting to get head block from {rpc.URL}")
                block = await rpc.get_head_block()
                if block is None:
                    continue

                chain_id = await rpc.get_chain_id()

                for action in actions:
                    if isinstance(action.data, dict):
                        abi_bin = await rpc.abi_json_to_bin(
                            action.account, action.name, action.data
                        )
                        action.data = binascii.unhexlify(abi_bin["binargs"])

                break
            except Exception:
                continue

        if block is None:
            raise FailedToGetBlock(
                f"Failed to get head block from any of the ENDPOINTS."
            )

        transaction = EosTransaction(
            ref_block_num=block["block_num"] & 65535,
            ref_block_prefix=block["ref_block_prefix"],
            actions=actions,
        )

        # serialize
        serialized_transaction = serializer.serialize(transaction)

        digest = hashlib.sha256(
            b"".join((chain_id, serialized_transaction, context_free_bytes))  # type: ignore
        ).digest()
        signatures = [self.account.key.sign(digest)]
        serialized_transaction = binascii.hexlify(serialized_transaction).decode()

        # event loop
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        # create task
        tasks = [
            asyncio.create_task(
                self.tx(future, rpc, signatures, serialized_transaction)
            )
            for rpc in self.rpcs
        ]

        # Add a timeout so this doesn't hang indefinitely if no APIs are working
        async def timeout(fut: asyncio.Future, length: int):
            await asyncio.sleep(length)
            fut.set_result(None)

        tasks.append(asyncio.create_task(timeout(future, 10)))

        result = await future
        if not result:
            raise FailedSend("Endpoints seem to be down at the moment.")

        for task in tasks:
            task.cancel()

        return result

    async def tx(
        self,
        fut: asyncio.Future,
        rpc: EosJsonRpcWrapper,
        signatures: list,
        serialized_transaction: str,
    ) -> None:
        """Does a single transaction push to a single EosJsonRpcWrapper object, if it is successful sets the
        callback future."""
        try:
            resp = await rpc.push_transaction(
                signatures=signatures, serialized_transaction=serialized_transaction
            )
        except EosAssertMessageException as e:
            raise ValueError(e)
        content = json.dumps(resp).replace("\\", "")
        if "authorization" in content and "block_num" in content:
            fut.set_result(resp)

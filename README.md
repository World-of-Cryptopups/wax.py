# wax.py

Push WAX transactions from python.

This is a wrapper to aioeos by ulam labs (https://github.com/ulamlabs/aioeos) and is rebased from https://gist.github.com/Vyryn/21bdfe0d3ec66baf62eeadc60fc6db41

## Install

```sh
pip install -U git+https://github.com/TheBoringDude/wax.py.git
```

## Usage

```py
import asyncio
from wax import WaxHandler
from wax.endpoints import TESTNET_ENDPOINTS
from aioeos import EosAccount, EosAction, EosPermissionLevel

import os

# define some important utils in here
wallet = os.environ["WALLET"]
key = os.environ["PRIVATE_KEY"]
authorization = [EosPermissionLevel(wallet, "active")]


async def main():
    # create the account
    account = EosAccount(name=wallet, private_key=key)

    # setup the transaction action
    transfer = EosAction(
        account="eosio.token",
        name="transfer",
        authorization=authorization,
        data={"from": wallet, "to": "eosio", "quantity": "0.01000000 WAX", "memo": ""},
    )

    _wax = WaxHandler(account, TESTNET_ENDPOINTS)

    # call transact
    transact = await _wax.transact(transfer)

if __name__ == "__main__":
    asyncio.run(main())
```

##

**2021 | CTTO**

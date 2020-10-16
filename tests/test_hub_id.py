import os
import pytest
import sys


from forge.forge_async import ForgeAppAsync, Project  # noqa F401

if sys.version_info[:2] < (3, 6):
    pass


@pytest.mark.asyncio
async def test_api_key() -> None:
    async with ForgeAppAsync() as forge:
        forge: ForgeAppAsync
        assert forge.hub_id == os.environ["FORGE_HUB_ID"]

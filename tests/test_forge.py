import pytest
import sys

from forge.forge_async import ForgeAppAsync, Project  # noqa F401

if sys.version_info[:2] < (3, 6):
    pass


@pytest.mark.asyncio
async def test_forge() -> None:
    async with ForgeAppAsync() as forge:
        forge: ForgeAppAsync
        # Get all projects from a hub
        await forge.get_projects()
        assert getattr(forge, "projects", None)
        assert isinstance(forge.projects[0], Project)

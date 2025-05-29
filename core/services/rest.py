from .base import Service
from typing import override


class RESTService(Service):
    def __init__(self): ...

    @override
    async def start(self): ...

    @override
    async def stop(self): ...

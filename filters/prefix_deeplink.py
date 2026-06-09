from aiogram.filters import BaseFilter
from aiogram.filters.command import CommandObject
from aiogram.types import Message

class PrefixDeeplinkFilter(BaseFilter):
    
    def __init__(self, prefix: str):
        self.prefix = prefix

    async def __call__(self, message: Message, command: CommandObject = None) -> bool | dict:
        if not command or not command.args:
            return False
        
        if command.args.startswith(self.prefix):
            clean_payload = command.args[len(self.prefix):]
            return {"payload": clean_payload}
            
        return False

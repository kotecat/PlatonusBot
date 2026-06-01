from pydantic import BaseModel


class BaseSchema(BaseModel):
    ...
    
    def dump(self) -> dict:
        return self.model_dump(by_alias=True)

    @classmethod
    def dump_list(cls, items: list) -> list[dict]:
        return [item.dump() for item in items]
    
    def __str__(self):
        return str(self.model_dump(mode="json"))
    
    def __repr__(self):
        return str(self.model_dump(mode="python"))

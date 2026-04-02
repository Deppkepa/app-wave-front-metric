from abc import ABC
import uuid

class UniqueEntity(ABC):
    __unique_code: str = ''

    def __init__(self) -> None:
        super().__init__()
        self.unique_code = uuid.uuid4().hex

        
    @property
    def unique_code(self) -> str:
        return self.__unique_code
    
    @unique_code.setter
    def unique_code(self, value: str):
        self.__unique_code = value.strip()
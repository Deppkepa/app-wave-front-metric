import unittest
from src.logic.manager import manager

class TestJobFile(unittest.TestCase):
    __test_manager = manager
    # ⁡⁢⁢⁢INFO⁡: тест направлен на открытие файла формата h5
    def test_read(self):
        # TODO: Провести проверки на неправильный путь в функцию
        # TODO: Реализовать отдельный файл с обработчиком ошибок и Log
        
        name_file = "data\sunspot1300.h5"   
        result = self.__test_manager.open_file_h5(name_file)
        
        

if __name__ == "__main__": 
    unittest.main() 
        


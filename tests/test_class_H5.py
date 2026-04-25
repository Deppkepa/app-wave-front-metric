from src.logic.format.h5 import *
import unittest.mock as mock
from pathlib import Path
import numpy as np
import tempfile, unittest, h5py

class TestJobH5(unittest.TestCase):
    """Подготовка для тестов"""
    def setUp(self):
        self.__test_h5 = H5()
        
        # Создаем временную директорию, которая удалится сама
        self.__temp_dir = tempfile.TemporaryDirectory() 
        self.__path_temp_dir = Path(self.__temp_dir.name) 
        
 
        # --- Файл 1: Валидный файл (для "счастливого пути") ---
        self.__test_file_path_valid = self.__path_temp_dir / "valid_data.h5"
        test_data = np.random.rand(10, 50, 50)
        with h5py.File(self.__test_file_path_valid, 'w') as f:
            f.create_dataset('data', data=test_data)

        # --- Файл 2: Пустой файл (без ключей) ---
        self.__empty_file = self.__path_temp_dir / "empty.h5"
        with h5py.File(self.__empty_file, 'w'):
            pass
        
        # --- Файл 3: Путь к файлу, которого не существует ---
        self.__non_existent_path = self.__path_temp_dir / "no_such_file.h5"  
        
        # --- Файл 4: Файл с несколькими ключами ---
        self.__file_with_multiple_keys = self.__path_temp_dir / "multiple_keys.h5"
        data1 = np.array([1, 2, 3])
        data2 = np.array([4, 5, 6])
        with h5py.File(self.__file_with_multiple_keys, 'w') as f:
            f.create_dataset('data1', data=data1)
            f.create_dataset('data2', data=data2)
            
        # --- Файл 5: Создаем файл с 2D данными ---
        self.__file_with_2d_data = self.__path_temp_dir / "wrong_dim_2d.h5"
        with h5py.File(self.__file_with_2d_data, 'w') as f:
            data_2d = np.zeros((100, 200)) 
            f.create_dataset('data', data=data_2d)

        # --- Файл 6: Создаем файл с 4D данными ---
        self.__file_with_4d_data = self.__path_temp_dir / "wrong_dim_4d.h5"
        with h5py.File(self.__file_with_4d_data, 'w') as f:
            data_4d = np.zeros((10, 2, 3, 4))
            f.create_dataset('data', data=data_4d)

    """Сами тесты"""

    # --- Тест 1: Проверка на успешное чтение файла ---
    def test_happy_read_file(self):
        result = self.__test_h5.open_file(self.__test_file_path_valid)
        
        self.assertIsInstance(result, np.ndarray, "Данные должны быть представлены как numpy.ndarray")
        self.assertEqual(len(result.shape), 3, "Форма датасета не соответствует структуре") 
        self.assertIsNotNone(result, "Метод вернул None вместо данных")
        self.assertGreater(result.size, 0, "Массив данных пустой")
        self.assertEqual(self.__test_h5.key, 'data')
        self.assertEqual(self.__test_h5.count_image, 10)
        self.assertEqual(self.__test_h5.shape_image, (50, 50))


    # --- Тест 2: Тест на ошибку доступа к несуществующему файлу ---
    def test_file_not_found(self):
        with self.assertRaises(FileAccessError) as error_context:
            self.__test_h5.open_file(self.__non_existent_path)
        expected_msg = f"The file was not found on the way: {Path(self.__non_existent_path).resolve()}"
        self.assertEqual(str(error_context.exception), expected_msg)
    
    
    # --- Тест 3: Тест проверяет, что блок try/except OSError работает корректно. ---
    def test_h5py_file_error_is_handled(self):
        # Имитирую ошибку открытия файла, которая может быть связана с правами доступа к файлу или занятостью файла другим процессом
        with mock.patch('h5py.File', side_effect=OSError("Fake OS Error: Permission denied or file corrupt")):
            with self.assertRaises(H5ReaderError) as error_context:
                self.__test_h5.open_file(str(self.__test_file_path_valid))
        self.assertIsInstance(error_context.exception, H5ReaderError)
        self.assertIn("Couldn't open the file", str(error_context.exception))
        self.assertIn("Fake OS Error", str(error_context.exception))  


    # --- Тест 4: Тест на ошибку при открытии пустого файла ---
    def test_empty_file(self):
        with self.assertRaises(H5ReaderError) as error_context:
            self.__test_h5.open_file(str(self.__empty_file))
        self.assertIn("The file does not contain any keys (an empty file)", str(error_context.exception))
        
        
    # --- Тест 5: Проверка, что возникает ошибка, если ключей больше одного ---
    def test_error_multiple_keys(self):
        with self.assertRaises(CountKeyError) as error_context:
            self.__test_h5.open_file(str(self.__file_with_multiple_keys)) 
        self.assertIn("More than one key was found in the file", str(error_context.exception))
        
        
    # --- Тест 6: Проверка ошибки, если размерность данных меньше 3 ---
    def test_error_wrong_dimension_too_few(self):
        with self.assertRaises(H5ReaderError) as error_context:
            self.__test_h5.open_file(str(self.__file_with_2d_data))
        self.assertIn("Incorrect dimension of the data.", str(error_context.exception))
        
        
    # --- Тест 7: Проверка ошибки, если размерность данных больше 3 ---
    def test_error_wrong_dimension_too_many(self):
        with self.assertRaises(H5ReaderError) as error_context:
            self.__test_h5.open_file(str(self.__file_with_4d_data))
        self.assertIn("Incorrect dimension of the data.", str(error_context.exception))
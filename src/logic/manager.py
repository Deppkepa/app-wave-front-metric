# ⁡⁢⁢⁢INFO⁡⁡: пока временный класс который будет управлять всеми классами
import h5py
from pathlib import Path

class manager():

    # FIXME: Функцию перенести в класс read_format_h5 а тут сделать функцию которая будет определять формат файла и вызывать функцию
    # ⁡⁢⁢⁢INFO⁡⁡⁡: Открывает файл и выдает массив с данными из файла
    def open_file_h5(name_file: str):
        abs_path = Path(name_file).resolve()
        path_file = abs_path if abs_path.is_file() else abs_path.parent.joinpath('data', name_file)
        with h5py.File(path_file, 'r') as f:
            # FIXME: исправить прямое обращение к ключу
            
            data = f['data']
            
            image_count = data.shape[0]
            frame_size = data.shape[1:]
            # ⁡⁣⁢⁢IDEA⁡: Сделать выводом функции массив с данными из файла

            return f"Количество изображений в файле: {image_count}. \nРазмер субапертур: {frame_size}"
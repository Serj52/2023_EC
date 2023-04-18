import base64
import logging
import zipfile
import os


class ActionFiles:

    @staticmethod
    def encode_base64(file):
        """
        Кодирование файла в base64
        param:file - путь до файла
        """
        with open(file, 'rb') as f:
            doc64 = base64.b64encode(f.read())
            logging.info(f'Закодировал {file} в base64')
            doc_b64 = doc64.decode('utf-8')
            return doc_b64

    @staticmethod
    def file_compression(path, type_object, name_archive):
        """
        Архивирования файлов
        param:dir - директория с файлами для архивирования
        """
        if type_object == 'file':
            dir, path = os.path.split(path)
            with zipfile.ZipFile(os.path.join(dir, name_archive), 'w') as zip:
                zip.write(os.path.join(dir, path), path, compress_type=zipfile.ZIP_DEFLATED)
                os.remove(os.path.join(dir, path))
        else:
            with zipfile.ZipFile(os.path.join(path, name_archive), 'w') as zip:
                for file in os.listdir(path):
                    if '.zip' not in file:
                        zip.write(os.path.join(path, file), file, compress_type=zipfile.ZIP_DEFLATED)
                        os.remove(os.path.join(path, file))
        print(f'Архив {name_archive} в {path} создан')
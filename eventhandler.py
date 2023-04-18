import os
import logging
from datetime import datetime
import pandas
import json


class EventHandler:
    def __init__(self, config, actionfiles, web, rabbit):
        self.config = config
        self.actionfiles = actionfiles
        self.web = web
        self.rabbit = rabbit

    def handler(self, queue: str, task_id: str, event: str, text: str, index: str, response: dict = None,
                folder_path='',
                date_update=None,
                new_message=None) -> None:
        """
        Подготовка данных для ответа в шину данных
        param:queue - очередь для ответа
        param:task_id  - id ответа
        param:event  - send_data: для отправки найденных данных в шину,
        send_error для отправки в шину сообщения об ошибке
        param:text - текст для записи в ответ
        param:period - период за который были найдены данные
        """
        # TODO:Дописать отправку почты на целевом сервере
        message = self.create_message(response=response, type_response=event, task_id=task_id, index=index, text=text,
                                      folder_path=folder_path,
                                      date_update=date_update)
        self.rabbit.send_data_queue(queue, message)
        data = {
            "id": task_id,
            "request": new_message,
            "subject": index,
            'response': message,
            "status": text,
            "date response": str(datetime.now())
        }
        self.write_task_log(data, self.config.task_log)

    def create_message(self, type_response: str, task_id: str, index: str, date_update, response: dict = None,
                       folder_path='',
                       text='') -> json:
        """
        Создание сообщения для ответа в шину данных
        param:type_response - send_data: для отправки найденных данных в шину,
        send_error для отправки в шину сообщения об ошибке
        param:task_id - id запроса
        param:period - период за который были найдены данные
        param:text - текст для записи в ответ
        """
        if response is None:
            with open(os.path.join(self.config.templates, 'response.json'), mode='rb') as file:
                response = json.loads(file.read())
        response['header']['requestID'] = task_id
        response["header"]["timestamp"] = datetime.timestamp(datetime.now())
        response['header']['subject'] = index
        response["body"]["date_update"] = date_update
        if type_response == 'send_data':
            path_response = os.path.join(folder_path, 'response.json')
            # сохраняю файл в директории in_process
            json.dump(response, open(path_response, mode='w', encoding='utf-8'),
                      indent=4, ensure_ascii=False, default=str)
        elif type_response == 'send_error':
            response['ErrorText'] = text
        # возвращаю файл в формате json
        message = json.dumps(response, indent=4, ensure_ascii=False, default=str)
        return message

    def write_task_log(self, data, workbook_path):
        df = pandas.read_excel(workbook_path)
        df = df.append(data, ignore_index=True)
        df.to_excel(workbook_path, index=False)
        logging.info('Запись в task_log добавлена')

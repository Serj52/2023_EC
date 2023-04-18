import logging
import shutil
import json
import os
from jsonschema import validate
import jsonschema.exceptions
from config import Config
import pandas
from datetime import datetime
from eventhandler import EventHandler
from Lib.actionfiles import ActionFiles
from Lib.webworker import WebWorker
from config import Config
from index_worker import Index
from Lib.rabbit import Rabbit
from templates.valid_schema import schema


class Business:
    def __init__(self):
        self.config = Config()
        self.actionfiles = ActionFiles()
        self.web = WebWorker()
        self.rabbit = Rabbit(self.config)
        self.event = EventHandler(self.config, self.actionfiles, self.web, self.rabbit)

    @staticmethod
    def validator(task: json) -> bool:
        try:
            validate(task, schema)
            return True
        except jsonschema.exceptions.ValidationError as error:
            logging.info(f'Не валидный запрос {error}')
            return False

    def migration(self):
        Index(self.config, self.actionfiles, self.web, self.event).process('ICP', 'migration',
                                                                           self.config.queue_response)
        Index(self.config, self.actionfiles, self.web, self.event).process('IPC', 'migration',
                                                                           self.config.queue_response)

    def update(self, index, queue, task):
        if index == 'IPC':
            Index(self.config, self.actionfiles, self.web, self.event).process('IPC', 'update', queue,
                                                                               task)
        if index == 'ICP':
            Index(self.config, self.actionfiles, self.web, self.event).process('ICP', 'update', queue,
                                                                               task)

    def get_task(self):
        new_messages = {}
        type_index = ''
        try:
            new_messages = self.rabbit.check_queue(self.config.queue_request)
        except json.JSONDecodeError as err:
            self.event.handler(queue=self.config.queue_error, task_id=' ', event='send_error',
                               text='Запрос не валиден. Ожидал JSON', index=' ')
            logging.error(f'Проверьте кодировку запроса {err}')

        if new_messages:
            task_id = new_messages['header']['requestID']
            queue = new_messages['header']['replayRoutingKey']
            try:
                if self.validator(new_messages):
                    type_index = new_messages['header']['subject']
                    self.update(type_index, queue, task_id)
                else:
                    self.event.handler(queue=queue, task_id=task_id, event='send_error',
                                       text='Запрос не валиден', index=type_index)
                    logging.info('Запрос не валиден')
            except Exception as err:
                logging.info(err)
                self.event.handler(queue=queue, task_id=task_id, event='send_error',
                                   text='Возникла ошибка', index=type_index, new_message=new_messages)


if __name__ == '__main__':
    print(datetime.now())
    Business().migration()
    print(datetime.now())

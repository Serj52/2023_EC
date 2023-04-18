import requests
import logging
import time
import re
from datetime import datetime
import pandas as pd


class WebWorker:


    def download(self, link: str, params: dict, max_tries=10):
        while max_tries > 0:
            max_tries -= 1
            try:
                if max_tries == 1:
                    self.wait()
                response = requests.get(url=link, params=params)
                if response.status_code == 200:
                    return response.content
                else:
                    time.sleep(60)
            except Exception as err:
                logging.error(err)
        logging.error(f'Не получилось перейти по ссылке {link} {params}')

    @staticmethod
    def creater_param(index, last_period, mode):
        year = datetime.now().year
        if mode == 'update':
            if 'year' in index:
                return {'startPeriod': int(last_period) + 1, 'endPeriod': year}
            elif 'month' in index:
                month = datetime.now().month if len(str(datetime.now().month)) > 1 else '0' + str(datetime.now().month)
                # last_period храниться как год + месяц, разбиваем год и месяц
                last_month = last_period[-2:]
                last_year = last_period[:4]
                if last_month == '12':
                    last_month = '01'
                    last_year = int(last_year) + 1
                else:
                    # для случаев, когда last_month '01', '02'
                    if re.search('0\d', last_month) and last_month != '09':
                        last_month = '0' + str((int(last_month) + 1))
                    else:
                        last_month = int(last_month) + 1
                return {'startPeriod': f'{last_year}-{last_month}', 'endPeriod': f'{year}-{month}'}
            elif 'quarter' in index:
                last_year = last_period[:4]
                last_quarter = last_period[-1:]
                if last_quarter == '4':
                    last_quarter = '1'
                    last_year = int(last_year) + 1
                else:
                    last_quarter = int(last_quarter) + 1
                quarter = pd.Timestamp(datetime.now().month).quarter
                return {'startPeriod': f'{last_year}-Q{last_quarter}', 'endPeriod': f'{year}-Q{quarter}'}
        elif mode == 'migration':
            return {'startPeriod': year - 5, 'endPeriod': year}


    def wait(self, value, type, queue, task, index):
        logging.info(f'Засыпаю до {value} {type}')
        self.eventhandler.handler(queue=queue, task_id=task, event='send_error',
                                  text=f'Сайт не отвечает. Робот осуществит повторную попытку в {value}{type}',
                                  index=index)
        if type in ['hours', 'h', 'H', 'hour']:
            while True:
                hour = datetime.now().hour
                if hour == value:
                    logging.info(f'Проснулся')
                    return
                else:
                    time.sleep(60)
                    continue
        elif type in ['seconds', 'second', 's']:
            time.sleep(value)
            logging.info(f'Проснулся')
            return
        else:
            logging.error('Указан неправильный формат type')
            raise
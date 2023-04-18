import logging
import os
import json
import shutil
from datetime import datetime
from bs4 import BeautifulSoup


class Index:

    def __init__(self, config, actionfiles, webworker, eventhandler):
        self.config = config
        self.actionfiles = actionfiles
        self.web = webworker
        self.event = eventhandler
        self.data = {}
        self.options = {
            'ICP': {
                'periods': {
                    'year_outside_market': self.config.url_icp_outside_a,
                    'month_outside_market': self.config.url_icp_outside_m,
                    'quarter_outside_market': self.config.url_icp_outside_q,
                    'month_inside_market': self.config.url_icp_inside_m
                },
                'processed': self.config.icp_processed,
                'folderLoad': self.config.icp_load
            },
            'IPC': {
                'periods': {
                    'month': self.config.url_ipc_m
                },
                'processed': self.config.ipc_processed,
                'folderLoad': self.config.ipc_load
            }
        }

    @staticmethod
    def extract_data(folder: str, countries, index):
        """
        Извлечение данных из скаченного файла
        """
        response = []
        result = {}
        for file in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, file)):
                with open(os.path.join(folder, file), "r") as outfile:
                    content = outfile.read()
                soup = BeautifulSoup(content, 'html.parser')
                dataset = soup.find_all('g:series')
                country = ''
                last_period = 0
                if dataset:
                    for series in dataset:
                        okved2 = ''
                        for tag in series.contents:
                            if tag.name == 'g:serieskey':
                                for subtag in tag:
                                    if subtag.attrs.get("id") == "nace_r2":
                                        okved2 = subtag.attrs.get("value")
                                    elif subtag.attrs.get("id") == "geo":
                                        country = subtag.attrs.get("value")

                            elif tag.name == "g:obs":
                                data = {
                                    "period": "",
                                    "okved2": "",
                                    "country": "",
                                    "index": ""
                                }
                                if countries[country][index] != '':
                                    # извлекаем последнию записанную дату для данной страны
                                    last_period = countries[country][index]
                                for subtag in tag:
                                    if subtag.name == "g:obsdimension":
                                        period = data["period"] = subtag.attrs.get("value")
                                        if 'month' in index:
                                            period = subtag.attrs.get("value").replace('-', '')
                                        elif 'quarter' in index:
                                            period = subtag.attrs.get("value").replace('-Q', '')
                                        if int(period) > int(last_period):
                                            last_period = period
                                    elif subtag.name == "g:obsvalue":
                                        data["index"] = subtag.attrs.get("value")
                                    data["okved2"] = okved2
                                    data["country"] = country
                                response.append(data)
                    countries[country][index] = last_period
        result["data"] = response
        logging.info(f'Закончил извлечение данных для {index}')
        return response

    def loader(self, countries: dict, url: str, folder, index, mode):
        for country in countries:
            link = f"{url}{country}"
            last_period = countries[country][index]
            param = self.web.creater_param(index, last_period, mode)
            content = self.web.download(link, param)
            soup = BeautifulSoup(content, 'html.parser')
            dataset = soup.find_all('g:series')
            if dataset:
                with open(os.path.join(folder, f'{country}.xml'), "wb") as file:
                    file.write(content)
                    logging.info(f'{link} загружена')

    def process(self, index, mode, queue, task=None):
        options = self.options.get(index)
        with open(os.path.join(self.config.templates, 'response.json'), mode='rb') as file:
            response = json.loads(file.read())
        with open(os.path.join(self.config.templates, 'countries.json'), mode='r', encoding='utf-8') as file:
            countries = json.load(file)
        index_countries = countries.get(index)
        for index_type, link in options.get('periods').items():
            processed_dir = os.path.join(options.get('processed'), index_type)
            logging.info(f'Начинаю обработку {index_type}')
            folderload = os.path.join(options.get('folderLoad'), index_type)
            if index_type == 'month_inside_market':
                index_countries = dict(HU=index_countries['HU'], TR=index_countries['TR'])
            self.loader(index_countries, link, folderload, index_type, mode)
            data = self.extract_data(folderload, index_countries, index_type)
            if data:
                path = os.path.join(folderload, 'file_data.json')
                json.dump(data, open(path, mode='w', encoding='utf-8'), indent=4, ensure_ascii=False)
                self.actionfiles.file_compression(path, 'file', 'file_data.zip')
                self.actionfiles.file_compression(folderload, 'folder', 'files.zip')
                # перебираем файлы в folderload и записываем их в response
                for file in os.listdir(folderload):
                    file_path = os.path.join(folderload, file)
                    if 'file_data' in file:
                        response['body']['file_data'][index_type] = self.actionfiles.encode_base64(file_path)
                    elif 'files' in file:
                        response['body']['files'][index_type] = self.actionfiles.encode_base64(file_path)
                    # если такой файл существуе в папке processed, удаляем его
                    if os.path.exists(os.path.join(processed_dir, file)):
                        os.remove(os.path.join(processed_dir, file))
                    # переносим файлы в папку processed
                    shutil.move(file_path, processed_dir)
                logging.info(f'Закончил обработку {index_type}')
        if response['body']['file_data']:
            self.event.handler(response=response, queue=queue, task_id=task, event='send_data',
                               text=mode, index=index,
                               new_message=response, date_update=str(datetime.now()),
                               folder_path=options.get('processed'))
            # Обновляем файл countries
            json.dump(countries, open(os.path.join(self.config.templates, 'countries.json'),
                                      mode='w', encoding='utf-8'), indent=4, ensure_ascii=False)

        else:
            self.event.handler(queue=queue, task_id=task, event='send_error',
                               text='Нет новых данных', index=index,
                               new_message=response)
            logging.info('Нет новых данных')

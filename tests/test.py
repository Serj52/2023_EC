import time
import json
import logging
from business import EventHandler, Business
from config import Config

import os
from Lib.rabbit import Rabbit
from Lib.actionfiles import ActionFiles

from config import Config as cfg
import pytest
from Lib import exceptions

#
# def test_exception():
#     with pytest.raises(exceptions.WebsiteError):
#         b = IndexBusiness()
#         b.html_content(cfg.bed_url['ICP'])

# def test_handler_data():
#     """
#     Проверка парсинга данных на сайте по заданному периоду
#     """
#     b = IndexBusiness()
#     data = b.html_content(cfg.url['ICP'])
#     result = b.handler_data(data, '2022-08')
#     assert result['data'] != []
#     for index in result['data']:
#         assert index.get("name_period") != None
#         assert index.get("period") != None
#         assert index.get("type_index") != None
#         assert index.get("okved2") != None
#         assert index.get("country") != None
#         assert index.get("index") != None

def test_robot_update():
    """
    Проверка всего цикла обработки валидного запроса
    """
    tasks = ['request_icp.json', 'request_ipc.json']
    for task in tasks:
        with open(os.path.join(cfg.templates, 'countries.json'), mode='rb') as file:
            data = json.loads(file.read())

        if task == 'request_icp.json':
            data['ICP']['BE']['month_outside_market'] = "202301"
            data['ICP']['BE']['quarter_outside_market'] = "20222"

        elif task == 'request_ipc.json':
            data['IPC']['DE']['month'] = "202301"

        json.dump(data, open(os.path.join(cfg.templates, 'countries.json'), mode='w', encoding='utf-8'),
                  indent=4, ensure_ascii=False, default=str)

        Rabbit(Config).producer_queue(cfg.queue_request, task)
        time.sleep(5)
        Business().get_task()
        time.sleep(5)
        response = Rabbit(cfg).check_queue(cfg.queue_response)
        if task == 'request_icp.json':
            assert response['header']['subject'] == 'ICP'
        else:
            assert response['header']['subject'] == 'IPC'
        assert response != None
        assert response['header']['timestamp'] != ''
        assert response['header']['requestID'] != ''
        assert response['body']['file_data'] != ''
        assert response['body']['files'] != ''
        assert response['ErrorText'] == ''

def test_robot_not_update():
    """
    Проверка всего цикла обработки валидного запроса
    """
    tasks = ['request_icp.json', 'request_ipc.json']
    for task in tasks:
        Rabbit(Config).producer_queue(cfg.queue_request, task)
        time.sleep(5)
        Business().get_task()
        time.sleep(5)
        response = Rabbit(cfg).check_queue(cfg.queue_response)
        if task == 'request_icp.json':
            assert response['header']['subject'] == 'ICP'
        else:
            assert response['header']['subject'] == 'IPC'
        assert response != None
        assert response['header']['timestamp'] != ''
        assert response['header']['requestID'] != ''
        assert response['body']['file_data'] == {}
        assert response['body']['files'] == {}
        assert response['ErrorText'] == 'Нет новых данных'

def test_first_start_business():
    """
    Проверка всего цикла обработки валидного запроса
    """
    Business().migration()
    time.sleep(5)
    for index in ['ICP', 'IPC']:
        response = Rabbit(cfg).check_queue(cfg.queue_response)
        assert response != None
        assert response['header']['timestamp'] != ''
        assert response['header']['requestID'] == None
        if index == 'ICP':
            assert response['header']['subject'] == 'ICP'
            assert response['body']['file_data']['year_outside_market'] != {}
            assert response['body']['file_data']['month_outside_market'] != {}
            assert response['body']['file_data']['quarter_outside_market'] != {}
            assert response['body']['file_data']['month_inside_market'] != {}

            assert response['body']['files']['year_outside_market'] != {}
            assert response['body']['files']['month_outside_market'] != {}
            assert response['body']['files']['quarter_outside_market'] != {}
            assert response['body']['files']['month_inside_market'] != {}
        else:
            assert response['header']['subject'] == 'IPC'
            assert response['body']['file_data']['month'] != {}
            assert response['body']['files']['month'] != {}
        assert response['ErrorText'] == ''


def test_bad_encoding_request():
    Rabbit().producer_queue_test(queue_name='hello')
    IndexBusiness().process_task()
    response = Rabbit().check_queue(cfg.queue_error)
    assert response != None
    assert response['header']['timestamp'] != ''
    assert response['body']['date_update'] == ''
    assert response['body']['file_data'] == ''
    assert response['body']['files'] == []
    assert 'Запрос не валиден' in response['ErrorText']


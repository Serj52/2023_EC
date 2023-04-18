from business import Business
import logging
import logging.config
from Lib import log
from config import Config as cfg
import os
import json


class Robot:
    def run(self):
        while True:
            Business().get_task()


if __name__ == '__main__':
    log.set_1(cfg)
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
    })
    logging.info('\n\n=== Start ===\n\n')
    logging.info(f'Режим запуска {cfg.mode}')
    robot = Robot()
    robot.run()

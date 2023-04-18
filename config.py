import os



class Config:
    mode = 'test'
    root_dir = os.path.dirname(os.path.abspath(__file__))
    url_icp_outside_m = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/sts_inppnd_m/M.PREN..NSA.PCH_PRE.'
    url_icp_outside_q = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/sts_inppnd_q/Q.PREN..NSA.PCH_PRE.'
    url_icp_outside_a = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/sts_inppnd_a/A.PREN..NSA.PCH_SM.'
    url_icp_inside_m = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/sts_inppd_m/M.PRIN..NSA.PCH_PRE.'
    url_ipc_m = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/prc_ipc_g20/M.RCH_M.'


    icp_load = os.path.join(root_dir, 'load', 'ICP')
    icp_processed = os.path.join(root_dir, 'processed', 'ICP')
    templates = os.path.join(root_dir, 'templates')
    folder_logs = os.path.join(root_dir, 'Logs')
    log_file = "robot.log"
    task_log = os.path.join(root_dir, 'Logs', 'task_log.xlsx')
    ipc_load = os.path.join(root_dir, 'load', 'IPC')
    ipc_processed = os.path.join(root_dir, 'processed', 'IPC')
    response = os.path.join(templates, 'response.json')
    if mode == 'test':
        rabbit_host = ''
        rabbit_login = ''
        rabbit_pwd = os.environ['']
        queue_request = 'rpa.request.eurostat'
        queue_response = 'rpa.respond.eurostat'
        rabbit_port = 5672
        path = '/'
        queue_error = ''


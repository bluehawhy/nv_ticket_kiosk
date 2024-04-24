import os, sys


#add internal libary
from _src import ticket_kiosk_cmd, ticket_kiosk

refer_api = "local"
#refer_api = "global"

if refer_api == "global":
    sys.path.append((os.path.dirname(os.path.abspath(os.path.dirname(__file__)))))
    from _api import loggas, configus
if refer_api == "local":
    from _src._api import loggas, configus

logging= loggas.logger
logging_file_name = loggas.log_full_name

config_path = os.path.join('static','config','config.json')
message_path =configus.load_config(config_path)['message_path']

config_data = configus.load_config(config_path)
version = 'ticket kiosk v2.0'

revision_list=[
    'Revision list',
    'v1.0 (2023-07-11) : initial release',
    'v1.01 (2023-07-11) : bug fix',
    'v1.02 (2024-04-18) : bug fix',
    'v2.0 (2024-04-18)  : modify code to refer to only json and exce flie',
    '==============================================================================='
    ]

def message_on():
    if os.path.isfile(message_path):
        loggas.remove_message(message_path)
    for revision in revision_list:
        loggas.input_message(path = message_path,message = revision, settime= False)
    return 0


def debug_mode():
    ticket_kiosk.import_ticket(user=config_data['id'],password=config_data['password'],exce_path=config_data['last_file_path'])
    return 0

def prod_mode():
    cmd = ticket_kiosk_cmd.cmd_line(version,revision_list)
    cmd.main()

if __name__ =='__main__':
    prod_mode()

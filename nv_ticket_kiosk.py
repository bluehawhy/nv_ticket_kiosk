import os


from _src._api import logger, logging_message, config, rest
from _src import ticket_kiosk, ticket_kiosk_ui


logging= logger.logger
logging_file_name = logger.log_full_name

config_path = os.path.join('static','config','config.json')
message_path =config.load_config(config_path)['message_path']

config_data = config.load_config(config_path)
version = 'ticket kiosk v1.0'

revision_list=[
    'Revision list',
    'v1.0 (2023-06-29) : initial release',
    '==============================================================================='
    ]

def message_on():
    if os.path.isfile(message_path):
        logging_message.remove_message(message_path)
    for revision in revision_list:
        logging_message.input_message(path = message_path,message = revision, settime= False)
    return 0


if __name__ =='__main__':
    pa = r'D:\_source\source_code\nv_ticket_kiosk\static\excel\template.xlsx'
    session,session_info = rest.initsession('===','==')
    work_sheet = ticket_kiosk.import_ticket(exce_path=pa, session = session)
import os, sys
from PyQt6.QtWidgets import QApplication

#add internal libary
from _src import ticket_kiosk, ticket_kiosk_ui

refer_api = "local"
#refer_api = "global"

if refer_api == "local":
    from _src._api import loggas, configus

logging= loggas.logger

config_path = os.path.join('static','config','config.json')
message_path =configus.load_config(config_path)['message_path']

config_data = configus.load_config(config_path)
version = 'ticket kiosk v4.0'

revision_list=[
    'Revision list',
    'v1.0 (2023-07-11) : initial release',
    'v1.01 (2023-07-11) : bug fix',
    'v1.02 (2024-04-18) : bug fix',
    'v2.0 (2024-04-18)  : modify code to refer to only json and exce flie',
    'v3.0 (2024-04-18)  : modify excel sheet and referance value (must use v3.0 excel)',
    'v4.0 (2026-03-11)  : add UI',
    '==============================================================================='
    ]

def message_on():
    if os.path.isfile(message_path):
        loggas.remove_message(message_path)
    for revision in revision_list:
        loggas.input_message(path = message_path,message = revision, settime= False)
    return



def debug_mode():
    return


def prod_mode():
    app = QApplication(sys.argv)
    window = ticket_kiosk_ui.TicketKioskWindow(version, revision_list)
    window.show()
    sys.exit(app.exec())

if __name__ =='__main__':
    prod_mode()

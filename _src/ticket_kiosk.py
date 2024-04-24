import os, sys
import datetime
import re
import ast

refer_api = "local"
#refer_api = "global"

if refer_api == "global":
    sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
    from _api import loggas, configus, excelium, zyra
if refer_api == "local":
    from _src._api import loggas, configus, excelium, zyra

logging= loggas.logger

config_path = os.path.join('static','config','config.json')
field_mapping_path = os.path.join('static','config','field_mapping.json')

message_path =configus.load_config(config_path)['message_path']

#==========================================================================================
#==========================================================================================
#==========================================================================================

def verify_excel_file(worksheet=None):
    sheet_title = worksheet.title
    list_a_column = [c.value for c in worksheet['A']]
    if sheet_title != 'ticket':
        logging.debug('work sheet name is not ticket')
        return False
    if 'ticket kiosk' not in str(list_a_column):
        logging.debug('col A is not ticket kiosk')
        return False
    if 'Ticket List' not in str(list_a_column):
        logging.debug('col A is not Ticket List')
        return False
    return True

#==========================================================================================
#==========================================================================================
def get_system_info_from_ws(worksheet=None):
    #find ticket list cell
    cnt_ticket_index = [r.value for r in worksheet['A']].index('Ticket List')
    list_project_info_column = worksheet['D1:E%s' %str(cnt_ticket_index+1)]
    list_version_info_column = worksheet['G1:H%s' %str(cnt_ticket_index+1)]
    system_info = {}
    #make info
    for r in list_project_info_column:
        if type(r[1].value) == datetime.datetime:
            system_info[str(r[0].value).strip().replace(' ','_')]=r[1].value.strftime("%y-%m-%d")
        else:
            system_info[str(r[0].value).strip().replace(' ','_')]=r[1].value
    for r in list_version_info_column:
        if type(r[1].value) == datetime.datetime:
            system_info[str(r[0].value).strip().replace(' ','_')]=r[1].value.strftime("%y-%m-%d")
        else:
            system_info[str(r[0].value).strip().replace(' ','_')]=r[1].value
    logging.info('get system info done')
    return system_info

def get_col_attribute(worksheet=None):
    list_a_column = [c.value for c in worksheet['A']]
    cnt_ticket_index = list_a_column.index('Ticket List')
    list_col_attribute = [r.value for r in worksheet[cnt_ticket_index+2]]
    logging.debug('cnt_ticket_index - %s' %str(cnt_ticket_index))
    logging.debug('list_col_attribute - %s' %str(list_col_attribute))
    return cnt_ticket_index, list_col_attribute

def get_market_variant_from_map_ver(map_version):
    field_mapping_data = configus.load_config(field_mapping_path)
    list_market = field_mapping_data["change_field_value"]["map_version_market"]
    dict_variant = field_mapping_data["change_field_value"]["market_variant"]
    market = None
    variant = None
    for m_l in list_market:
        re_result = re.findall(m_l, map_version)
        if len(re_result) == 1:
            market = re_result[0]
            variant = dict_variant[market]
            break
    return market, variant


def make_dict_ticket_info(ticket_system_info, list_col_attribute,ticket_info_from_row):
    dict_ticket_info = {}
    field_mapping_data = configus.load_config(field_mapping_path)
    ticket_info_from_row = [ticket_info.strftime("%H:%M") if type(ticket_info) == datetime.time else ticket_info for ticket_info in ticket_info_from_row]
    for i in range(len(list_col_attribute)):
        dict_ticket_info[list_col_attribute[i].replace(' ','_')] = ticket_info_from_row[i]
    description = f"""\nDetected on Time & Date\n {ticket_system_info['Found_Date']} {dict_ticket_info['time']} \n \n
    TEST ENVIRONMENT \n{ticket_system_info['Test_environment']} \n \n
    Test Version\nHU version: {ticket_system_info['HU_version']} \nNavi version: {ticket_system_info['Navi_version']} \nMap version: {ticket_system_info['Map_version']} \n \n
    PRECONDITIONS \n{dict_ticket_info['precondition']} \n \n
    ERROR PATH/ACTION  \n{dict_ticket_info['action']} \n \n
    MISBEHAVIOR/REACTION \n{dict_ticket_info['misbehavior']} \n \n
    EXPECTED BEHAVIOR \n{dict_ticket_info['expected_result']} \n \n
    Error Recovery \n{dict_ticket_info['Error_Recovery']} \n \n
    Occurrence \n{dict_ticket_info['occurrence']} \n \n
    Log path  \ntime : {dict_ticket_info['time']}  \nHU : {dict_ticket_info['HU']}  \nBP : {dict_ticket_info['BP']}  \nlog path : {ticket_system_info['log_path']}"""
    dict_ticket_info['description'] = description
    market, variant = get_market_variant_from_map_ver(ticket_system_info['Map_version'])
    dict_ticket_info['market'] = market
    dict_ticket_info['variant'] = variant
    dict_ticket_info.update(ticket_system_info)
    #change project
    dict_ticket_info['Project'] = field_mapping_data["change_field_value"]["project"][dict_ticket_info['Project']]
    #change mapversion
    if dict_ticket_info['Project'] in field_mapping_data["change_field_value"]["project_ignore_mapversion"]:
        dict_ticket_info['Map_version'] = '-'
    return dict_ticket_info

#==========================================================================================
#==========================================================================================
#==========================================================================================

def make_dict_from_string(string):
    try:
        converted = ast.literal_eval(string)
        if isinstance(converted, dict):
            return converted
        if isinstance(converted, list):
            return converted
        else:
            return string
    except (SyntaxError, ValueError):
        return string

def make_ticket_import_data(dict_ticket_info):
    #template
    ticket_import_data = {"fields":{}}
    field_mapping_data = configus.load_config(field_mapping_path)
    custumfield_list = field_mapping_data['custumfield_list']
    mapping_field_list = field_mapping_data['mapping_field_list']
    for field in custumfield_list.keys():
        if '-' not in str(custumfield_list[field]):
            ticket_import_data["fields"][field] = custumfield_list[field]
        else:
            replace_value = str(custumfield_list[field]).replace('-',dict_ticket_info[mapping_field_list[field]])
            replace_value = make_dict_from_string(replace_value)
            ticket_import_data["fields"][field] = replace_value
    return ticket_import_data

#==========================================================================================
#==========================================================================================
#==========================================================================================

def create_ticket(rh,json_ticket):
    logging.info(f'start to create ticket - {json_ticket}')
    #json_ticket = {'json_ticket':0}
    response= rh.createTicket(json_ticket)
    logging.info(response)
    return response

#==========================================================================================
#==========================================================================================
#==========================================================================================


def import_ticket(user=None, password=None, exce_path=None):
    config_data = configus.load_config(config_path)
    session, session_info, status_login = zyra.initsession(user,password, jira_url= config_data['jira_url'])
    #check login fail
    if session_info.status_code == 401:
        logging.info('please check user and password')
        return 0
    elif session_info.status_code != 200:
        logging.info('checking login issue')
        logging.info(session_info)
        return 0

    #check excel file
    if str(exce_path).split('.')[-1] != "xlsx":
        logging.info('please check file path - %s' %str(exce_path))
        return 0
    config_data['last_file_path'] = exce_path
    config_data = configus.save_config(config_data,config_path)

    #get data from exce
    wb = excelium.Workbook(exce_path,read_only=False,data_only=False)

    list_ws = wb.get_sheet_list()
    ticket_ws = wb.get_worksheet(list_ws[0])
    result_excel = verify_excel_file(worksheet=ticket_ws)
    if result_excel is False:
        logging.info('excel file is currupt, please use template again')
        logging.info('static/excel/template.xlsx')
        return 0
    
    rh = zyra.Handler_Jira(session,jira_url= config_data['jira_url'])
    
    ticket_system_info = get_system_info_from_ws(ticket_ws)
    cnt_ticket_index, list_col_attribute = get_col_attribute(ticket_ws)
    cnt_upload = list_col_attribute.index('upload')
    cnt_current_row = cnt_ticket_index + 2
    while True:
        cnt_current_row += 1
        ticket_info_from_row = [ticket_info.value for ticket_info in ticket_ws[cnt_current_row]]
        dict_ticket_info = make_dict_ticket_info(ticket_system_info, list_col_attribute,ticket_info_from_row)
        if dict_ticket_info['summary'] is None:
            break
        ticket_import_data = make_ticket_import_data(dict_ticket_info)
        logging.info(f'dict_ticket_info - {dict_ticket_info}')
        logging.info(f'ticket_import_data - {ticket_import_data}')
        if 'n' in dict_ticket_info['upload']:
            ticket_import_data ={'json_ticket':0}
        response = create_ticket(rh,ticket_import_data)
        code_respons = response.status_code
        txt_response = response.json()
        logging.debug(code_respons)
        logging.debug(txt_response)
        if code_respons == 201:
            wb.change_cell_data(ws=ticket_ws, col= 1, row= cnt_current_row, val=txt_response["key"])
            wb.change_cell_data(ws=ticket_ws, col= cnt_upload+1, row= cnt_current_row, val='no')
        elif code_respons == 500:
            pass
        elif code_respons == 400:
            wb.change_cell_data(ws=ticket_ws, col= 1, row= cnt_current_row, val=str(txt_response['errors']))
        else:
            pass
        wb.save_workbook(exce_path)
    wb.close_workbook()
    return ticket_ws

import os
import datetime
import re



from _src._api import logger, logging_message, config, excel, rest


logging= logger.logger
logging_file_name = logger.log_full_name

config_path = os.path.join('static','config','config.json')
message_path =config.load_config(config_path)['message_path']

config_data = config.load_config(config_path)

def verify_excel_file(worksheet=None):
    sheet_title = worksheet.title
    list_a_cols = [c.value for c in worksheet['A']]
    if sheet_title != 'ticket':
        logging.debug('work sheet name is not ticket')
        return False
    if 'ticket kiosk_v1.0' not in list_a_cols:
        logging.debug('col A is not ticket kiosk')
        return False
    if 'Ticket List' not in list_a_cols:
        logging.debug('col A is not Ticket List')
        return False
    return True

def get_information_from_ws(worksheet=None):
    dict_info={
            "project":worksheet['E2'].value,
            "date": worksheet['E3'].value.strftime("%y-%m-%d") if type(worksheet['E3'].value) == datetime.datetime else worksheet['E3'].value,
            "log_path":worksheet['E4'].value,
            "Test_environment":worksheet['E5'].value,
            "HW_Version":worksheet['E6'].value,
            "System":worksheet['E7'].value,
            "HU_version":worksheet['H3'].value,
            "Navi_version":worksheet['H4'].value,
            "Map_version":worksheet['H5'].value,
            "UI_version":worksheet['H6'].value
    }
    logging.info('get info done')
    return dict_info

def find_ticketlist(worksheet=None):
    list_a_cols = [c.value for c in worksheet['A']]
    cnt_Ticket_List = list_a_cols.index('Ticket List')
    list_ticket_attri = [r.value for r in worksheet[cnt_Ticket_List+2]]
    logging.debug('list_ticket_attri - %s' %str(list_ticket_attri))
    return cnt_Ticket_List, list_ticket_attri

def find_market_variant_from_map(map_version):
    list_market = config_data["ticket"]["map_version_market"]
    dict_variant = config_data["ticket"]["market_variant"]
    market = None
    variant = None
    for m_l in list_market:
        re_result = re.findall(m_l, map_version)
        if len(re_result) == 1:
            market = re_result[0]
            variant = dict_variant[market]
            break
    logging.debug('market:%s - variant:%s'%(market, variant))
    return market, variant

def create_ticket(rh,dict_ticket_info,dict_ticket):
    logging.info('start to create ticket')
    logging.debug('dict_ticket_info - %s' %str(dict_ticket_info))
    logging.debug('dict_ticket - %s' %str(dict_ticket))
    if dict_ticket['upload'] not in ['yes','y']:
        response= rh.createTicket({'json_ticket':0})
        return response
    
    #start make description
    description = f"\nDetected on Time & Date\n {dict_ticket_info['date']} {dict_ticket['time']} \n \nTEST ENVIRONMENT \n{dict_ticket_info['Test_environment']} \n \nTest Version\nHU version: {dict_ticket_info['HU_version']} \nNavi version: {dict_ticket_info['Navi_version']} \nMap version: {dict_ticket_info['Map_version']} \n \nPRECONDITIONS \n{dict_ticket['precondition']} \n \nERROR PATH/ACTION  \n{dict_ticket['action']} \n \nMISBEHAVIOR/REACTION \n{dict_ticket['misbehavior']} \n \nEXPECTED BEHAVIOR \n{dict_ticket['expected_result']} \n \nError Recovery \n{dict_ticket['error_recovery']} \n \nOccurrence \n{dict_ticket['occurrence']} \n \nLog path  \ntime : {dict_ticket['time']}  \nHU : {dict_ticket['hu']}  \nBP : {dict_ticket['bp']}  \nlog path : {dict_ticket_info['log_path']}"
    
    #find market and variant
    market, variant = find_market_variant_from_map(dict_ticket_info['Map_version'])
    project = config_data["ticket"]["project"]
    #set a dictionary to upload jira.
    json_ticket = {
        "fields":{
            "summary":dict_ticket['summary'],
            "description":description,
            "priority":{"name":dict_ticket['priority']},
            "project":{"key":project[dict_ticket_info['project']]},
            "customfield_12238":{"value":dict_ticket_info['Test_environment']},
            "customfield_10824":dict_ticket_info['HU_version'],
            "customfield_10826":dict_ticket_info['Navi_version'],
            "customfield_12242":{"value":dict_ticket_info['Map_version']},
            "customfield_12204":{"value":dict_ticket_info['HW_Version']},
            "customfield_11101":{"value":dict_ticket['occurrence']}, #occurrence
            "customfield_13003":{"value":dict_ticket['ticket_category']}, #ticket_category
            "customfield_11102":[{"value":variant,}], #variant 
            "customfield_13005":{"value":dict_ticket['system_component']}, #system_component
            "customfield_14025":{"value":dict_ticket_info['System']}, #System (List)
            "customfield_11223":market, #market
            "issuetype":{"name":"Bug"}, 
            "customfield_10136": dict_ticket_info['date'], #Found Date
            "customfield_11103":"-" #Entry Code
            }
            }
    if dict_ticket_info['project'] in config_data["ticket"]["project_ignore_mapversion"]:
            json_ticket["fields"]["customfield_12242"] = {"value":"-"}
    
    #create ticket.
    logging.info(json_ticket)
    response= rh.createTicket(json_ticket)
    logging.info(response)
    return response


def import_ticket(exce_path=None, session = None):
    rh = rest.Handler_Jira(session)
    wb = excel.Workbook(exce_path,read_only=False,data_only=False)
    #get data from excel
    list_ws = wb.get_sheet_list()
    ticket_ws = wb.get_worksheet(list_ws[0])
    result_excel = verify_excel_file(worksheet=ticket_ws)
    if result_excel is False:
        logging_message.input_message(path = message_path,message = 'excel file is currupt, please use template again', settime= True)
        logging_message.input_message(path = message_path,message = 'static/excel/template.xlsx', settime= True)
        return 0
    dict_ticket_info = get_information_from_ws(ticket_ws)
    cnt_Ticket_List, list_ticket_attri = find_ticketlist(ticket_ws)
    logging.info(list_ticket_attri)
    cnt_summary = list_ticket_attri.index('summary')
    cnt_upload = list_ticket_attri.index('upload')
    cnt_current_row = cnt_Ticket_List + 2
    while True:
        cnt_current_row += 1
        dict_ticket = {}
        list_ticket = [r.value for r in ticket_ws[cnt_current_row]]
        list_ticket = [r.strftime("%H:%M") if type(r) == datetime.time else r for r in list_ticket]
        if list_ticket[cnt_summary] is None:
            break
        for i in range(len(list_ticket_attri)):
            dict_ticket[list_ticket_attri[i].replace(' ','_').lower()] = list_ticket[i]
        response = create_ticket(rh,dict_ticket_info,dict_ticket)
        code_respons = response.status_code
        txt_response = response.json()
        logging.debug(code_respons)
        logging.debug(txt_response)
        if code_respons == 201:
            wb.change_cell_data(ws=ticket_ws, col= 1, row= cnt_current_row, val=txt_response["key"])
        else:
            wb.change_cell_data(ws=ticket_ws, col= 1, row= cnt_current_row, val=str(txt_response['errors']))
        wb.change_cell_data(ws=ticket_ws, col= cnt_upload+1, row= cnt_current_row, val='no')
        wb.save_workbook(exce_path)
    wb.close_workbook()
    return ticket_ws

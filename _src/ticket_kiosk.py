import os
import datetime
import re



from _src._api import loggas, configus, excelium, zyra


logging= loggas.logger

config_path = os.path.join('static','config','config.json')
field_mapping_path = os.path.join('static','config','field_mapping.json')

message_path =configus.load_config(config_path)['message_path']


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
    #find ticket list cell
    cnt_Ticket_List = [r.value for r in worksheet['A']].index('Ticket List')
    logging.info(cnt_Ticket_List)
    list_de_cols = worksheet['D1:E%s' %str(cnt_Ticket_List+1)]
    list_gh_cols = worksheet['G1:H%s' %str(cnt_Ticket_List+1)]
    dict_info = {}
    #make info
    for r in list_de_cols:
        if type(r[1].value) == datetime.datetime:
            dict_info[str(r[0].value).strip().lower().replace(' ','_')]=r[1].value.strftime("%y-%m-%d")
        else:
            dict_info[str(r[0].value).strip().lower().replace(' ','_')]=r[1].value
    for r in list_gh_cols:
        if type(r[1].value) == datetime.datetime:
            dict_info[str(r[0].value).strip().lower().replace(' ','_')]=r[1].value.strftime("%y-%m-%d")
        else:
            dict_info[str(r[0].value).strip().lower().replace(' ','_')]=r[1].value
    logging.info('get info done')
    logging.info(dict_info)
    return dict_info

def find_ticketlist(worksheet=None):
    list_a_cols = [c.value for c in worksheet['A']]
    cnt_Ticket_List = list_a_cols.index('Ticket List')
    list_ticket_attri = [r.value for r in worksheet[cnt_Ticket_List+2]]
    logging.debug('list_ticket_attri - %s' %str(list_ticket_attri))
    return cnt_Ticket_List, list_ticket_attri

def find_market_variant_from_map(map_version):
    logging.info(map_version)
    field_mapping_data = configus.load_config(field_mapping_path)
    list_market = field_mapping_data["ticket"]["map_version_market"]
    dict_variant = field_mapping_data["ticket"]["market_variant"]
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

def make_ticket_info(dict_ticket_info,dict_ticket):
    field_mapping_data = configus.load_config(field_mapping_path)
    #market and variant
    market, variant = find_market_variant_from_map(dict_ticket_info['map_version'])
    description = f"\nDetected on Time & Date\n {dict_ticket_info['date']} {dict_ticket['time']} \n \nTEST ENVIRONMENT \n{dict_ticket_info['test_environment']} \n \nTest Version\nHU version: {dict_ticket_info['hu_version']} \nNavi version: {dict_ticket_info['navi_version']} \nMap version: {dict_ticket_info['map_version']} \n \nPRECONDITIONS \n{dict_ticket['precondition']} \n \nERROR PATH/ACTION  \n{dict_ticket['action']} \n \nMISBEHAVIOR/REACTION \n{dict_ticket['misbehavior']} \n \nEXPECTED BEHAVIOR \n{dict_ticket['expected_result']} \n \nError Recovery \n{dict_ticket['error_recovery']} \n \nOccurrence \n{dict_ticket['occurrence']} \n \nLog path  \ntime : {dict_ticket['time']}  \nHU : {dict_ticket['hu']}  \nBP : {dict_ticket['bp']}  \nlog path : {dict_ticket_info['log_path']}"

    #template
    json_ticket = {
        "fields":{
            "issuetype":{"name":"Bug"}
            }
        }
    #update template
    #description
    json_ticket["fields"]["summary"] = dict_ticket['summary']
    json_ticket["fields"]["description"] = description
    json_ticket["fields"]["priority"] = {"name":dict_ticket['priority']}
    json_ticket["fields"]["project"]={"key":field_mapping_data["ticket"]["project"][dict_ticket_info['project']]}
    json_ticket["fields"]["customfield_12238"]={"value":dict_ticket_info['test_environment']}
    json_ticket["fields"]["customfield_10824"]=dict_ticket_info['navi_version']
    json_ticket["fields"]["customfield_10826"]=dict_ticket_info['hu_version']
    json_ticket["fields"]["customfield_12242"]={"value":dict_ticket_info['map_version']}
    json_ticket["fields"]["customfield_12204"]={"value":dict_ticket_info['hw_version']}
    json_ticket["fields"]["customfield_11101"]={"value":dict_ticket['occurrence']}
    json_ticket["fields"]["customfield_13003"]={"value":dict_ticket['ticket_category']}
    json_ticket["fields"]["customfield_11102"]=[{"value":variant}]
    json_ticket["fields"]["customfield_13005"]={"value":dict_ticket['system_component']}
    json_ticket["fields"]["customfield_14025"]={"value":dict_ticket_info['system_(list)']}
    json_ticket["fields"]["customfield_10136"]=dict_ticket_info['date']

    #set a dictionary to upload jira.
    if dict_ticket_info['project'] in field_mapping_data["ticket"]["project_ignore_mapversion"]:
            json_ticket["fields"]["customfield_12242"] = {"value":"-"}
    return json_ticket
    
def create_ticket(rh,dict_ticket_info,dict_ticket):
    config_data = configus.load_config(config_path)
    
    logging.info('start to create ticket')
    #logging.debug('dict_ticket_info - %s' %str(dict_ticket_info))
    #logging.debug('dict_ticket - %s' %str(dict_ticket))
    if dict_ticket['upload'] not in ['yes','y']:
        response= rh.createTicket({'json_ticket':0})
        return response
    
    #create ticket.
    json_ticket = make_ticket_info(dict_ticket_info,dict_ticket)
    logging.info('ticket_import_information - %s' %str(json_ticket))
    response= rh.createTicket(json_ticket)
    #response= rh.createTicket({'json_ticket':0})
    logging.info(response)
    return response


def import_ticket(user=None, password=None, exce_path=None):
    config_data = configus.load_config(config_path)

    session, session_info, status_login = zyra.initsession(user,password, jira_url= config_data['jira_url'])
    logging.info(session)
    logging.info(session_info)
    logging.info(status_login)

    #check login fail
    if session_info.status_code == 401:
        logging.info('please check user and password')
        return 0
    rh = zyra.Handler_Jira(session,jira_url= config_data['jira_url'])
    #check excel file
    if str(exce_path).split('.')[-1] != "xlsx":
        logging.info('please check file path - %s' %str(exce_path))
        return 0
    config_data['last_file_path'] = exce_path
    config_data = configus.save_config(config_data,config_path)
    wb = excelium.Workbook(exce_path,read_only=False,data_only=False)
    #get data from excel
    list_ws = wb.get_sheet_list()
    ticket_ws = wb.get_worksheet(list_ws[0])
    result_excel = verify_excel_file(worksheet=ticket_ws)
    if result_excel is False:
        logging.info('excel file is currupt, please use template again')
        logging.info('static/excel/template.xlsx')
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
        #logging.info(f'dict_ticket_info - {str(dict_ticket_info)}')
        #logging.info('dict_ticket - %s' %str(dict_ticket))
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

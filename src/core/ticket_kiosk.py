import os, sys
import datetime
import re
import ast

from ..utils import loggas, configus, excelium, zyra

logging= loggas.logger

config_path = os.path.join('resources','config','config.json')
field_mapping_path = os.path.join('resources','config','field_mapping.json')

message_path =configus.load_config(config_path)['message_path']

#==========================================================================================
#==========================================================================================
#==========================================================================================

def verify_excel_file(worksheet=None):
    sheet_title = worksheet.title
    list_a_column = [c.value for c in worksheet['A']]
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

def get_excel_sheet(excel_path=None):
    wb = excelium.Workbook(excel_path, read_only=True, data_only=True)
    try:
        list_ws = wb.get_sheet_list()
        return list_ws
    finally:
        wb.close_workbook() # 정보를 가져온 후 즉시 닫기
        logging.info(f"Closed temp workbook for sheet list: {excel_path}")

def make_dict_ticket_info(ticket_system_info, list_col_attribute,ticket_info_from_row):
    dict_ticket_info = {}
    field_mapping_data = configus.load_config(field_mapping_path)
    ticket_info_from_row = [ticket_info.strftime("%H:%M") if type(ticket_info) == datetime.time else ticket_info for ticket_info in ticket_info_from_row]
    for i in range(len(list_col_attribute)):
        dict_ticket_info[list_col_attribute[i].replace(' ','_')] = ticket_info_from_row[i]
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
        #logging.info(field)
        #logging.info(custumfield_list[field])
        if '-' not in str(custumfield_list[field]):
            ticket_import_data["fields"][field] = custumfield_list[field]
        else:
            replace_value = str(custumfield_list[field]).replace('-',str(dict_ticket_info[mapping_field_list[field]]))
            replace_value = make_dict_from_string(replace_value)
            ticket_import_data["fields"][field] = replace_value
    return ticket_import_data

#==========================================================================================
#==========================================================================================
#==========================================================================================

def create_ticket(rh,json_ticket):
    #logging.info(f'start to create ticket - {json_ticket}')
    #json_ticket = {'json_ticket':0}
    response= rh.createTicket(json_ticket)
    logging.info(response)
    return response

#==========================================================================================
#==========================================================================================
#==========================================================================================

def import_ticket(user=None, password=None, exce_path=None, worksheet = None):
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
    
    # return zephyr
    rh = zyra.Handler_Jira(session,jira_url= config_data['jira_url'])

    #check excel file
    if str(exce_path).split('.')[-1] != "xlsx":
        logging.info('please check file path - %s' %str(exce_path))
        return 0
    config_data['last_file_path'] = exce_path
    config_data = configus.save_config(config_data,config_path)

    #get data from exce
    wb = excelium.Workbook(exce_path,read_only=False,data_only=True) #함수가 아닌 데이터 값만 받아와야함.

    ticket_ws = wb.get_worksheet(worksheet)
    result_excel = verify_excel_file(worksheet=ticket_ws)
    
    if result_excel is False:
        logging.info('excel file is currupt, please use template again')
        logging.info('static/excel/template.xlsx')
        wb.close_workbook()
        return 0
    
    wb.close_workbook() #데이터를 받기 위한 워크북은 닫기

    wb_save = excelium.Workbook(exce_path,read_only=False,data_only=False) #값을 저장하기 위한 워크북 오픈
    save_ws = wb_save.get_worksheet(worksheet)

    ticket_system_info = get_system_info_from_ws(ticket_ws)
    cnt_ticket_index, list_col_attribute = get_col_attribute(ticket_ws)
    cnt_upload = list_col_attribute.index('upload')
    cnt_current_row = cnt_ticket_index + 2
    empty_row_count = 0  # 연속된 빈 행을 카운트
    MAX_EMPTY_ROWS = 2   # 2줄 연속 비어있으면 종료

    while True:
        cnt_current_row += 1
        
        # 1. 엑셀 행 데이터 가져오기
        ticket_info_from_row = [ticket_info.value for ticket_info in ticket_ws[cnt_current_row]]
        dict_ticket_info = make_dict_ticket_info(ticket_system_info, list_col_attribute, ticket_info_from_row)

        # 2. Summary 비어있는지 체크
        if dict_ticket_info.get('summary') is None:
            empty_row_count += 1
            if empty_row_count >= MAX_EMPTY_ROWS:
                logging.info(f"연속 {MAX_EMPTY_ROWS}행이 비어 있어 작업을 종료합니다. (Row: {cnt_current_row})")
                break
            else:
                logging.debug(f"{cnt_current_row}행의 Summary가 없습니다. 다음 행을 확인합니다.")
                continue
        
        # 3. 데이터가 존재하면 카운트 초기화 후 진행
        empty_row_count = 0
        
        # --- 티켓 생성 로직 시작 ---
        try:
            # 업로드 제외 여부 확인 ('n' 체크)
            if 'n' in str(dict_ticket_info.get('upload', '')).lower():
                logging.info(f"Row {cnt_current_row} skipped (upload='n')")
                continue

            ticket_import_data = make_ticket_import_data(dict_ticket_info)
            
            # API 호출
            response = create_ticket(rh, ticket_import_data)
            code_respons = response.status_code
            txt_response = response.json()

            if code_respons == 201:
                logging.info(f"create ticket: {txt_response.get('key')}")
                print(f"create ticket: {txt_response.get('key')}")
                wb_save.change_cell_data(ws=save_ws, col=1, row=cnt_current_row, val=txt_response["key"])
                wb_save.change_cell_data(ws=save_ws, col=cnt_upload+1, row=cnt_current_row, val='no')
            else:
                logging.warning(f"fail ({code_respons}): {txt_response}")
                print(f"fail ({code_respons}): {txt_response}")
                wb_save.change_cell_data(ws=save_ws, col=1, row=cnt_current_row, val=str(txt_response.get('errors', 'Error')))
            
            # 엑셀 저장
            wb_save.save_workbook(exce_path)

        except Exception as e:
            logging.error(f"Row {cnt_current_row} 처리 중 예기치 못한 오류: {e}")
            continue

    wb_save.close_workbook()
    return ticket_ws
import os

from _src import jfrog_arti

def main():
    os.system('cls')
    print('hello this is jfrog command - v0.1')
    print('please enter you want')
    print('01. install jfrog')
    print('02. setup user name and password')
    print('03. setup jfrog (overwrite)')
    print('04. setup download path')
    print('05. download file from artifactory')
    print('06. retry last download')
    print('07. show last artifactory path')
    print('09. upload file from artifactory')
    print('10. add ignore_list')
    print('11. remove ignore_list')
    print('12. show ignore_list')
    print('0. exit')
    
    select_number = input('please enter number:')
    select_number = int(select_number) if select_number.isdigit() else None

    if select_number == 0 :
        exit_main()
        return 0
    elif select_number == 1 :
        cmd_install_jfrog()
        return 0
    elif select_number == 2 :
        cmd_update_username_password()
        return 0
    elif select_number == 3 :
        cmd_set_up_jfrog()
        return 0
    elif select_number == 4 :
        cmd_set_up_download_path()
        return 0
    elif select_number == 5 :
        cmd_download()
        return 0
    elif select_number == 6 :
        cmd_retry_download()
        return 0
    elif select_number == 7 :
        cmd_last_artifactory_path()
        return 0
    elif select_number == 9 :
        cmd_upload()
        return 0
    elif select_number == 10 :
        cmd_add_ignore_list()
        return 0
    elif select_number == 11:
        cmd_remove_ignore_list()
        return 0
    elif select_number == 12:
        cmd_check_ignore_list()
        return 0
    else:
        wrong_select(select_number)
        return 0

#===============================================================
def cmd_install_jfrog():
    os.system('cls')
    print('this is install jfrog')
    print('start install jfrog when you enter.')
    os.system('pause')
    result = jfrog_arti.install_jfrog_lib()
    if result[0] is True:
        print(f'install jfrog success - {result[1]}')
    else:   
        print(f'install jfrog fail - {result[1]}')   
    os.system('pause')
    return main()

def cmd_update_username_password():
    os.system('cls')
    print('update user name and password')
    user_name = input('please enter user name:')
    password = input('please enter password:')
    jfrog_arti.update_jfrog_server_config(user = user_name, password = password)
    print('updated your user name and password')
    os.system('pause')
    return main() 

def cmd_set_up_jfrog():
    os.system('cls')
    print('this is setup jfrog (overwrite)')
    jfrog_arti.setup_jfrog_server_config()
    os.system('pause')
    return main()

def cmd_set_up_download_path():
    os.system('cls')
    local_path = input('please enter local path:')
    local_path = local_path.replace('\\','/')+'/'
    jfrog_arti.update_jfrog_server_config(last_path = local_path)
    os.system('pause')
    return main()

def cmd_download():
    os.system('cls')
    print('this is download from artifactory')
    arti_path = input('please enter artifactory path:')
    config_data = jfrog_arti.update_jfrog_server_config(last_arti = arti_path)
    jfrog_arti.sync_arti_local(arti_path, config_data['last_path'])
    os.system('pause')
    return main()

def cmd_retry_download():
    os.system('cls')
    print('retry to download from artifactory')
    config_data = jfrog_arti.update_jfrog_server_config()
    arti_path = config_data['last_arti']
    local_path = config_data['last_path']
    print('this is your last one')
    print(f'artifactory - {arti_path}')
    print(f'local path - {local_path}')
    jfrog_arti.sync_arti_local(arti_path, local_path)
    os.system('pause')

    return main()

def cmd_last_artifactory_path():
    os.system('cls')
    print('show last artifactory path')
    config_data = jfrog_arti.update_jfrog_server_config()
    arti_path = config_data['last_arti']
    print(f'artifactory - {arti_path}')
    os.system('pause')

    return main()

def cmd_upload():
    os.system('cls')
    print(f'not support yet.')
    os.system('pause')

    return main()

def wrong_select(select_number):
    os.system('cls')
    print(f'you wrote wrong number - {select_number}')
    print(f'please enter correct number')
    os.system('pause')
    return main()


def cmd_check_ignore_list():
    os.system('cls')
    ignore_list = jfrog_arti.load_ignore_config()
    print(ignore_list)
    os.system('pause')
    return main()

def cmd_add_ignore_list():
    os.system('cls')
    word = input('please enter word:')
    jfrog_arti.modify_ignore_list(word=word, add= True)
    os.system('pause')
    return main()
    
def cmd_remove_ignore_list():
    os.system('cls')
    word = input('please enter word:')
    jfrog_arti.modify_ignore_list(word=word, remove= True)
    os.system('pause')
    return main()

def exit_main():
    os.system('cls')
    print('the program is terminated.....')
    os.system('pause')
    return 0

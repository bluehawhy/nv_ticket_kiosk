import os


from _src import ticket_kiosk
from _src._api import configus


config_path = os.path.join('static','config','config.json')
config_data = configus.load_config(config_path)


class cmd_line:
    def __init__(self, version, revision):
        self.version = version
        self.revision = revision
        
    def main(self):
        os.system('color 0A')
        os.system('mode con cols=100 lines=30')
        os.system('cls')
        print('hello %s' %self.version)
        for r in self.revision:
            print(r)
        print('please enter you want')
        print('01. setup user name and password')
        print('02. create ticket')
        print('0. exit')
        
        select_number = input('please enter number:')
        select_number = int(select_number) if select_number.isdigit() else None

        if select_number == 0 :
            self.exit_main()
            return 0
        elif select_number == 1 :
            self.cmd_update_username_password()
            return 0
        elif select_number == 2 :
            self.cmd_create_ticket()
        else:
            self.wrong_select(select_number)
            return 0

    #===============================================================

    def cmd_update_username_password(self):
        os.system('cls')
        print('update user name and password')
        user_name = input('please enter user name:')
        password = input('please enter password:')
        config_data = configus.load_config(config_path)
        config_data["id"] = user_name
        config_data["password"] = password
        config_data = configus.save_config(config_data,config_path)
        print('updated your user name and password')
        os.system('pause')
        return self.main()

    def cmd_create_ticket(self):
        os.system('cls')
        config_data = configus.load_config(config_path)
        print('please enter 0, if you use previous path - %s' %config_data['last_file_path'])
        file_path = input('please enter excel path:')
        if file_path == '0':
            file_path = config_data['last_file_path']
        os.system('pause')
        ticket_kiosk.import_ticket(user=config_data["id"], password=config_data["password"], exce_path=file_path)
        os.system('pause')
        return self.main()

    def wrong_select(self, select_number):
        os.system('cls')
        print(f'you wrote wrong number - {select_number}')
        print(f'please enter correct number')
        os.system('pause')
        return self.main()

    def exit_main(self):
        os.system('cls')
        print('the program is terminated.....')
        os.system('pause')
        return 0

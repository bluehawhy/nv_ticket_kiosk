import sys
import os
import time
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTextEdit, QLabel, QFileDialog, 
                             QApplication, QSizePolicy, QLineEdit, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QTextCursor, QFont, QColor

# 기존 로직 모듈 임포트
from _src import ticket_kiosk
from _src._api import configus

# 설정 경로
config_path = os.path.join('static', 'config', 'config.json')

# --- 1. 로그 가로채기 클래스 ---
class StreamToLogger(QObject):
    log_written = pyqtSignal(str)
    def write(self, text):
        if text.strip():
            self.log_written.emit(text.strip())
    def flush(self): pass

# --- 2. 백그라운드 작업 스레드 ---
class Worker(QThread):
    finished = pyqtSignal(str)
    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        try:
            self.func(*self.args)
            self.finished.emit("Success")
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

# --- 3. 메인 GUI 클래스 ---
class TicketKioskWindow(QMainWindow):
    def __init__(self, version, revision):
        super().__init__()
        
        # 프레임리스 및 반투명 설정 (VisionOS 스타일)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.version = version
        self.revision = revision
        self.drag_pos = None
        self.workers = []
        self.last_path = ""  # 탐색기용 경로 저장 변수

        self.init_ui()
        
        # 시스템 출력 가로채기
        self.stdout_receiver = StreamToLogger()
        self.stdout_receiver.log_written.connect(self.log)
        sys.stdout = self.stdout_receiver

        self.log(f"--- {self.version} UI Started ---")

    def init_ui(self):
        self.resize(500, 620)
        self.setMinimumSize(450, 580)

        # 메인 베이스 위젯
        central_widget = QWidget()
        central_widget.setObjectName("mainWidget")
        self.setCentralWidget(central_widget)

        # QSS 스타일시트 (분리된 라벨 및 폴더 버튼 스타일 추가)
        self.setStyleSheet("""
            #mainWidget {
                background-color: rgba(255, 255, 255, 0.8); 
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
            }
            #titleBar {
                background-color: transparent;
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            }
            .sectionLabel {
                color: #2C3E50;
                font-weight: bold;
                font-size: 12px;
                border-bottom: 2px solid #3498DB;
                margin-bottom: 2px;
            }
            .infoLabel {
                background-color: rgba(255, 255, 255, 0.5);
                border-radius: 8px;
                padding: 10px;
                color: #34495E;
                font-size: 11px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }
            #folderBtn {
                background-color: rgba(52, 152, 219, 0.1);
                border-radius: 8px;
                font-size: 16px;
            }
            #folderBtn:hover {
                background-color: rgba(52, 152, 219, 0.2);
                border: 1px solid #3498DB;
            }
            QPushButton {
                background-color: rgba(232, 234, 237, 0.6);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 10px;
                padding: 8px;
                font-weight: bold;
                color: #2C3E50;
            }
            QPushButton:hover {
                background-color: rgba(52, 152, 219, 0.3);
                border: 1px solid #3498DB;
            }
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 10px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)

        master_layout = QVBoxLayout(central_widget)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(0)

        # 1. 타이틀바
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(title_bar)
        
        self.title_label = QLabel(f"{self.version}")
        self.title_label.setStyleSheet("font-weight: bold; color: #333; margin-left: 15px;")
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("background: transparent; border: none; font-size: 16px;")
        btn_close.clicked.connect(self.close)
        
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(btn_close)
        master_layout.addWidget(title_bar)

        # 2. 컨텐츠 영역
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(12)

        # --- 아이디 표시 ---
        id_label = QLabel("USER ID")
        id_label.setProperty("class", "sectionLabel")
        content_layout.addWidget(id_label)

        self.id_display = QLabel("Loading...")
        self.id_display.setProperty("class", "infoLabel")
        content_layout.addWidget(self.id_display)

        # --- 엑셀 경로 표시 + 폴더 버튼 ---
        path_label = QLabel("EXCEL FILE PATH")
        path_label.setProperty("class", "sectionLabel")
        content_layout.addWidget(path_label)

        path_box = QHBoxLayout()
        self.path_display = QLabel("Not Set")
        self.path_display.setProperty("class", "infoLabel")
        
        self.btn_folder = QPushButton("📂")
        self.btn_folder.setObjectName("folderBtn")
        self.btn_folder.setFixedSize(35, 35)
        self.btn_folder.setToolTip("Open in Explorer")
        self.btn_folder.clicked.connect(self.open_explorer)

        path_box.addWidget(self.path_display, stretch=1)
        path_box.addWidget(self.btn_folder)
        content_layout.addLayout(path_box)

        # 메인 명령 버튼들
        cmd_label = QLabel("MAIN COMMANDS")
        cmd_label.setProperty("class", "sectionLabel")
        content_layout.addWidget(cmd_label)

        btn_layout = QHBoxLayout()
        self.btn_setup = QPushButton("Setup User/PW")
        self.btn_setup.clicked.connect(self.ui_update_user_pw)
        
        self.btn_create = QPushButton("Create Ticket (Excel)")
        self.btn_create.clicked.connect(self.ui_create_ticket)
        
        btn_layout.addWidget(self.btn_setup)
        btn_layout.addWidget(self.btn_create)
        content_layout.addLayout(btn_layout)

        # 로그 터미널
        log_label = QLabel("EXECUTION LOG")
        log_label.setProperty("class", "sectionLabel")
        content_layout.addWidget(log_label)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        content_layout.addWidget(self.log_display)

        master_layout.addWidget(content_area)
        
        # 데이터 로드
        self.refresh_config_info()

    # --- 기능 함수들 ---
    def log(self, text):
        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] {text}")
        self.log_display.moveCursor(QTextCursor.MoveOperation.End)

    def refresh_config_info(self):
        """기존 info_display 대신 id_display와 path_display를 업데이트합니다."""
        try:
            # configus.load_config가 정상 작동한다는 전제 하에 작성
            data = configus.load_config(config_path)
            user_id = data.get('id', 'N/A')
            file_path = data.get('last_file_path', 'Not Set')
            
            self.id_display.setText(user_id)
            self.path_display.setText(file_path)
            self.last_path = file_path # 폴더 열기용 저장
        except Exception as e:
            self.log(f"Config Error: {e}")

    def open_explorer(self):
        """엑셀 파일이 있는 폴더를 탐색기로 엽니다."""
        if not self.last_path or self.last_path == "Not Set":
            self.log("No path information available.")
            return
            
        folder_path = os.path.dirname(self.last_path)
        if os.path.exists(folder_path):
            os.startfile(folder_path) # 윈도우 탐색기 호출
            self.log(f"Opened Folder: {folder_path}")
        else:
            self.log("Path not found.")

    def ui_update_user_pw(self):
        from PyQt6.QtWidgets import QInputDialog
        user, ok1 = QInputDialog.getText(self, "Setup", "Enter User Name:")
        if ok1 and user:
            pw, ok2 = QInputDialog.getText(self, "Setup", "Enter Password:", QLineEdit.EchoMode.Password)
            if ok2 and pw:
                data = configus.load_config(config_path)
                data["id"], data["password"] = user, pw
                configus.save_config(data, config_path)
                self.log("User information updated.")
                self.refresh_config_info()

    def ui_create_ticket(self):
        data = configus.load_config(config_path)
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", data.get('last_file_path', ""), "Excel Files (*.xlsx *.xls)")
        
        if file_path:
            try:
                sheets = ticket_kiosk.get_excel_sheet(excel_path=file_path)
                from PyQt6.QtWidgets import QInputDialog
                sheet_name, ok = QInputDialog.getItem(self, "Select Sheet", "Select Worksheet:", sheets, 0, False)
                
                if ok and sheet_name:
                    # 파일 경로가 업데이트되었으므로 config 저장 및 UI 갱신
                    data["last_file_path"] = file_path
                    configus.save_config(data, config_path)
                    self.refresh_config_info()
                    
                    self.log(f"Starting import: {sheet_name}")
                    self.run_task(ticket_kiosk.import_ticket, data["id"], data["password"], file_path, sheet_name)
            except Exception as e:
                self.log(f"Error: {e}")

    def run_task(self, func, *args):
        worker = Worker(func, *args)
        worker.finished.connect(lambda msg: self.log(f"Task Finished: {msg}"))
        worker.start()
        self.workers.append(worker)

    # 창 이동 이벤트 (기존 코드 유지)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        if self.drag_pos:
            new_pos = event.globalPosition().toPoint()
            self.move(self.pos() + (new_pos - self.drag_pos))
            self.drag_pos = new_pos

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

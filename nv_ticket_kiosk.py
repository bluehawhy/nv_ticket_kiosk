import os, sys, re
from PyQt6.QtWidgets import QApplication
from pathlib import Path
import re


# 1. 유틸리티 (설정, 로거 등)
from src.utils import loggas, configus

# 2. 핵심 로직 및 디바이스 제어 모듈 (core)
from src.ui import (
    ticket_kiosk_ui     
)

logging= loggas.logger

config_path = os.path.join('resources','config','config.json')
message_path =configus.load_config(config_path)['message_path']

config_data = configus.load_config(config_path)

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

last_v = "v0.0"  # 기본값 백업
for item in reversed(revision_list):
    match = re.search(r'^(v\d+\.\d+)', item.strip())
    if match:
        last_v = match.group(1)
        break

# 2. 찾은 버전을 툴 이름 뒤에 붙여줍니다.
version = f'ticket kiosk {last_v}'


def find_location_from_path(path):
    """경로를 받아 확장자를 제거하고 파일명 뒤에 _location.txt를 붙인 후,

    해당 파일 내의 {'lat': ..., 'lon': ...} 좌표 값을 찾아 딕셔너리로 반환합니다.
    """
    path_obj = Path(path)

    # 1. 파일 확장자(.png)를 지우고 _location.txt로 변경
    # path_obj.stem : 확장자를 뺀 파일명 ("Screenshot_20260812_081545")
    target_path = path_obj.with_name(f"{path_obj.stem}_location.txt")

    if not target_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {target_path}")

    # 2. 파일 읽기
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 3. {'lat': 숫자, 'lon': 숫자} 형태의 정규식 패턴 탐색
    pattern = r"\{'lat':\s*([0-9.-]+),\s*'lon':\s*([0-9.-]+)\}"
    match = re.search(pattern, content)

    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return {"lat": lat, "lon": lon}

    raise ValueError(f"위치 정보를 파일에서 찾을 수 없습니다: {target_path}")

def debug_mode():
    # --- 사용 예시 ---
    location = find_location_from_path(r"\\navis1\02.Project\00.NAS\09_Project_Navkingdom\45_DEV\TQA\Log\0_miskang\V239\V239.20_263312\260812\Screenshot_20260812_081545.png")
    print(location)
    return

def prod_mode():
    app = QApplication(sys.argv)
    window = ticket_kiosk_ui.TicketKioskWindow(version, revision_list)
    window.show()
    sys.exit(app.exec())

if __name__ =='__main__':
    debug_mode()

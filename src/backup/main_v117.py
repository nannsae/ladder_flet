# main.py
import os
import flet as ft
import random
import asyncio

# --- Constants for width calculation ---
BASE_WIDTH = 320  # Width for up to 5 participants
EXTRA_WIDTH_PER_PARTICIPANT = 65 # Additional width needed for each participant > 5

# --- Constants for colors ---
COLOR_ICON_ACTIVE = ft.Colors.WHITE
COLOR_ICON_DISABLED = ft.Colors.GREY
COLOR_ICON_BLINK = ft.Colors.RED

class LadderGame(ft.Container):
    # --- LadderGame.__init__ ---
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.num_participants = 0
        # 위젯 컬렉션 리스트 (list_widgettype_role)
        self.list_buttons_start = []
        self.list_textfields_name = []
        self.list_textfields_result = []
        # 데이터/상태 리스트 (list_datatype_role or prefix_name)
        self.list_horizontal_lines = []
        self.list_vertical_lines = []
        self.list_colors = [
            "orange", "cyan", "green", "purple", "brown",
            "pink", "teal", "indigo", "lime", "deeporange",
            "red", "blue", "amber", "lightblue", "deepPurple",
            "yellow", "grey", "bluegrey", "lightgreen", "black" # 10가지 색상 추가
        ]
        self.list_active_animation_indices = [] # 현재 애니메이션 중인 참가자 인덱스 리스트
        # 상태 변수 (is_prefix or count_prefix)
        self.is_win_state = False
        self.count_active_animations = 0
        # UI 위젯 멤버 변수 (widgettype_role)
        self.image_background_default = ft.DecorationImage("ladder_img.jpg", fit=ft.ImageFit.FILL)

        # --- 참가자 선택 UI (widgettype_role) ---
        self.text_participants_label = ft.Text("Participants (2-10):", bgcolor="white", color="black", size=14)
        self.dropdown_participants = ft.Dropdown(
            options=[ft.dropdown.Option(str(i)) for i in range(2, 11)], # 범위 11로 업데이트 (2-10)
            value="3",
            width=90,
            color="cyan",
            text_align=ft.TextAlign.RIGHT, # 드롭다운 메뉴내 텍스트 정렬 방식
            text_style=ft.TextStyle(color="cyan"), # 드롭다운 메뉴내 텍스트 색상
            menu_height = 200, # 드롭다운 메뉴 높이
            bgcolor="cyan", # 드롭다운 메뉴 컬러
        )
        self.button_confirm_participants = ft.ElevatedButton("Confirm", on_click=self.click_participants_game, height=40)

        self.row_initial_controls = ft.Row(
            controls=[self.text_participants_label, self.dropdown_participants, self.button_confirm_participants],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        self.container_initial_view = ft.Container(
            content=self.row_initial_controls,
            width=BASE_WIDTH, # 초기에는 기본 너비 사용
            height=100,
            alignment=ft.alignment.center,
            bgcolor="white",
            border=ft.border.all(1, "black"), # 모든 면에 1픽셀 검정색 테두리
            border_radius=ft.border_radius.all(5), # 모든 면에 5픽셀 둥근 테두리
            shadow=ft.BoxShadow(
                spread_radius=1, # 1픽셀 그림자 퍼짐 반경
                blur_radius=5, # 5픽셀 그림자 흐림 반경
                color="grey", # 회색 그림자
                offset=ft.Offset(2, 2),
            ),
            padding=10,
        )

        self.column_initial_view = ft.Column(
            controls=[self.container_initial_view],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )

        # --- 동적 너비를 가질 프레임들 (widgettype_role) ---
        self.row_participants = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            spacing=10,
            width=BASE_WIDTH # 초기 너비
        )
        self.container_canvas = ft.Container(
            width=BASE_WIDTH, # 초기 너비
            height=480,
            border=ft.border.all(1, "black"),
            content=ft.Stack(), # 내용은 아래 stack_canvas으로 참조
            image=self.image_background_default,
        )
        self.row_results = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            spacing=10,
            width=BASE_WIDTH # 초기 너비
        )
        # --- 동적 너비 프레임 종료 ---

        self.stack_canvas = self.container_canvas.content
        self.textfield_log = ft.TextField(
            multiline=True, read_only=True, expand=True, height=150, border_color="black", visible=False
        )

        self.column_main_game = ft.Column(
            controls=[
                self.row_participants,
                self.container_canvas,
                self.row_results,
            ],
            visible=False,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            # expand=True, # 너비가 명시적으로 설정되므로 expand=True 제거
            width=BASE_WIDTH # 초기 너비
        )

        # --- 수정됨: main_game_column을 스크롤 가능한 Row로 감싸기 (widgettype_role) ---
        self.row_main_game_scroll = ft.Row(
            [self.column_main_game],
            scroll=ft.ScrollMode.ADAPTIVE, # 필요할 때 수평 스크롤 활성화
            expand=True, # Row가 사용 가능한 수직 공간을 차지하도록 허용
            vertical_alignment=ft.CrossAxisAlignment.START # 스크롤 내에서 column_main_game을 상단에 정렬
        )
        # --- 수정 종료 ---

        self.column_root = ft.Column(
            # --- 수정됨: 스크롤 래퍼 사용 ---
            controls=[self.column_initial_view, self.row_main_game_scroll],
            # --- 수정 종료 ---
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        # 루트 content를 Flet Container의 content 속성에 할당
        self.content = self.column_root

    # --- 추가됨: 동적 너비를 위한 헬퍼 메소드 ---
    def _calculate_dynamic_width(self):
        """참가자 수에 따라 필요한 너비를 계산합니다."""
        if self.num_participants <= 5:
            return BASE_WIDTH
        else:
            # 로컬 변수 (snake_case)
            extra_participants = self.num_participants - 5
            return BASE_WIDTH + (extra_participants * EXTRA_WIDTH_PER_PARTICIPANT)
    # --- 추가된 메소드 종료 ---

    # --- 추가됨: 시작 버튼 텍스트 편집 메소드 ---
    def edit_start_button_text(self, index, button_target: ft.ElevatedButton):
        """시작 버튼의 텍스트를 편집하기 위한 AlertDialog를 생성하고 표시합니다."""
        # 로컬 변수 (widgettype_role)
        textfield_edit = ft.TextField(
            value=button_target.text, # 현재 버튼 텍스트로 미리 채움
            label="New Button Text",
            autofocus=True,
            max_length=4,  # 입력 길이 제한 (필요에 따라 조정)
            on_submit=lambda e: save_and_close(e)
        )

        def save_and_close(e):
            # 로컬 변수 (snake_case)
            new_value = textfield_edit.value.strip()
            if new_value: # 비어 있지 않은 경우에만 업데이트
                button_target.text = new_value # 버튼 텍스트 업데이트 (파라미터)
                button_target.update() # UI에서 특정 버튼 업데이트
            self.page.close(alertdialog_edit)

        def close_any_dialog(dlg, e):
            self.page.close(dlg)

        # 로컬 변수 (widgettype_role)
        alertdialog_edit = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Edit Button {index + 1} Text"),
            content=textfield_edit,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_any_dialog(alertdialog_edit, e)),
                ft.TextButton("Save", on_click=save_and_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(alertdialog_edit)
        textfield_edit.focus()
        self.page.update()
    # --- 추가된 메소드 종료 ---

    def edit_callback(self, index, textfield_target: ft.TextField):
        """결과 상자 값을 편집하기 위한 AlertDialog를 생성하고 표시합니다."""
        # 다이얼로그 내 편집을 위한 TextField 생성
        # 로컬 변수 (widgettype_role)
        textfield_edit = ft.TextField(
            value=textfield_target.value, # 현재 값으로 미리 채움
            label="New Result",
            autofocus=True, # 다이얼로그 열릴 때 필드 포커스 (대체로 유용함)
            max_length=6,  # 입력을 6자로 제한
            on_submit=lambda e: save_and_close(e) # Enter 키로 저장 허용
        )

        def save_and_close(e):
            # 로컬 변수 (snake_case)
            new_value = textfield_edit.value.strip()
            if new_value: # 새 값이 비어 있지 않은 경우에만 업데이트
                textfield_target.value = new_value # 컨트롤 업데이트 (파라미터)
                textfield_target.update() # UI에서 특정 TextField 업데이트
                #page.update()
            self.page.close(alertdialog_edit)

        def close_any_dialog(dlg, e):
            self.page.close(dlg)

        # 로컬 변수 (widgettype_role)
        alertdialog_edit = ft.AlertDialog(
            modal=True, # 배경과의 상호작용 방지
            title=ft.Text(f"Edit Result {index + 1}"),
            content=textfield_edit,
            actions=[
                # 취소 버튼은 저장 없이 다이얼로그 닫음
                ft.TextButton("Cancel", on_click=lambda e: close_any_dialog(alertdialog_edit, e)),
                # 저장 버튼은 save_and_close 함수 호출
                ft.TextButton("Save", on_click=save_and_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(alertdialog_edit)
        textfield_edit.focus()
        self.page.update()

    def click_participants_game(self, e):
        self.num_participants = int(self.dropdown_participants.value)
        self.column_initial_view.visible = False
        # self.column_main_game.visible = True # 가시성은 이제 래퍼가 처리
        self.row_main_game_scroll.visible = True

        # --- 수정됨: 참가자가 많을 경우 창 너비 약간 조정 ---
        # 현재 창 높이는 고정
        # self.page.window.width = 400 # 원본 유지 또는 약간 증가? 400 유지.
        # self.page.window.height = 800
        # self.page.window_resizable = True
        # --- 수정 종료 ---

        # --- 수정됨: 동적 너비 계산 및 설정 ---
        # 로컬 변수 (snake_case)
        dynamic_width = self._calculate_dynamic_width()
        self.row_participants.width = dynamic_width
        self.container_canvas.width = dynamic_width
        self.row_results.width = dynamic_width
        self.column_main_game.width = dynamic_width # 스크롤 래퍼 내부 컬럼 너비 설정
        self.column_main_game.visible = True # 실제 콘텐츠 보이게 설정
        # --- 수정 종료 ---

        self.page.update() # 페이지 크기 및 가시성 먼저 업데이트
        self.create_main_widgets() # 이제 크기가 조정된 컨테이너 내에 위젯 생성

        # --- 수정됨: 애니메이션이 실행 중이지 않을 때만 생성 버튼 활성화 ---
        if self.page.appbar and len(self.page.appbar.actions) > 0: # 안전 확인
            self.page.appbar.actions[0].disabled = False # 이제 생성 버튼 활성화
            self.page.appbar.actions[0].icon_color = COLOR_ICON_ACTIVE # 아이콘 색상 활성화
        # --- 수정 종료 ---
        self.page.update()

        if self.page and self.page.loop:
             self.page.loop.create_task(self.blink_generate_icon())

    def generate_default_results(self):
        """'Win' 하나와 나머지는 'Lose'인 기본 결과를 생성합니다."""
        # 로컬 변수 (list_datatype_role, snake_case)
        list_default_results = ["Lose"] * self.num_participants
        index_win = random.randint(0, self.num_participants - 1)
        list_default_results[index_win] = "Win"
        return list_default_results

    def create_main_widgets(self):
        self.row_participants.controls.clear()
        self.row_results.controls.clear()
        # 위젯 컬렉션 리스트 비우기
        self.list_buttons_start.clear()
        self.list_textfields_name.clear()
        self.list_textfields_result.clear()

        # default_names = ["=A=", "=B=", "=C=", "=D=", "=E="] # 현재 사용 안 함

        # 로컬 변수 (list_datatype_role)
        list_default_results = self.generate_default_results()

        # --- 참가자가 많을 경우 위젯 크기 약간 조정? (선택 사항) ---
        # 예를 들어 self.num_participants > 7일 때 버튼/상자를 약간 좁게 만들 수 있음.
        # 단순화를 위해 현재는 고정 크기 유지.
        # 로컬 변수 (snake_case)
        button_width = 50
        result_box_width = 50
        # ---

        for i in range(self.num_participants):
            # 시작 버튼
            # 로컬 변수 (widgettype_role)
            button_start = ft.ElevatedButton(
                f"{i+1}",
                # --- 수정됨: on_click에 디스패처 메소드 사용 ---
                on_click=lambda e, idx=i: self.handle_start_button_click(idx),
                # --- 수정 종료 ---
                height=40,
                width=button_width, # 변수 너비 사용
                # 충분한 색상이 있는지 확인
                color=self.list_colors[i % len(self.list_colors)],
                # --- 수정됨: 생성 전에 편집을 허용하기 위해 활성화 상태로 시작 ---
                disabled=False,
                # --- 수정 종료 ---
            )
            self.list_buttons_start.append(button_start) # 리스트에 추가

            # 이름 입력 (여전히 숨겨짐)
            # 로컬 변수 (widgettype_role)
            textfield_name = ft.TextField(
                value="", width=10, height=0, max_length=3, text_align=ft.TextAlign.CENTER,
                text_size=0, content_padding=0,
            )
            self.list_textfields_name.append(textfield_name) # 리스트에 추가

            # 결과 상자
            # 로컬 변수 (widgettype_role)
            textfield_result = ft.TextField(
                value=list_default_results[i % len(list_default_results)],
                width=result_box_width, # 변수 너비 사용
                height=40,
                text_align=ft.TextAlign.CENTER,
                text_size=14,
                content_padding=0,
                border_color="black",
                read_only=True,
                on_click=lambda e, idx=i: self.handle_result_box_click(idx),
            )
            self.list_textfields_result.append(textfield_result) # 리스트에 추가

            # 참가자 컬럼 (상단)
            # 로컬 변수 (widgettype_role)
            column_participant = ft.Column(
                controls=[button_start, textfield_name],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            )
            self.row_participants.controls.append(column_participant)
            # 결과 상자 (하단)
            self.row_results.controls.append(textfield_result)

        # 크기가 조정된 프레임 내에 새로 추가된 컨트롤을 렌더링하기 위해 업데이트 필요
        self.update()

    # --- 추가됨: 시작 버튼 클릭 디스패처 ---
    def handle_start_button_click(self, index):
        """상단 시작 버튼 클릭을 처리합니다.
        가로선이 존재하면 게임 애니메이션을 시작합니다.
        가로선이 없으면 버튼 텍스트 편집 다이얼로그를 엽니다.
        """
        if not self.list_horizontal_lines: # 리스트가 비어 있는지 확인 (사다리 생성 안 됨)
            # 버튼 텍스트 편집 함수 호출
            if index < len(self.list_buttons_start): # 안전 확인
                self.edit_start_button_text(index, self.list_buttons_start[index])
        else:
            # 가로선 존재, 게임 애니메이션 시작
            self.start_game(index)
    # --- 추가된 메소드 종료 ---

    def handle_result_box_click(self, index):
        """main에서 전달된 편집 콜백 함수를 호출합니다."""
        if index < len(self.list_textfields_result): # 안전 확인
            self.edit_callback(index, self.list_textfields_result[index])

    def generate_horizontal_lines(self):
        self.list_horizontal_lines = []
        # --- 잠재적으로 더 넓어진 캔버스 너비 사용 ---
        # 로컬 변수 (snake_case)
        width = round(self.container_canvas.width / 10) * 10
        height = round(self.container_canvas.height / 10) * 10
        # ---
        self.stack_canvas.controls.clear()
        # self.update() # 나중에 그리기 후 업데이트 호출

        self.draw_vertical_lines(height) # 현재 너비 기준으로 세로선 그리기

        # --- 선 생성 로직은 대부분 동일 ---
        # 이제 잠재적으로 더 넓어진 캔버스 경계 내에서 작동
        # 로컬 변수 (snake_case, dict_datatype_role, is_prefix)
        count_horizontal_lines = random.randint(self.num_participants * 2, self.num_participants * 5)
        dict_y_coords_per_pair = {i: [] for i in range(len(self.list_vertical_lines) - 1)}

        # 쌍 간 최소 선 보장
        for i in range(len(self.list_vertical_lines) - 1):
            if i + 1 >= len(self.list_vertical_lines): continue # 안전 확인
            x1, _, _, _ = self.list_vertical_lines[i]
            x2, _, _, _ = self.list_vertical_lines[i + 1]
            count_horizontal = 0
            count_attempts = 0 # 배치가 어려울 경우 무한 루프 방지
            while count_horizontal < 2 and count_attempts < 50:
                count_attempts += 1
                y = random.randint(30, height - 50)
                y = round(y / 10) * 10
                is_valid_y = True
                # 현재 쌍 내 거리 확인
                if any(abs(y - yc) < self.get_min_y_distance() for yc in dict_y_coords_per_pair[i]):
                    is_valid_y = False
                # 왼쪽 인접 쌍과의 거리 확인
                if is_valid_y and i > 0 and y in dict_y_coords_per_pair.get(i - 1, []):
                    is_valid_y = False
                # 오른쪽 인접 쌍과의 거리 확인
                if is_valid_y and i < len(self.list_vertical_lines) - 2 and y in dict_y_coords_per_pair.get(i + 1, []):
                     is_valid_y = False

                if is_valid_y:
                    dict_y_coords_per_pair[i].append(y)
                    self.list_horizontal_lines.append((x1, y, x2, y))
                    count_horizontal += 1

        # 추가적인 무작위 선 추가
        # 로컬 변수 (snake_case)
        count_additional_lines_needed = count_horizontal_lines - len(self.list_horizontal_lines)
        count_attempts = 0
        while count_additional_lines_needed > 0 and count_attempts < 100:
            count_attempts += 1
            if len(self.list_vertical_lines) < 2: break # 최소 두 개의 세로선 필요

            index_x1 = random.randint(0, len(self.list_vertical_lines) - 2)
            x1, _, _, _ = self.list_vertical_lines[index_x1]
            x2, _, _, _ = self.list_vertical_lines[index_x1 + 1]

            y = random.randint(30, height - 50)
            y = round(y / 10) * 10

            is_valid_y = True
            # 선택된 쌍 내 거리 확인
            if any(abs(y - yc) < self.get_min_y_distance() for yc in dict_y_coords_per_pair[index_x1]):
                is_valid_y = False
            # 왼쪽 인접 쌍과의 거리 확인
            if is_valid_y and index_x1 > 0 and y in dict_y_coords_per_pair.get(index_x1 - 1, []):
                is_valid_y = False
            # 오른쪽 인접 쌍과의 거리 확인
            if is_valid_y and index_x1 < len(self.list_vertical_lines) - 2 and y in dict_y_coords_per_pair.get(index_x1 + 1, []):
                 is_valid_y = False

            if is_valid_y:
                dict_y_coords_per_pair[index_x1].append(y)
                self.list_horizontal_lines.append((x1, y, x2, y))
                count_additional_lines_needed -= 1
        # --- 선 생성 로직 종료 ---

        # 가로선 그리기
        for x1, y, x2, _ in self.list_horizontal_lines:
            # 로컬 변수 (snake_case)
            line_width = int(x2 - x1)
            self.stack_canvas.controls.append(
                ft.Container(
                    left=int(x1), top=y, width=line_width, height=2, bgcolor="grey",
                )
            )
            # self.textfield_log.value += f"H: ({int(x1)},{y})-({int(x2)},{y})\n" # 단축된 로그

        # self.textfield_log.value += f"V lines: {self.list_vertical_lines}\n"
        # self.textfield_log.value += f"H lines count: {len(self.list_horizontal_lines)}\n"
        self.update() # 모든 것을 그린 후 업데이트

    def draw_vertical_lines(self, height):
        self.list_vertical_lines = [] # 그리기 전에 이전 선 지우기
        if self.column_main_game.visible:
            # --- 계산은 이제 현재 container_canvas.width 사용 ---
            # 로컬 변수 (snake_case)
            line_spacing = self.get_line_spacing() # 현재 너비에 따라 다름
            total_width = self.container_canvas.width
            side_margin = line_spacing / 2
            available_width = total_width - (side_margin * 2)
            inner_spacing = available_width / (self.num_participants - 1) if self.num_participants > 1 else 0
            # ---

            for i in range(self.num_participants):
                x = side_margin + (i * inner_spacing) if self.num_participants > 1 else total_width / 2
                x = int(round(x / 10) * 10) # 반올림 유지
                current_height = int(round(height / 10) * 10)

                self.stack_canvas.controls.append(
                    ft.Container(left=x, top=0, width=2, height=current_height, bgcolor="grey")
                )
                # 필요한 정보만 저장 (시작 x, 시작 y, 끝 x, 끝 y)
                self.list_vertical_lines.append((x, 0, x, current_height))
                # self.textfield_log.value += f"V: ({x},0)-({x},{current_height})\n" # 단축된 로그

            self.list_vertical_lines.sort(key=lambda line: line[0]) # x 좌표 기준으로 정렬
            #self.textfield_log.value += f"Sorted V lines: {self.list_vertical_lines}\n"

    def get_line_spacing(self):
        # 캔버스 컨테이너의 현재 너비 사용
        # 로컬 변수 (snake_case)
        width = round(self.container_canvas.width / 10) * 10
        # 최소 참가자 수 + 1개의 간격 필요 (여백 포함)
        return width / (self.num_participants + 1) if self.num_participants > 0 else width

    def get_min_y_distance(self):
        return 20 # 최소 수직 거리 유지

    def start_game(self, participant_index):
        """주어진 참가자에 대한 사다리 애니메이션을 시작합니다."""
        # 이 메소드는 이제 가로선이 존재할 때 handle_start_button_click에 의해서만 호출됨.

        self.container_canvas.image = self.image_background_default
        self.is_win_state = False
        # self.update() # 나중에 업데이트 호출

        # --- 만약을 위해 버튼 상태 다시 확인 ---
        if participant_index >= len(self.list_buttons_start) or self.list_buttons_start[participant_index].disabled:
            print(f"Warning: start_game called for disabled or invalid button index {participant_index}")
            return
        # ---

        if participant_index in self.list_active_animation_indices:
            return

        self.list_active_animation_indices.append(participant_index)
        self.list_buttons_start[participant_index].disabled = True

        self.count_active_animations += 1
        # 애니메이션 중 생성 버튼 비활성화
        if self.page and self.page.appbar and len(self.page.appbar.actions) > 0:
            self.page.appbar.actions[0].disabled = True
            self.page.appbar.actions[0].icon_color = COLOR_ICON_DISABLED # 아이콘 색상 비활성화
        self.update() # 버튼 상태 및 앱바 업데이트
        self.page.loop.create_task(self.animate_line(participant_index))

    async def animate_line(self, participant_index):
        # --- 계산은 현재 캔버스 너비 사용 ---
        # 로컬 변수 (snake_case)
        width = round(self.container_canvas.width / 10) * 10
        height = round(self.container_canvas.height / 10) * 10
        line_spacing = self.get_line_spacing()
        total_width = self.container_canvas.width
        side_margin = line_spacing / 2
        available_width = total_width - (side_margin * 2)
        inner_spacing = available_width / (self.num_participants - 1) if self.num_participants > 1 else 0
        # ---

        # --- 정렬된 list_vertical_lines 리스트에서 시작 X 가져오기 ---
        if participant_index < len(self.list_vertical_lines):
             start_x = self.list_vertical_lines[participant_index][0] # 튜플 (x1, y1, x2, y2)에서 x 가져오기
             x = int(round(start_x / 10) * 10)
             # print(f"Animate Start: P{participant_index}, VLineX: {start_x}, RoundedX: {x}")
        else:
             # 인덱스가 범위를 벗어난 경우 대체 또는 오류 처리
             print(f"Error: participant_index {participant_index} out of range for list_vertical_lines (len {len(self.list_vertical_lines)})")
             x = int(total_width / 2) # 대체로 중앙으로 기본 설정
             # 이 애니메이션이 올바르게 진행될 수 없으므로 애니메이션 카운트 감소
             self.count_active_animations -= 1
             if self.count_active_animations == 0 and self.page.appbar and len(self.page.appbar.actions) > 0:
                 self.page.appbar.actions[0].disabled = False
                 self.page.appbar.actions[0].icon_color = COLOR_ICON_ACTIVE # 아이콘 색상 활성화
             # 버튼 즉시 다시 활성화
             if participant_index < len(self.list_buttons_start):
                 self.list_buttons_start[participant_index].disabled = False
             if participant_index in self.list_active_animation_indices:
                 self.list_active_animation_indices.remove(participant_index)
             self.update()
             return # 시작점이 유효하지 않으면 애니메이션 중지
        # ---

        y = 10
        direction = 0
        color = self.list_colors[participant_index % len(self.list_colors)]

        # 로컬 변수 (widgettype_role, is_prefix)
        container_animated_line = ft.Container(left=x, top=y, width=5, height=0, bgcolor=color)
        self.stack_canvas.controls.append(container_animated_line)
        self.update() # 초기 점 표시

        # --- 애니메이션 루프 로직은 동일하게 유지, 현재 x, y에서 작동 ---
        while y < height - 5:
            is_moved_horizontally = False
            # 현재 위치 (x, y) 및 방향 기준으로 가로선 확인
            for hx1, hy, hx2, _ in self.list_horizontal_lines:
                # 아래로 이동 (방향 0) 중 가로선과 충돌
                if direction == 0 and abs(y - hy) < 5 and hx1 <= x <= hx2:
                    if x < (hx1 + hx2) / 2: # 왼쪽 끝에 더 가까움
                        direction = 1  # 오른쪽으로 이동
                        x = hx1        # 가로선 시작점에 정렬
                    else:              # 오른쪽 끝에 더 가까움
                        direction = 2  # 왼쪽으로 이동
                        x = hx2        # 가로선 끝점에 정렬
                    is_moved_horizontally = True
                    break # 방향 변경되면 내부 루프 종료
                # 오른쪽으로 이동 (방향 1) 중 가로선 끝 도달
                elif direction == 1 and abs(x - hx2) < 5 and abs(y - hy) < 5: # y 정렬도 확인
                    direction = 0  # 아래로 이동
                    x = hx2        # 정렬 보장
                    is_moved_horizontally = True
                    break
                # 왼쪽으로 이동 (방향 2) 중 가로선 시작 도달
                elif direction == 2 and abs(x - hx1) < 5 and abs(y - hy) < 5: # y 정렬도 확인
                    direction = 0  # 아래로 이동
                    x = hx1        # 정렬 보장
                    is_moved_horizontally = True
                    break

            # 방향에 따라 위치 업데이트
            # 로컬 변수 (snake_case)
            step = 10
            if direction == 0: # 아래
                container_animated_line.width = 5
                container_animated_line.height = step
                y += step
                container_animated_line.top = y
                # 방금 수평 이동을 마쳤다면 x가 표류하지 않도록 보장
                if is_moved_horizontally: container_animated_line.left = x
            elif direction == 1: # 오른쪽
                container_animated_line.width = step
                container_animated_line.height = 5
                x += step
                container_animated_line.left = x
                container_animated_line.top = y # 수평 이동 중 y 동일하게 유지
            elif direction == 2: # 왼쪽
                container_animated_line.width = step
                container_animated_line.height = 5
                x -= step
                container_animated_line.left = x
                container_animated_line.top = y # y 동일하게 유지

            self.update()
            await asyncio.sleep(0.02)
        # --- 애니메이션 루프 종료 ---

        # --- 최종 x 기준으로 결과 인덱스 계산 ---
        # 로컬 변수 (snake_case)
        index_result = 0
        if self.num_participants > 1 and inner_spacing > 0:
            # 최종 x 기준으로 가장 가까운 세로선 인덱스 찾기
            distance_closest = float('inf') # 무한대로 초기화
            for i, (_, _, vx, _) in enumerate(self.list_vertical_lines):
                dist = abs(x - vx)
                if dist < distance_closest:
                    distance_closest = dist
                    index_result = i
            # index_result = int(round((x - side_margin) / inner_spacing)) # 이전 계산은 덜 견고할 수 있음
            # 만약을 위해 인덱스 제한
            index_result = max(0, min(index_result, self.num_participants - 1)) # min()은 작은 값을 리턴함 max()는 큰 값을 리턴함함
        elif self.num_participants == 1:
             index_result = 0
        # ---

        if index_result < len(self.list_textfields_result):
            self.list_textfields_result[index_result].bgcolor = color
        else:
            print(f"Error: index_result {index_result} out of range for list_textfields_result (len {len(self.list_textfields_result)})")

        if participant_index in self.list_active_animation_indices:
            self.list_active_animation_indices.remove(participant_index)
        if participant_index < len(self.list_buttons_start):
            self.list_buttons_start[participant_index].disabled = False
        else:
             print(f"Error: participant_index {participant_index} out of range for list_buttons_start (len {len(self.list_buttons_start)})")


        self.count_active_animations -= 1
        # 다른 애니메이션이 실행 중이지 않을 때만 생성 버튼 다시 활성화
        if self.page and self.page.appbar and len(self.page.appbar.actions) > 0:
            if self.count_active_animations == 0:
                self.page.appbar.actions[0].disabled = False
                self.page.appbar.actions[0].icon_color = COLOR_ICON_ACTIVE # 아이콘 색상 활성화

        self.update() # 결과 상자 색상, 버튼 상태, 앱바 업데이트

        # --- 승리 조건 확인 ---
        if index_result < len(self.list_textfields_result) and \
           (self.list_textfields_result[index_result].value == "Win" or self.list_textfields_result[index_result].value == "당첨"):
            self.container_canvas.image = ft.DecorationImage("award.jpg", fit=ft.ImageFit.FIT_HEIGHT)
            self.is_win_state = True
            self.update()
            # 깜빡이기 전에 participant_index 유효한지 확인
            if participant_index < len(self.list_buttons_start):
                await self.blink_result_box(index_result, participant_index)
        else:
            self.is_win_state = False
        # ---

    async def blink_result_box(self, index_result, index_participant):
        # 요소 접근 전에 인덱스 유효한지 확인
        if index_result >= len(self.list_textfields_result) or index_participant >= len(self.list_buttons_start):
            print(f"Error: Invalid indices for blinking - result:{index_result}, participant:{index_participant}")
            return

        # 로컬 변수 (snake_case, is_prefix)
        color_original_result = self.list_textfields_result[index_result].bgcolor
        color_original_button = self.list_buttons_start[index_participant].color
        color_blink_result = "yellow"
        color_blink_button = "black"

        for i in range(10):
            is_blink_on = i % 2 == 0
            # 수정하기 전에 컨트롤이 여전히 존재하는지 확인
            if index_result < len(self.list_textfields_result):
                 self.list_textfields_result[index_result].bgcolor = color_blink_result if is_blink_on else color_original_result
            if index_participant < len(self.list_buttons_start):
                 self.list_buttons_start[index_participant].color = color_blink_button if is_blink_on else color_original_button
            self.update()
            await asyncio.sleep(0.2)

        # 최종 상태 복원, 존재 여부 다시 확인
        if index_result < len(self.list_textfields_result):
            self.list_textfields_result[index_result].bgcolor = color_original_result
        if index_participant < len(self.list_buttons_start):
            self.list_buttons_start[index_participant].color = color_original_button
        self.update()

    def update(self):
        if self.page is not None:
            # 잠재적으로 빠른 업데이트 또는 닫기 중 견고성을 위해 try-except 사용
            try:
                self.page.update()
            except Exception as e:
                print(f"Error during page update: {e}")


    def new_game(self, e):
        self.num_participants = 0
        # 리스트 비우기
        self.list_buttons_start.clear()
        self.list_textfields_name.clear()
        self.list_textfields_result.clear()
        self.list_horizontal_lines.clear() # 중요: 가로선 지우기
        self.list_vertical_lines.clear()
        self.list_active_animation_indices.clear()
        self.count_active_animations = 0
        self.textfield_log.value = ""

        self.column_initial_view.visible = True
        # self.column_main_game.visible = False # 래퍼가 처리
        self.row_main_game_scroll.visible = False

        self.stack_canvas.controls.clear()
        self.row_participants.controls.clear()
        self.row_results.controls.clear()

        # --- 수정됨: 너비를 기본으로 재설정 ---
        self.row_participants.width = BASE_WIDTH
        self.container_canvas.width = BASE_WIDTH
        self.row_results.width = BASE_WIDTH
        self.column_main_game.width = BASE_WIDTH
        # --- 수정 종료 ---

        self.container_canvas.image = self.image_background_default
        self.is_win_state = False

        # 새 게임 시작 시 생성 버튼 비활성화
        if self.page and self.page.appbar and len(self.page.appbar.actions) > 0:
            self.page.appbar.actions[0].disabled = True
            self.page.appbar.actions[0].icon_color = COLOR_ICON_DISABLED # 아이콘 색상 비활성화

        self.update()

    async def blink_generate_icon(self):
        """AppBar의 'Generate' 아이콘을 5초 동안 깜빡입니다."""
        if not (self.page and self.page.appbar and len(self.page.appbar.actions) > 0):
            return

        # 로컬 변수 (widgettype_role)
        iconbutton_generate = self.page.appbar.actions[0]

        # 깜빡임 시작 전에 버튼이 활성화 상태인지 확인 (비활성 상태면 깜빡일 필요 없음)
        if iconbutton_generate.disabled:
            return

        for i in range(10):
            # 애니메이션이 중간에 시작되면 깜빡임 중단
            if self.count_active_animations > 0:
                iconbutton_generate.disabled = True
                iconbutton_generate.icon_color = COLOR_ICON_DISABLED
                self.update()
                return

            is_on = i % 2 == 0
            iconbutton_generate.icon_color = COLOR_ICON_BLINK if is_on else COLOR_ICON_ACTIVE
            self.update() # 일관성을 위해 self.update 사용
            await asyncio.sleep(0.25)

        # 깜빡임 완료 후 최종 상태 설정
        if self.count_active_animations > 0:
            iconbutton_generate.icon_color = COLOR_ICON_DISABLED
            iconbutton_generate.disabled = True
        else:
            iconbutton_generate.icon_color = COLOR_ICON_ACTIVE
            iconbutton_generate.disabled = False
        self.update()


    def generate_ladder(self, e):
        """사다리 뷰를 다시 생성하고 구성 요소를 재설정합니다."""
        if self.column_main_game.visible: # 메인 뷰 활성 상태인지 확인
            self.textfield_log.value = ""
            self.stack_canvas.controls.clear()
            self.list_horizontal_lines = [] # 새 선 생성 전에 지우기
            self.list_vertical_lines = []
            self.list_active_animation_indices = []
            self.count_active_animations = 0

            # --- 수정됨: 동적 너비 다시 계산 및 설정 ---
            # 참가자 수 변경 없이 생성을 클릭한 경우 중요
            # 로컬 변수 (snake_case)
            dynamic_width = self._calculate_dynamic_width()
            self.row_participants.width = dynamic_width
            self.container_canvas.width = dynamic_width
            self.row_results.width = dynamic_width
            self.column_main_game.width = dynamic_width
            # --- 수정 종료 ---

            # 이름 입력 모양 재설정 (사용된 적이 있다면)
            # 로컬 변수 (widgettype_role)
            for textfield_name_entry in self.list_textfields_name:
                textfield_name_entry.color = None # 색상이 상태를 나타낸다고 가정

            # 기본 결과 다시 생성하고 결과 상자 업데이트
            # 로컬 변수 (list_datatype_role, widgettype_role)
            # list_default_results = self.generate_default_results()
            # for i, textfield_result_box in enumerate(self.list_textfields_result):
            #     if i < len(list_default_results):
            #         textfield_result_box.value = list_default_results[i]
            #     textfield_result_box.bgcolor = None
            #     textfield_result_box.border_color = "black"

            # 시각적 사다리 선 다시 생성 (self.list_horizontal_lines 채움)
            self.generate_horizontal_lines() # 이제 업데이트된 너비 사용

            # --- 수정됨: 선 생성 후 시작 버튼 활성화 ---
            # 이제 선이 존재하므로 클릭하면 게임 시작해야 함.
            # 로컬 변수 (widgettype_role)
            for button_start in self.list_buttons_start:
                button_start.disabled = False
            # --- 수정 종료 ---

            # AppBar의 생성 버튼 활성화 보장 (애니메이션 카운트 0이므로)
            if self.page and self.page.appbar and len(self.page.appbar.actions) > 0:
                self.page.appbar.actions[0].disabled = False
                self.page.appbar.actions[0].icon_color = COLOR_ICON_ACTIVE # 아이콘 색상 활성화

            # 배경 이미지 및 승리 상태 재설정
            self.container_canvas.image = self.image_background_default
            self.is_win_state = False

            self.update() # 모든 변경 사항으로 UI 업데이트

    def toggle_log_visibility(self, e):
        print(self.textfield_log.value)

# --- main 함수 (너비/스크롤 관련 변경 필요 없음) ---
def main(page: ft.Page):
    page.title = "사다리 게임"
    # --- 창 크기 고정, 내부 스크롤에 의존 ---
    page.window.width = 400
    page.window.height = 800
    # ---
    page.window.resizable = True
    page.vertical_alignment = ft.MainAxisAlignment.CENTER # Enum 사용
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER # Enum 사용
    page.padding = 20

    def close_any_dialog(dlg, e):
        page.close(dlg)

    # 로컬 변수 (widgettype_role, snake_case)
    alertdialog_info = ft.AlertDialog(
        title=ft.Text(
            "Game Info.", color="black", size=20, weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        content=ft.Column(
            [
                ft.Text("Email: jaekwonyi@naver.com", color="black", size=16),
                ft.Text("Ver: 1.1.7", color="black", size=16), # 아이콘 색상 변경으로 버전 번호 올림
                ft.Text("Desc.: Ladder game (2-10 players).", color="black", size=16),
                ft.Text("Feat.: Edit buttons before generation.", color="black", size=14),
            ], tight=True,
        ),
        bgcolor="white", title_padding=10, content_padding=10,
        shape=ft.RoundedRectangleBorder(radius=10),
        actions=[ft.TextButton("OK", on_click=lambda e: close_any_dialog(alertdialog_info, e))],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    ladder_game = LadderGame(page) # 메인 게임 클래스 인스턴스화

    # AppBar 위젯 직접 생성
    page.appbar = ft.AppBar(
        title=ft.Text("LADDER GAME"), center_title=True, bgcolor="#00796B",
        leading=ft.IconButton(ft.Icons.REFRESH, tooltip="NEW GAME", on_click=ladder_game.new_game),
        actions=[
            ft.IconButton(
                ft.Icons.GRID_GOLDENRATIO, tooltip="Generate a ladder",
                on_click=ladder_game.generate_ladder,
                disabled=True, # 초기 상태 비활성화
                icon_color=COLOR_ICON_DISABLED, # 초기 색상 비활성화
            ),
            ft.IconButton(
                ft.Icons.PERSON, tooltip="Author", on_click=lambda e: page.open(alertdialog_info)
            ),
            # 디버깅용,, 활성화하지 마세요
            #ft.IconButton(ft.Icons.VIEW_LIST, tooltip="로그 보기", on_click=ladder_game.toggle_log_visibility),
        ],
    )

    page.add(ladder_game) # 메인 게임 컨테이너를 페이지에 추가

if __name__ == "__main__":
    # 로컬 변수 (snake_case)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_folder = os.path.join(base_dir, "assets")
    if not os.path.isdir(assets_folder):
        print(f"Warning: Assets directory not found at {assets_folder}")
    ft.app(target=main, assets_dir=assets_folder)

import os
import flet as ft
import random
import asyncio

class LadderGame(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page # self.page = page 를 다시 추가 (중요!)
        self.num_participants = 0
        self.buttons = []
        self.name_entries = []
        self.result_boxes = []
        self.horizontal_lines = []
        self.vertical_lines = []  # Store vertical line coordinates
        self.colors = ["red", "cyan", "green", "purple", "orange"]  # Participant colors
        self.current_animations = []
        self.default_background = ft.DecorationImage("ladder_img.jpg", fit=ft.ImageFit.FILL) # 기본 배경 이미지 저장
        self.is_win_state = False # Win 상태인지 확인하는 변수 추가
        # self.show_log = False # 로그보기 버튼 상태 # Removed

        # Initialize UI components
        self.num_label = ft.Text("Participants (2-5):", bgcolor="white", color="black", size=16)
        self.num_spinbox = ft.Dropdown(
            options=[ft.dropdown.Option(str(i)) for i in range(2, 6)],
            value="3",
            width=80,
            color="cyan",
            bgcolor="cyan",
            text_align=ft.TextAlign.RIGHT,
            text_style=ft.TextStyle(color="cyan"),
        )
        self.num_button = ft.ElevatedButton("Confirm", on_click=self.set_participants, height=40)

        self.initial_view = ft.Row(
            controls=[self.num_label, self.num_spinbox, self.num_button],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        # Set the width of the initial view
        self.initial_view_container = ft.Container(
            content=self.initial_view,
            width=320,
            height=100,
            alignment=ft.alignment.center,
            bgcolor="white",
            border=ft.border.all(1, "black"),
            border_radius=ft.border_radius.all(5),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color="#9E9E9E",
                offset=ft.Offset(2, 2),
            ),
            padding=10,
        )

        # Set the height of the initial view
        self.initial_view_column = ft.Column(
            controls=[self.initial_view_container],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )

        self.participant_frame = ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND, spacing=10)  # Changed to Row

        # canvas_container에 배경이미지를 넣고 싶어요 "assets/ladder_img.jpg"
        self.canvas_container = ft.Container(
            width=320,
            height=480,
            # bgcolor="white",
            border=ft.border.all(1, "black"),
            content=ft.Stack(),
            image=self.default_background, # 기본 배경 이미지로 설정
        )

        self.canvas = self.canvas_container.content
        self.log_text = ft.TextField(
            multiline=True, read_only=True, expand=True, height=150, border_color="black", visible=False
        )
        self.result_frame = ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND, spacing=10)  # Changed to Row

        self.main_view = ft.Column(
            controls=[
                self.participant_frame,
                self.canvas_container,
                self.result_frame,
                # self.log_text, # Removed
            ],
            visible=False,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )

        self.content = ft.Column(
            controls=[self.initial_view_column, self.main_view],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def set_participants(self, e):
        self.num_participants = int(self.num_spinbox.value)
        self.initial_view_column.visible = False
        self.main_view.visible = True
        # 창 크기 변경을 page.update() 전에 수행
        self.page.window.width = 400  # 갤럭시 S24 width
        self.page.window.height = 800  # 갤럭시 S24 height
        self.page.window_resizable = True  # Ensure the window is resizable
        self.page.update()
        self.create_main_widgets()
        # Enable the "사다리 생성" button in the app bar
        self.page.appbar.actions[0].disabled = False
        self.page.update()

    def create_main_widgets(self):
        self.participant_frame.controls.clear()
        self.result_frame.controls.clear()
        self.buttons = []
        self.name_entries = []
        self.result_boxes = []

        default_names = ["=A=", "=B=", "=C=", "=D=", "=E="]
        # default_results = ["당첨", "꽝", "꽝", "꽝", "꽝"]

        # Generate random results with one winner
        default_results = ["Lose"] * self.num_participants
        win_index = random.randint(0, self.num_participants - 1)
        default_results[win_index] = "Win"

        for i in range(self.num_participants):
            # Start button
            start_button = ft.ElevatedButton(
                f"{i+1}",
                on_click=lambda e, i=i: self.start_game(i),
                height=40,
                width=50,
                color=self.colors[i],
                disabled=True,  # Initially disabled
            )
            self.buttons.append(start_button)

            # Name entry
            name_entry = ft.TextField(
                value="",
                width=10,
                height=0,
                max_length=3,
                text_align=ft.TextAlign.CENTER,
                text_size=0,
                content_padding=0,
            )
            self.name_entries.append(name_entry)

            # Result box
            result_box = ft.TextField(
                value=default_results[i % len(default_results)],
                width=50,
                height=40,
                text_align=ft.TextAlign.CENTER,
                text_size=14,
                content_padding=0,
                border_color="black", # 테두리 색상 추가
            )
            self.result_boxes.append(result_box)

            # Create a Column for each participant's widgets
            participant_column = ft.Column(
                controls=[start_button, name_entry],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            )
            self.participant_frame.controls.append(participant_column)
            self.result_frame.controls.append(result_box)

            self.update()

    # Removed select_all_text and select_all_text_on_click functions

    def generate_horizontal_lines(self):
        self.horizontal_lines = []
        width = round(self.canvas_container.width / 10) * 10
        height = round(self.canvas_container.height / 10) * 10
        self.canvas.controls.clear()
        self.update()  # Add update() here

        # Draw vertical lines
        self.draw_vertical_lines(height)

        # Generate horizontal lines
        num_horizontal_lines = random.randint(self.num_participants * 3, self.num_participants * 5)
        y_coords = []

        i, j = 0, 0
        for _ in range(num_horizontal_lines):

            # 수직선의 x 좌표를 기반으로 x1과 x2를 선택
            available_x_coords = [x for x, _, _, _ in self.vertical_lines]

            # 참가자 수 -1 번의 횟수만큼은 random이 아닌 순차적으로 x1_index는 0,1,2 순서로 증가한다.
            # available_x_coords에서 i번째,i+1번째 x를 추출한다.
            #
            if i < (self.num_participants - 1) * 2:
                x1_index = j
                x1 = available_x_coords[x1_index]
                x2 = available_x_coords[x1_index + 1]
                if i != 0 and i % 2 == 1:
                    j = j + 1
                i = i + 1
            else:
                # x1과 x2는 서로 다른 수직선의 x 좌표여야 함
                x1_index = random.randint(0, len(available_x_coords) - 2)
                x1 = available_x_coords[x1_index]
                x2 = available_x_coords[x1_index + 1]

            y = random.randint(30, height - 50)

            # Ensure y is a multiple of 10
            y = round(y / 10) * 10
            y = int(y)

            # Ensure minimum vertical distance
            if any(abs(y - yc) < self.get_min_y_distance() for yc in y_coords):
                continue

            y_coords.append(y)
            self.horizontal_lines.append((int(x1), y, int(x2), y))

        # Draw horizontal lines
        for x1, y, x2, _ in self.horizontal_lines:
            line_width = int(x2 - x1)
            self.canvas.controls.append(
                ft.Container(
                    left=int(x1),
                    top=y,
                    width=line_width,
                    height=2,
                    bgcolor="grey",
                )
            )
            self.log_text.value += f"Horizontal line: start=({int(x1)}, {y}), end=({int(x2)}, {y})\n"

        # Log horizontal lines
        self.log_text.value += f"Vertical lines: {self.vertical_lines}\n"
        self.log_text.value += f"Horizontal lines: {self.horizontal_lines}\n"
        self.update()

    def draw_vertical_lines(self, height):
        if self.main_view.visible:
            line_spacing = self.get_line_spacing()
            # Calculate the total width available for the lines
            total_width = self.canvas_container.width
            # Calculate the width of the side margins
            side_margin = line_spacing / 2  # Modified line
            # Calculate the width available for the lines between the side margins
            available_width = total_width - (side_margin * 2)
            # Calculate the spacing between the lines
            if self.num_participants > 1:
                inner_spacing = available_width / (self.num_participants - 1)  # Modified line
            else:
                inner_spacing = 0

            for i in range(self.num_participants):
                # Calculate the x-coordinate of the line
                if self.num_participants > 1:
                    x = side_margin + (i * inner_spacing)
                else:
                    x = total_width / 2
                x = round(x / 10) * 10  # Ensure x is a multiple of 10
                x = int(x)
                current_height = int(round(height / 10) * 10)
                self.canvas.controls.append(
                    ft.Container(
                        left=x,
                        top=0,
                        width=2,  # Modified line
                        # =round(height / 10) * 10,  # Ensure height is a multiple of 10
                        height=current_height,
                        bgcolor="grey",
                    )
                )
                self.vertical_lines.append((x, 0, x, current_height))
                self.log_text.value += f"Vertical line: start=({x}, 0), end=({x}, {current_height})\n"

    def get_line_spacing(self):
        width = round(self.canvas_container.width / 10) * 10
        return width / (self.num_participants + 1)

    def get_min_y_distance(self):
        return 20

    def start_game(self, participant_index):
        # "Win" 상태이고, 다른 참가자의 버튼을 누른 경우 배경 이미지 변경
        if self.is_win_state and not self.buttons[participant_index].disabled:
            self.canvas_container.image = self.default_background
            self.is_win_state = False
            self.update()

        if self.buttons[participant_index].disabled:
            return

        if participant_index in self.current_animations:
            return
        self.current_animations.append(participant_index)

        self.buttons[participant_index].disabled = True
        self.update()

        # Disable the "사다리 생성" button
        self.page.appbar.actions[0].disabled = True
        self.update()
        self.page.loop.create_task(self.animate_line(participant_index))  # Modified line
        # Enable the "사다리 생성" button

    async def animate_line(self, participant_index):  # Modified to async def
        width = round(self.canvas_container.width / 10) * 10
        height = round(self.canvas_container.height / 10) * 10

        line_spacing = self.get_line_spacing()

        # Calculate the total width available for the lines
        total_width = self.canvas_container.width
        # Calculate the width of the side margins
        side_margin = line_spacing / 2  # Modified line
        # Calculate the width available for the lines between the side margins
        available_width = total_width - (side_margin * 2)
        # Calculate the spacing between the lines
        if self.num_participants > 1:
            inner_spacing = available_width / (self.num_participants - 1)  # Modified line
        else:
            inner_spacing = 0

        # participant_index에 해당하는 vertical_lines의 x좌표값으로 x를 할당하도록 작성해 주세요
        if self.num_participants > 1:
            x = int((self.vertical_lines[participant_index][0] * 10) / 10)  # Modified line
            # x = int(side_margin + (participant_index * inner_spacing))
            # x 값을 출력해주세요
            print(f"participant_index: {participant_index}, x좌표값: {x}")
        else:
            x = int(total_width / 2)

        y = 10
        direction = 0  # 0: down, 1: right, 2: left
        color = self.colors[participant_index]

        line_container = ft.Container(
            left=x,
            top=y,
            width=5,  # Modified line
            height=0,
            bgcolor=color,
        )
        self.canvas.controls.append(line_container)

        while y < height - 5:
            # Check for intersections with horizontal lines
            for x1, y1, x2, y2 in self.horizontal_lines:
                if direction == 0 and abs(y - y1) < 5 and x1 <= x <= x2:
                    # Change direction to right or left
                    if x < (x1 + x2) / 2:
                        direction = 1  # Go right
                        x = x1
                    else:
                        direction = 2  # Go left
                        x = x2
                    break
                elif direction == 1 and abs(x - x2) < 5 and y1 <= y <= y2:
                    direction = 0  # Go down
                    x = x2
                    break
                elif direction == 2 and abs(x - x1) < 5 and y1 <= y <= y2:
                    direction = 0  # Go down
                    x = x1
                    break

            # Update position
            if direction == 0:
                line_container.width = 5  # Modified line
                line_container.height = 10
                y += 10
                # line_container.left = x
                line_container.top = y
            elif direction == 1:
                line_container.width = 10
                line_container.height = 5  # Modified line
                x += 10
                line_container.left = x
                line_container.top = y
            elif direction == 2:
                line_container.width = 10
                line_container.height = 5  # Modified line
                x -= 10
                line_container.left = x
                line_container.top = y

            self.update()
            await asyncio.sleep(0.02)  # Wait for 5ms, changed from 0.01 to 0.1

        # Game finished
        # Calculate the final result index
        if self.num_participants > 1:
            result_index = int(round((x - side_margin) / inner_spacing))
        else:
            result_index = 0

        # self.result_boxes[result_index].value = "완료"
        self.result_boxes[result_index].bgcolor = color
        # self.name_entries[participant_index].color = color
        if participant_index in self.current_animations:
            self.current_animations.remove(participant_index)
        self.buttons[participant_index].disabled = False
        self.update()
        self.page.appbar.actions[0].disabled = False
        self.update()

        # Check if the result is "Win" and change the background
        # "Win" 이거나 "당첨" 일 경우
        if self.result_boxes[result_index].value == "Win" or self.result_boxes[result_index].value == "당첨":
            self.canvas_container.image = ft.DecorationImage("award.jpg", fit=ft.ImageFit.FIT_HEIGHT)
            self.is_win_state = True # Win 상태로 변경
            self.update()
            await self.blink_result_box(result_index, participant_index) # result_box 깜빡임 함수 호출
        else:
            self.is_win_state = False # Win 상태가 아님

    async def blink_result_box(self, result_index, participant_index):
        # result_box의 배경색을 5초 동안 깜빡이게 합니다.
        # start_button도 5초 동안 깜빡이게 합니다.
        original_color = self.result_boxes[result_index].bgcolor
        original_button_color = self.buttons[participant_index].color
        for _ in range(10):  # 5초 동안 10번 깜빡임 (0.5초 간격)
            self.result_boxes[result_index].bgcolor = "yellow" if self.result_boxes[result_index].bgcolor == original_color else original_color
            self.buttons[participant_index].color = "black" if self.buttons[participant_index].color == original_button_color else original_button_color
            self.update()
            await asyncio.sleep(0.2)
        self.result_boxes[result_index].bgcolor = original_color  # 깜빡임 종료 후 배경색 복원
        self.buttons[participant_index].color = original_button_color
        self.update()
        
        # original_color = self.result_boxes[result_index].bgcolor
        # for _ in range(10):  # 5초 동안 10번 깜빡임 (0.5초 간격)
        #     self.result_boxes[result_index].bgcolor = "yellow" if self.result_boxes[result_index].bgcolor == original_color else original_color
        #     self.update()
        #     await asyncio.sleep(0.2)
        # self.result_boxes[result_index].bgcolor = original_color  # 깜빡임 종료 후 배경색 복원
        # self.update()

    def update(self):
        if self.page is not None:
            self.page.update()

    def new_game(self, e):
        # Reset the game state
        self.num_participants = 0
        self.buttons = []
        self.name_entries = []
        self.result_boxes = []
        self.horizontal_lines = []
        self.vertical_lines = []
        self.current_animations = []
        self.log_text.value = ""  # Add log_text clear
        self.initial_view_column.visible = True
        self.main_view.visible = False
        self.canvas.controls.clear()
        self.update()  # Add update() here
        self.participant_frame.controls.clear()
        self.result_frame.controls.clear()
        # Disable the "사다리 생성" button in the app bar
        self.page.appbar.actions[0].disabled = True
        self.page.update()
        # Reset the background image to the default
        self.canvas_container.image = self.default_background # 기본 배경 이미지로 설정
        self.is_win_state = False # Win 상태 초기화
        self.update()

    def generate_ladder(self, e):
        if self.main_view.visible:
            self.log_text.value = ""  # Clear log
            self.canvas.controls.clear()  # Clear canvas controls
            self.horizontal_lines = []  # Clear horizontal lines
            self.vertical_lines = []  # Clear vertical lines
            self.current_animations = []  # Clear current animations
            # self.name_entries 선택 상태를 초기화해주세요
            for name_entry in self.name_entries:
                name_entry.color = None

            # Clear and re-initialize result boxes
            for result_box in self.result_boxes:
                # result_box.value = ""
                result_box.bgcolor = None  # Reset background color
                result_box.border_color = "black" # 테두리 색상 초기화
            self.update()

            self.generate_horizontal_lines()
            self.update()
            # Re-enable start buttons
            for button in self.buttons:
                button.disabled = False
            self.update()
            # Enable the "사다리 생성" button
            self.page.appbar.actions[0].disabled = False
            self.update()
            # Reset the background image to the default
            self.canvas_container.image = self.default_background # 기본 배경 이미지로 설정
            self.is_win_state = False # Win 상태 초기화
            self.update()

    def toggle_log_visibility(self, e):
        # self.show_log = not self.show_log # Removed
        # self.log_text.visible = self.show_log # Add log_text visible # Removed
        print(self.log_text.value)  # Modified
        # self.update() # Removed


def main(page: ft.Page):  # Define the main function
    page.title = "사다리 게임"
    page.window.width = 400  # 갤럭시 S24 width
    page.window.height = 800  # 갤럭시 S24 height
    page.window_resizable = True
    page.vertical_alignment = 'center'
    page.horizontal_alignment = 'center'
    page.padding = 20  # Add padding to the page

    # # assets 디렉토리 존재 확인 및 메시지 출력
    # assets_dir = "./assets"
    # err_message = ""
    # if not os.path.exists(assets_dir):
    #     print(f"Error: '{assets_dir}' directory not found in the same directory as main.py.")
    #     # err_message 변수에 print 메세지를 저장해주세요
    #     err_message += f"Error: '{assets_dir}' not found."
    # else:
    #     image_path = os.path.join(assets_dir, "ladder_img.jpg")
    #     if not os.path.exists(image_path):
    #         print(f"Error: '{image_path}' image file not found in '{assets_dir}' directory.")
    #         err_message += f"Error: '{image_path}' not found."
    #     else:
    #         print(f"'{image_path}' image file found and will be used as background.")
    #         err_message += f"Succ: '{image_path}' found."

    def close_dialog(e):
        page.close(dlg)

    dlg = ft.AlertDialog(
        title=ft.Text(
            "Game Info.",
            color="black",
            size=20,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        content=ft.Column(
            [
                ft.Text("Email: jaekwonyi@naver.com", color="black", size=16),
                ft.Text("Ver: 0.9.0", color="black", size=16),
                ft.Text("Desc.: This is a ladder game.", color="black", size=16),
                # ft.Text(err_message, color="black", size=16),
            ],
            tight=True,
        ),
        bgcolor="white",
        title_padding=10,
        content_padding=10,
        shape=ft.RoundedRectangleBorder(radius=10),
        actions=[ft.TextButton("OK", on_click=close_dialog)],  # 확인 버튼 추가
        actions_alignment=ft.MainAxisAlignment.END,  # 버튼 정렬
    )

    ladder_game = LadderGame(page)
    page.appbar = ft.AppBar(
        title=ft.Text("LADDER GAME"),
        center_title=True,
        bgcolor="#00796B",
        leading=ft.IconButton(ft.Icons.REFRESH, tooltip="NEW GAME", on_click=ladder_game.new_game),
        actions=[
            ft.IconButton(
                ft.Icons.GRID_GOLDENRATIO,
                tooltip="Generate",
                on_click=ladder_game.generate_ladder,
                disabled=True,
            ),  # Changed to self.generate_ladder
            # ft.ElevatedButton("Open", on_click=lambda e: page.open(dlg)),
            ft.IconButton(
                ft.Icons.PERSON, tooltip="Author", on_click=lambda e: page.open(dlg)
            ),  # 람다 함수로 page 전달 (유지)
            # 디버깅용으로 활성화하지 마세요
            # ft.IconButton(ft.Icons.VIEW_LIST, tooltip="로그 보기", on_click=ladder_game.toggle_log_visibility),
        ],
    )

    # page.on_keyboard_event = lambda e: page.close_dialog() if e.key == "escape" else None #Added escape key to close dialog
    page.add(ladder_game)


if __name__ == "__main__":
    # 현재 스크립트 파일의 절대 경로를 기준으로 assets 폴더 경로 생성
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_folder = os.path.join(base_dir, "assets")

    ft.app(target=main, assets_dir=assets_folder)  # Run the app

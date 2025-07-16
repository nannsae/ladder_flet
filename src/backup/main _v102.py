# main.py
import os
import flet as ft
import random
import asyncio

class LadderGame(ft.Container):
    # --- No changes in LadderGame.__init__ up to self.content ---
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        #self.edit_callback = edit_callback # Store the callback function passed from main
        self.num_participants = 0
        self.buttons = []
        self.name_entries = []
        self.result_boxes = []
        self.horizontal_lines = []
        self.vertical_lines = []  # Store vertical line coordinates
        self.colors = ["orange", "cyan", "green", "purple", "brown"]  # Participant colors
        self.current_animations = []
        self.default_background = ft.DecorationImage("ladder_img.jpg", fit=ft.ImageFit.CONTAIN) # 기본 배경 이미지 저장
        self.is_win_state = False # Win 상태인지 확인하는 변수 추가

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

        self.initial_view_column = ft.Column(
            controls=[self.initial_view_container],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )

        self.participant_frame = ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND, spacing=10)

        self.canvas_container = ft.Container(
            width=320,
            height=480,
            border=ft.border.all(1, "black"),
            content=ft.Stack(),
            image=self.default_background,
        )

        self.canvas = self.canvas_container.content
        self.log_text = ft.TextField(
            multiline=True, read_only=True, expand=True, height=150, border_color="black", visible=False
        )
        self.result_frame = ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND, spacing=10)

        self.main_view = ft.Column(
            controls=[
                self.participant_frame,
                self.canvas_container,
                self.result_frame,
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

    def edit_callback(self, index, result_box_control: ft.TextField):
        """Creates and shows an AlertDialog to edit a result box value."""
        # Create a TextField for editing within the dialog
        edit_field = ft.TextField(
            value=result_box_control.value, # Pre-fill with current value
            label="New Result",
            autofocus=True, # Focus the field when dialog opens (still useful as a fallback)
            max_length=6,  # Limit input to 6 characters
            on_submit=lambda e: save_and_close(e) # Allow saving with Enter key
        )

        def save_and_close(e):
            new_value = edit_field.value.strip() # Get the edited value and remove whitespace
            if new_value: # Only update if the new value is not empty
                result_box_control.value = new_value
                result_box_control.update() # Update the specific TextField in the UI
                #page.update()
            self.page.close(edit_dialog) # Close the dialog

        def close_any_dialog(dlg, e):
            self.page.close(dlg)


        edit_dialog = ft.AlertDialog(
            modal=True, # Prevent interaction with the background
            title=ft.Text(f"Edit Result {index + 1}"),
            content=edit_field, # The TextField for editing
            actions=[
                # Cancel button closes the dialog without saving
                ft.TextButton("Cancel", on_click=lambda e: close_any_dialog(edit_dialog, e)),
                # Save button calls the save_and_close function
                ft.TextButton("Save", on_click=save_and_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            # --- Modified: Added on_open handler ---
            #on_open=lambda e: edit_field.focus() or edit_field.select_all(), # Focus and select all text when dialog opens
            # --- End of modification ---
        )
        self.page.open(edit_dialog)
        edit_field.focus()
        self.page.update()

    def set_participants(self, e):
        self.num_participants = int(self.num_spinbox.value)
        self.initial_view_column.visible = False
        self.main_view.visible = True
        self.page.window.width = 400
        self.page.window.height = 800
        self.page.window_resizable = True
        self.page.update()
        self.create_main_widgets()
        self.page.appbar.actions[0].disabled = False
        self.page.update()
        # --- Added: Start blinking the generate icon after setting participants ---
        if self.page and self.page.loop:
             self.page.loop.create_task(self.blink_generate_icon())
        # --- End of addition ---

    def generate_default_results(self):
        """Generates default results with one 'Win' and the rest 'Lose'."""
        default_results = ["Lose"] * self.num_participants
        win_index = random.randint(0, self.num_participants - 1)
        default_results[win_index] = "Win"
        return default_results
    
    def create_main_widgets(self):
        self.participant_frame.controls.clear()
        self.result_frame.controls.clear()
        self.buttons = []
        self.name_entries = []
        self.result_boxes = []

        default_names = ["=A=", "=B=", "=C=", "=D=", "=E="]

        default_results = self.generate_default_results()

        for i in range(self.num_participants):
            # Start button
            start_button = ft.ElevatedButton(
                f"{i+1}",
                on_click=lambda e, i=i: self.start_game(i),
                height=40,
                width=50,
                color=self.colors[i],
                disabled=True,
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
                border_color="black",
                read_only=True, # Make result_box read-only for direct typing
                # Modified: Call handle_result_box_click instead of opening dialog directly
                on_click=lambda e, idx=i: self.handle_result_box_click(idx),
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

    # --- Added: Method to handle result box click and call the callback ---
    def handle_result_box_click(self, index):
        """Calls the edit callback function passed from main."""
        if index < len(self.result_boxes): # Safety check
            # Pass the index and the actual result_box control to the callback
            self.edit_callback(index, self.result_boxes[index])

    def generate_horizontal_lines(self):
        self.horizontal_lines = []
        width = round(self.canvas_container.width / 10) * 10
        height = round(self.canvas_container.height / 10) * 10
        self.canvas.controls.clear()
        self.update()

        self.draw_vertical_lines(height)

        num_horizontal_lines = random.randint(self.num_participants * 2, self.num_participants * 5)
        y_coords_per_pair = {i: [] for i in range(len(self.vertical_lines) - 1)}

        # Ensure exactly 2 horizontal lines between each pair of vertical lines
        for i in range(len(self.vertical_lines) - 1):
            x1, _, x2, _ = self.vertical_lines[i][0], self.vertical_lines[i][1], self.vertical_lines[i + 1][0], self.vertical_lines[i + 1][1]
            horizontal_count = 0
            while horizontal_count < 2:  # Ensure exactly 2 horizontal lines
                y = random.randint(30, height - 50)
                y = round(y / 10) * 10  # Ensure y is a multiple of 10
                if not any(abs(y - yc) < self.get_min_y_distance() for yc in y_coords_per_pair[i]):  # Ensure minimum vertical distance within the pair
                    # Ensure y is not the same as any y in adjacent pairs
                    if i > 0 and y in y_coords_per_pair[i - 1]:
                        continue
                    if i < len(self.vertical_lines) - 2 and y in y_coords_per_pair[i + 1]:
                        continue
                    y_coords_per_pair[i].append(y)
                    self.horizontal_lines.append((x1, y, x2, y))
                    horizontal_count += 1

        # Add additional random horizontal lines
        for _ in range(num_horizontal_lines - len(self.horizontal_lines)):
            available_x_coords = [x for x, _, _, _ in self.vertical_lines]
            x1_index = random.randint(0, len(available_x_coords) - 2)
            x1 = available_x_coords[x1_index]
            x2 = available_x_coords[x1_index + 1]

            y = random.randint(30, height - 50)
            y = round(y / 10) * 10  # Ensure y is a multiple of 10

            # Ensure minimum vertical distance and no duplicate y in adjacent pairs
            if not any(abs(y - yc) < self.get_min_y_distance() for yc in y_coords_per_pair[x1_index]):
                if x1_index > 0 and y in y_coords_per_pair[x1_index - 1]:
                    continue
                if x1_index < len(self.vertical_lines) - 2 and y in y_coords_per_pair[x1_index + 1]:
                    continue
                y_coords_per_pair[x1_index].append(y)
                self.horizontal_lines.append((x1, y, x2, y))

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

        self.log_text.value += f"Vertical lines: {self.vertical_lines}\n"
        self.log_text.value += f"Horizontal lines: {self.horizontal_lines}\n"
        self.update()
 
    def draw_vertical_lines(self, height):
        if self.main_view.visible:
            line_spacing = self.get_line_spacing()
            total_width = self.canvas_container.width
            side_margin = line_spacing / 2
            available_width = total_width - (side_margin * 2)
            if self.num_participants > 1:
                inner_spacing = available_width / (self.num_participants - 1)
            else:
                inner_spacing = 0

            for i in range(self.num_participants):
                if self.num_participants > 1:
                    x = side_margin + (i * inner_spacing)
                else:
                    x = total_width / 2
                x = round(x / 10) * 10
                x = int(x)
                current_height = int(round(height / 10) * 10)
                self.canvas.controls.append(
                    ft.Container(
                        left=x,
                        top=0,
                        width=2,
                        height=current_height,
                        bgcolor="grey",
                    )
                )
                self.vertical_lines.append((x, 0, x, current_height))
                self.log_text.value += f"Vertical line: start=({x}, 0), end=({x}, {current_height})\n"
            #vertical_lines를 x좌표값 기준으로 정렬
            self.vertical_lines.sort(key=lambda x: x[0])
            self.log_text.value += f"Vertical lines: {self.vertical_lines}\n"


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

        # --- Disable Generate button during animation ---
        if self.page and self.page.appbar and len(self.page.appbar.actions) > 0:
            self.page.appbar.actions[0].disabled = True
        self.update()
        self.page.loop.create_task(self.animate_line(participant_index))

    async def animate_line(self, participant_index):
        width = round(self.canvas_container.width / 10) * 10
        height = round(self.canvas_container.height / 10) * 10

        line_spacing = self.get_line_spacing()
        total_width = self.canvas_container.width
        side_margin = line_spacing / 2
        available_width = total_width - (side_margin * 2)
        if self.num_participants > 1:
            inner_spacing = available_width / (self.num_participants - 1)
        else:
            inner_spacing = 0

        if self.num_participants > 1:
            x = int((self.vertical_lines[participant_index][0] * 10) / 10)
            print(f"participant_index: {participant_index}, x좌표값: {x}")
        else:
            x = int(total_width / 2)

        y = 10
        direction = 0  # 0: down, 1: right, 2: left
        color = self.colors[participant_index]

        line_container = ft.Container(
            left=x,
            top=y,
            width=5,
            height=0,
            bgcolor=color,
        )
        self.canvas.controls.append(line_container)

        while y < height - 5:
            for x1, y1, x2, y2 in self.horizontal_lines:
                if direction == 0 and abs(y - y1) < 5 and x1 <= x <= x2:
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
                line_container.width = 5
                line_container.height = 10
                y += 10
                line_container.top = y
            elif direction == 1:
                line_container.width = 10
                line_container.height = 5
                x += 10
                line_container.left = x
                line_container.top = y
            elif direction == 2:
                line_container.width = 10
                line_container.height = 5
                x -= 10
                line_container.left = x
                line_container.top = y

            self.update()
            await asyncio.sleep(0.02)  # Wait for 2ms, changed from 0.01 to 0.1

        if self.num_participants > 1:
            result_index = int(round((x - side_margin) / inner_spacing))
        else:
            result_index = 0

        self.result_boxes[result_index].bgcolor = color
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

    def update(self):
        if self.page is not None:
            self.page.update()

    def new_game(self, e):
        self.num_participants = 0
        self.buttons = []
        self.name_entries = []
        self.result_boxes = []
        self.horizontal_lines = []
        self.vertical_lines = []
        self.current_animations = []
        self.log_text.value = ""
        self.initial_view_column.visible = True
        self.main_view.visible = False
        self.canvas.controls.clear()
        self.update()
        self.participant_frame.controls.clear()
        self.result_frame.controls.clear()
        self.page.appbar.actions[0].disabled = True
        self.page.update()
        self.canvas_container.image = self.default_background
        self.is_win_state = False

        # Disable Generate button in AppBar
        if self.page and self.page.appbar and len(self.page.appbar.actions) > 0:
            self.page.appbar.actions[0].disabled = True

        self.update() # Update UI to reflect reset

        # --- Added: Start blinking the generate icon ---
        # Note: This blink will happen while the button is disabled.
        # if self.page and self.page.loop:
        #      self.page.loop.create_task(self.blink_generate_icon())
        # --- End of addition ---

    async def blink_generate_icon(self):
        """Blinks the 'Generate' icon in the AppBar for 5 seconds."""
        if not (self.page and self.page.appbar and len(self.page.appbar.actions) > 0):
            return # Safety check

        generate_button = self.page.appbar.actions[0]
        original_color = generate_button.icon_color # Store original color (might be None)
        blink_color = ft.colors.RED

        for i in range(10): # Blink 10 times (on/off cycle = 2 steps) over 5 seconds (20 * 0.25s = 5s)
            is_on = i % 2 == 0
            generate_button.icon_color = blink_color if is_on else original_color
            self.page.update()
            await asyncio.sleep(0.25)

        # Restore original state (color only, keep disabled state)
        generate_button.icon_color = original_color
        self.page.update()

    def generate_ladder(self, e):
        if self.main_view.visible:
            self.log_text.value = ""
            self.canvas.controls.clear()
            self.horizontal_lines = []
            self.vertical_lines = []
            self.current_animations = []
            for name_entry in self.name_entries:
                name_entry.color = None
            
            default_results = self.generate_default_results()
            # --- Modified: Reset result box values and appearance ---
            # Generate new random results when ladder is regenerated
            # default_results = ["Lose"] * self.num_participants
            # win_index = random.randint(0, self.num_participants - 1)
            # default_results[win_index] = "Win"

            for i, result_box in enumerate(self.result_boxes):
                result_box.value = default_results[i] # Assign new default value
                result_box.bgcolor = None
                result_box.border_color = "black"
            # --- End of modification ---
            self.update()

            self.generate_horizontal_lines()
            self.update()
            for button in self.buttons:
                button.disabled = False
            self.update()
            self.page.appbar.actions[0].disabled = False
            self.update()
            self.canvas_container.image = self.default_background
            self.is_win_state = False
            self.update()

    def toggle_log_visibility(self, e):
        print(self.log_text.value)

# --- main function ---
def main(page: ft.Page):
    page.title = "사다리 게임"
    page.window.width = 400
    page.window.height = 800
    page.window.resizable = True
    page.vertical_alignment = 'center'
    page.horizontal_alignment = 'center'
    page.padding = 20

    def close_any_dialog(dlg, e):
        page.close(dlg)

    info_dlg = ft.AlertDialog(
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
                ft.Text("Ver: 1.0.2", color="black", size=16), # Version bump
                ft.Text("Desc.: This is a ladder game.", color="black", size=16),
            ],
            tight=True,
        ),
        bgcolor="white",
        title_padding=10,
        content_padding=10,
        shape=ft.RoundedRectangleBorder(radius=10),
        # Modified: Use the helper function
        actions=[ft.TextButton("OK", on_click=lambda e: close_any_dialog(info_dlg, e))],
        actions_alignment=ft.MainAxisAlignment.END,
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
                tooltip="Generate a ladder",
                on_click=ladder_game.generate_ladder,
                disabled=True,
            ),
            ft.IconButton(
                ft.Icons.PERSON, tooltip="Author", on_click=lambda e: page.open(info_dlg)
            ),
            # 디버깅용,, 활성화하지 마세요
            #ft.IconButton(ft.Icons.VIEW_LIST, tooltip="로그 보기", on_click=ladder_game.toggle_log_visibility),
        ],
    )

    page.add(ladder_game)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_folder = os.path.join(base_dir, "assets")

    # Check for assets folder existence (optional but good practice)
    if not os.path.isdir(assets_folder):
        print(f"Warning: Assets directory not found at {assets_folder}")
        # Decide how to handle this - maybe exit or use default colors/no images

    ft.app(target=main, assets_dir=assets_folder)

# main.py
import os
import flet as ft
import random
import asyncio

# --- Constants for width calculation ---
BASE_WIDTH = 320  # Width for up to 5 participants
EXTRA_WIDTH_PER_PARTICIPANT = 65 # Additional width needed for each participant > 5

class LadderGame(ft.Container):
    # --- No changes in LadderGame.__init__ up to self.content ---
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.num_participants = 0
        self.buttons = []
        self.name_entries = []
        self.result_boxes = []
        self.horizontal_lines = []
        self.vertical_lines = []
        self.colors = [
            "orange", "cyan", "green", "purple", "brown",
            "pink", "teal", "indigo", "lime", "deeporange" # Added more colors for up to 10
        ]
        self.current_animations = []
        self.default_background = ft.DecorationImage("ladder_img.jpg", fit=ft.ImageFit.FILL)
        self.is_win_state = False
        self.active_animations_count = 0

        # --- MODIFIED: Participant selection ---
        self.num_label = ft.Text("Participants (2-10):", bgcolor="white", color="black", size=14) # Updated label
        self.num_spinbox = ft.Dropdown(
            options=[ft.dropdown.Option(str(i)) for i in range(2, 11)], # Updated range to 11 (for 2-10)
            value="3",
            width=90,
            color="cyan",
            bgcolor="cyan",
            text_align=ft.TextAlign.RIGHT,
            text_style=ft.TextStyle(color="cyan"),
            menu_height = 200,     
        )
        # --- End of MODIFICATION ---
        self.num_button = ft.ElevatedButton("Confirm", on_click=self.click_participants_game, height=40)

        self.initial_view = ft.Row(
            controls=[self.num_label, self.num_spinbox, self.num_button],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.initial_view_container = ft.Container(
            content=self.initial_view,
            width=BASE_WIDTH, # Use base width initially
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

        # --- These frames will have dynamic width ---
        self.participant_frame = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            spacing=10,
            width=BASE_WIDTH # Initial width
        )
        self.canvas_container = ft.Container(
            width=BASE_WIDTH, # Initial width
            height=480,
            border=ft.border.all(1, "black"),
            content=ft.Stack(),
            image=self.default_background,
        )
        self.result_frame = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            spacing=10,
            width=BASE_WIDTH # Initial width
        )
        # --- End of dynamic width frames ---

        self.canvas = self.canvas_container.content
        self.log_text = ft.TextField(
            multiline=True, read_only=True, expand=True, height=150, border_color="black", visible=False
        )

        self.main_view = ft.Column(
            controls=[
                self.participant_frame,
                self.canvas_container,
                self.result_frame,
            ],
            visible=False,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            # expand=True, # Remove expand=True as width will be set explicitly
            width=BASE_WIDTH # Initial width
        )

        # --- MODIFIED: Wrap main_view in a scrolling Row ---
        self.main_view_scroll_wrapper = ft.Row(
            [self.main_view],
            scroll=ft.ScrollMode.ADAPTIVE, # Enable horizontal scrolling when needed
            expand=True, # Allow the Row to take available vertical space
            vertical_alignment=ft.CrossAxisAlignment.START # Align main_view to the top within the scroll
        )
        # --- End of MODIFICATION ---

        self.content = ft.Column(
            # --- MODIFIED: Use the scroll wrapper ---
            controls=[self.initial_view_column, self.main_view_scroll_wrapper],
            # --- End of MODIFICATION ---
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    # --- ADDED: Helper method for dynamic width ---
    def _calculate_dynamic_width(self):
        """Calculates the required width based on the number of participants."""
        if self.num_participants <= 5:
            return BASE_WIDTH
        else:
            extra_participants = self.num_participants - 5
            return BASE_WIDTH + (extra_participants * EXTRA_WIDTH_PER_PARTICIPANT)
    # --- End of ADDED method ---

    # --- ADDED: Method to edit start button text ---
    def edit_start_button_text(self, index, button_control: ft.ElevatedButton):
        """Creates and shows an AlertDialog to edit a start button's text."""
        edit_field = ft.TextField(
            value=button_control.text, # Pre-fill with current button text
            label="New Button Text",
            autofocus=True,
            max_length=4,  # Limit input length (adjust as needed)
            on_submit=lambda e: save_and_close(e)
        )

        def save_and_close(e):
            new_value = edit_field.value.strip()
            if new_value: # Only update if not empty
                button_control.text = new_value # Update button text
                button_control.update() # Update the specific button in the UI
            self.page.close(edit_dialog)

        def close_any_dialog(dlg, e):
            self.page.close(dlg)

        edit_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Edit Button {index + 1} Text"),
            content=edit_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_any_dialog(edit_dialog, e)),
                ft.TextButton("Save", on_click=save_and_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(edit_dialog)
        edit_field.focus()
        self.page.update()
    # --- End of ADDED method ---

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
        )
        self.page.open(edit_dialog)
        edit_field.focus()
        self.page.update()

    def click_participants_game(self, e):
        self.num_participants = int(self.num_spinbox.value)
        self.initial_view_column.visible = False
        # self.main_view.visible = True # Visibility handled by wrapper now
        self.main_view_scroll_wrapper.visible = True # Show the scroll wrapper

        # --- MODIFIED: Adjust window width slightly if many participants ---
        # Keep window height fixed for now
        # self.page.window.width = 400 # Keep original or slightly increase? Let's keep 400.
        # self.page.window.height = 800
        # self.page.window_resizable = True
        # --- End of MODIFICATION ---

        # --- MODIFIED: Calculate and set dynamic width ---
        dynamic_width = self._calculate_dynamic_width()
        self.participant_frame.width = dynamic_width
        self.canvas_container.width = dynamic_width
        self.result_frame.width = dynamic_width
        self.main_view.width = dynamic_width # Set width for the column inside scroll wrapper
        self.main_view.visible = True # Make the actual content visible
        # --- End of MODIFICATION ---

        self.page.update() # Update page dimensions and visibility first
        self.create_main_widgets() # Now create widgets within the sized containers

        # --- MODIFIED: Enable Generate button only if no animations are running ---
        # Initially, active_animations_count is 0, so it should be enabled unless generate_ladder hasn't run.
        # Let's keep it disabled initially, and enable it in generate_ladder.
        # self.page.appbar.actions[0].disabled = self.active_animations_count > 0
        self.page.appbar.actions[0].disabled = False # Enable Generate button now
        # --- End of MODIFICATION ---
        self.page.update()

        if self.page and self.page.loop:
             self.page.loop.create_task(self.blink_generate_icon())

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

        # default_names = ["=A=", "=B=", "=C=", "=D=", "=E="] # Not used currently

        default_results = self.generate_default_results()

        # --- Adjust widget sizes slightly if many participants? (Optional) ---
        # Could make buttons/boxes slightly narrower if self.num_participants > 7, for example.
        # Let's keep them fixed for now for simplicity.
        button_width = 50
        result_box_width = 50
        # ---

        for i in range(self.num_participants):
            # Start button
            start_button = ft.ElevatedButton(
                f"{i+1}",
                # --- MODIFIED: Use dispatcher method for on_click ---
                on_click=lambda e, idx=i: self.handle_start_button_click(idx),
                # --- End of MODIFICATION ---
                height=40,
                width=button_width, # Use variable width
                # Ensure enough colors are available
                color=self.colors[i % len(self.colors)],
                # --- MODIFIED: Start enabled to allow editing before generation ---
                disabled=False,
                # --- End of MODIFICATION ---
            )
            self.buttons.append(start_button)

            # Name entry (still hidden)
            name_entry = ft.TextField(
                value="", width=10, height=0, max_length=3, text_align=ft.TextAlign.CENTER,
                text_size=0, content_padding=0,
            )
            self.name_entries.append(name_entry)

            # Result box
            result_box = ft.TextField(
                value=default_results[i % len(default_results)],
                width=result_box_width, # Use variable width
                height=40,
                text_align=ft.TextAlign.CENTER,
                text_size=14,
                content_padding=0,
                border_color="black",
                read_only=True,
                on_click=lambda e, idx=i: self.handle_result_box_click(idx),
            )
            self.result_boxes.append(result_box)

            # Participant column (top)
            participant_column = ft.Column(
                controls=[start_button, name_entry],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            )
            self.participant_frame.controls.append(participant_column)
            # Result box (bottom)
            self.result_frame.controls.append(result_box)

        # Update needed to render the newly added controls within the sized frames
        self.update()

    # --- ADDED: Dispatcher for start button clicks ---
    def handle_start_button_click(self, index):
        """Handles clicks on the top start buttons.

        If horizontal lines exist, starts the game animation.
        If no horizontal lines exist, opens the edit dialog for the button text.
        """
        if not self.horizontal_lines: # Check if the list is empty (no ladder generated)
            # Call the edit function for the button text
            if index < len(self.buttons): # Safety check
                self.edit_start_button_text(index, self.buttons[index])
        else:
            # Horizontal lines exist, so start the game animation
            self.start_game(index)
    # --- End of ADDED method ---

    def handle_result_box_click(self, index):
        """Calls the edit callback function passed from main."""
        if index < len(self.result_boxes): # Safety check
            self.edit_callback(index, self.result_boxes[index])

    def generate_horizontal_lines(self):
        self.horizontal_lines = []
        # --- Use the potentially wider canvas width ---
        width = round(self.canvas_container.width / 10) * 10
        height = round(self.canvas_container.height / 10) * 10
        # ---
        self.canvas.controls.clear()
        # self.update() # Update called later after drawing

        self.draw_vertical_lines(height) # Draw vertical lines based on current width

        # --- Logic for generating lines remains mostly the same ---
        # It now operates within the potentially wider canvas bounds
        num_horizontal_lines = random.randint(self.num_participants * 2, self.num_participants * 5)
        y_coords_per_pair = {i: [] for i in range(len(self.vertical_lines) - 1)}

        # Ensure minimum lines between pairs
        for i in range(len(self.vertical_lines) - 1):
            if i + 1 >= len(self.vertical_lines): continue # Safety check
            x1, _, _, _ = self.vertical_lines[i]
            x2, _, _, _ = self.vertical_lines[i + 1]
            horizontal_count = 0
            attempts = 0 # Prevent infinite loops if placement is difficult
            while horizontal_count < 2 and attempts < 50:
                attempts += 1
                y = random.randint(30, height - 50)
                y = round(y / 10) * 10
                valid_y = True
                # Check distance within the current pair
                if any(abs(y - yc) < self.get_min_y_distance() for yc in y_coords_per_pair[i]):
                    valid_y = False
                # Check distance with left adjacent pair
                if valid_y and i > 0 and y in y_coords_per_pair.get(i - 1, []):
                    valid_y = False
                # Check distance with right adjacent pair
                if valid_y and i < len(self.vertical_lines) - 2 and y in y_coords_per_pair.get(i + 1, []):
                     valid_y = False

                if valid_y:
                    y_coords_per_pair[i].append(y)
                    self.horizontal_lines.append((x1, y, x2, y))
                    horizontal_count += 1

        # Add additional random lines
        additional_lines_needed = num_horizontal_lines - len(self.horizontal_lines)
        attempts = 0
        while additional_lines_needed > 0 and attempts < 100:
            attempts += 1
            if len(self.vertical_lines) < 2: break # Need at least two vertical lines

            x1_index = random.randint(0, len(self.vertical_lines) - 2)
            x1, _, _, _ = self.vertical_lines[x1_index]
            x2, _, _, _ = self.vertical_lines[x1_index + 1]

            y = random.randint(30, height - 50)
            y = round(y / 10) * 10

            valid_y = True
            # Check distance within the chosen pair
            if any(abs(y - yc) < self.get_min_y_distance() for yc in y_coords_per_pair[x1_index]):
                valid_y = False
            # Check distance with left adjacent pair
            if valid_y and x1_index > 0 and y in y_coords_per_pair.get(x1_index - 1, []):
                valid_y = False
            # Check distance with right adjacent pair
            if valid_y and x1_index < len(self.vertical_lines) - 2 and y in y_coords_per_pair.get(x1_index + 1, []):
                 valid_y = False

            if valid_y:
                y_coords_per_pair[x1_index].append(y)
                self.horizontal_lines.append((x1, y, x2, y))
                additional_lines_needed -= 1
        # --- End of line generation logic ---

        # Draw horizontal lines
        for x1, y, x2, _ in self.horizontal_lines:
            line_width = int(x2 - x1)
            self.canvas.controls.append(
                ft.Container(
                    left=int(x1), top=y, width=line_width, height=2, bgcolor="grey",
                )
            )
            # self.log_text.value += f"H: ({int(x1)},{y})-({int(x2)},{y})\n" # Shortened log

        # self.log_text.value += f"V lines: {self.vertical_lines}\n"
        # self.log_text.value += f"H lines count: {len(self.horizontal_lines)}\n"
        self.update() # Update after drawing everything

    def draw_vertical_lines(self, height):
        self.vertical_lines = [] # Clear previous lines before drawing
        if self.main_view.visible:
            # --- Calculations now use the current canvas_container.width ---
            line_spacing = self.get_line_spacing() # Depends on current width
            total_width = self.canvas_container.width
            side_margin = line_spacing / 2
            available_width = total_width - (side_margin * 2)
            inner_spacing = available_width / (self.num_participants - 1) if self.num_participants > 1 else 0
            # ---

            for i in range(self.num_participants):
                x = side_margin + (i * inner_spacing) if self.num_participants > 1 else total_width / 2
                x = int(round(x / 10) * 10) # Keep rounding
                current_height = int(round(height / 10) * 10)

                self.canvas.controls.append(
                    ft.Container(left=x, top=0, width=2, height=current_height, bgcolor="grey")
                )
                # Store only necessary info (start x, start y, end x, end y)
                self.vertical_lines.append((x, 0, x, current_height))
                # self.log_text.value += f"V: ({x},0)-({x},{current_height})\n" # Shortened log

            self.vertical_lines.sort(key=lambda line: line[0]) # Sort by x-coordinate
            #self.log_text.value += f"Sorted V lines: {self.vertical_lines}\n"

    def get_line_spacing(self):
        # Uses the current width of the canvas container
        width = round(self.canvas_container.width / 10) * 10
        # Need at least num_participants + 1 gaps (including margins)
        return width / (self.num_participants + 1) if self.num_participants > 0 else width

    def get_min_y_distance(self):
        return 20 # Keep minimum vertical distance

    def start_game(self, participant_index):
        """Starts the ladder animation for a given participant."""
        # This method is now only called by handle_start_button_click
        # when horizontal lines exist.

        self.canvas_container.image = self.default_background
        self.is_win_state = False
        # self.update() # Update called later

        # --- Check button state again just in case ---
        if participant_index >= len(self.buttons) or self.buttons[participant_index].disabled:
            print(f"Warning: start_game called for disabled or invalid button index {participant_index}")
            return
        # ---

        if participant_index in self.current_animations:
            return

        self.current_animations.append(participant_index)
        self.buttons[participant_index].disabled = True

        self.active_animations_count += 1
        # Disable Generate button during animation
        if self.page and self.page.appbar and len(self.page.appbar.actions) > 0:
            self.page.appbar.actions[0].disabled = True

        self.update() # Update button state and appbar
        self.page.loop.create_task(self.animate_line(participant_index))

    async def animate_line(self, participant_index):
        # --- Calculations use current canvas width ---
        width = round(self.canvas_container.width / 10) * 10
        height = round(self.canvas_container.height / 10) * 10
        line_spacing = self.get_line_spacing()
        total_width = self.canvas_container.width
        side_margin = line_spacing / 2
        available_width = total_width - (side_margin * 2)
        inner_spacing = available_width / (self.num_participants - 1) if self.num_participants > 1 else 0
        # ---

        # --- Get starting X from the sorted vertical_lines list ---
        if participant_index < len(self.vertical_lines):
             start_x = self.vertical_lines[participant_index][0] # Get x from tuple (x1, y1, x2, y2)
             x = int(round(start_x / 10) * 10)
             # print(f"Animate Start: P{participant_index}, VLineX: {start_x}, RoundedX: {x}")
        else:
             # Fallback or error handling if index is out of bounds
             print(f"Error: participant_index {participant_index} out of range for vertical_lines (len {len(self.vertical_lines)})")
             x = int(total_width / 2) # Default to center as fallback
             # Decrement animation count as this animation can't proceed correctly
             self.active_animations_count -= 1
             if self.active_animations_count == 0 and self.page.appbar and len(self.page.appbar.actions) > 0:
                 self.page.appbar.actions[0].disabled = False
             # Re-enable button immediately
             if participant_index < len(self.buttons):
                 self.buttons[participant_index].disabled = False
             if participant_index in self.current_animations:
                 self.current_animations.remove(participant_index)
             self.update()
             return # Stop animation if start point is invalid
        # ---

        y = 10
        direction = 0
        color = self.colors[participant_index % len(self.colors)]

        line_container = ft.Container(left=x, top=y, width=5, height=0, bgcolor=color)
        self.canvas.controls.append(line_container)
        self.update() # Show the initial dot

        # --- Animation loop logic remains the same, operates on current x, y ---
        while y < height - 5:
            moved_horizontally = False
            # Check horizontal lines based on current position (x, y) and direction
            for hx1, hy, hx2, _ in self.horizontal_lines:
                # Moving Down (direction 0) and hitting a horizontal line
                if direction == 0 and abs(y - hy) < 5 and hx1 <= x <= hx2:
                    if x < (hx1 + hx2) / 2: # Closer to left end
                        direction = 1  # Go right
                        x = hx1        # Align with start of horizontal line
                    else:              # Closer to right end
                        direction = 2  # Go left
                        x = hx2        # Align with end of horizontal line
                    moved_horizontally = True
                    break # Exit inner loop once direction changes
                # Moving Right (direction 1) and reaching the end of the horizontal line
                elif direction == 1 and abs(x - hx2) < 5 and abs(y - hy) < 5: # Check y alignment too
                    direction = 0  # Go down
                    x = hx2        # Ensure alignment
                    moved_horizontally = True
                    break
                # Moving Left (direction 2) and reaching the start of the horizontal line
                elif direction == 2 and abs(x - hx1) < 5 and abs(y - hy) < 5: # Check y alignment too
                    direction = 0  # Go down
                    x = hx1        # Ensure alignment
                    moved_horizontally = True
                    break

            # Update position based on direction
            step = 10
            if direction == 0: # Down
                line_container.width = 5
                line_container.height = step
                y += step
                line_container.top = y
                # Ensure x doesn't drift if we just finished moving horizontally
                if moved_horizontally: line_container.left = x
            elif direction == 1: # Right
                line_container.width = step
                line_container.height = 5
                x += step
                line_container.left = x
                line_container.top = y # Keep y the same while moving horizontally
            elif direction == 2: # Left
                line_container.width = step
                line_container.height = 5
                x -= step
                line_container.left = x
                line_container.top = y # Keep y the same

            self.update()
            await asyncio.sleep(0.02)
        # --- End of animation loop ---

        # --- Calculate result index based on final x ---
        result_index = 0
        if self.num_participants > 1 and inner_spacing > 0:
            # Find the closest vertical line index based on final x
            closest_dist = float('inf')
            for i, (vx, _, _, _) in enumerate(self.vertical_lines):
                dist = abs(x - vx)
                if dist < closest_dist:
                    closest_dist = dist
                    result_index = i
            # result_index = int(round((x - side_margin) / inner_spacing)) # Old calculation might be less robust
            # Clamp index just in case
            result_index = max(0, min(result_index, self.num_participants - 1))
        elif self.num_participants == 1:
             result_index = 0
        # ---

        if result_index < len(self.result_boxes):
            self.result_boxes[result_index].bgcolor = color
        else:
            print(f"Error: result_index {result_index} out of range for result_boxes (len {len(self.result_boxes)})")


        if participant_index in self.current_animations:
            self.current_animations.remove(participant_index)
        if participant_index < len(self.buttons):
            self.buttons[participant_index].disabled = False
        else:
             print(f"Error: participant_index {participant_index} out of range for buttons (len {len(self.buttons)})")


        self.active_animations_count -= 1
        # Re-enable Generate button ONLY if no other animations are running
        if self.page and self.page.appbar and len(self.page.appbar.actions) > 0:
            if self.active_animations_count == 0:
                self.page.appbar.actions[0].disabled = False

        self.update() # Update result box color, button state, appbar

        # --- Win condition check ---
        if result_index < len(self.result_boxes) and \
           (self.result_boxes[result_index].value == "Win" or self.result_boxes[result_index].value == "당첨"):
            self.canvas_container.image = ft.DecorationImage("award.jpg", fit=ft.ImageFit.FIT_HEIGHT)
            self.is_win_state = True
            self.update()
            # Ensure participant_index is valid before blinking
            if participant_index < len(self.buttons):
                await self.blink_result_box(result_index, participant_index)
        else:
            self.is_win_state = False
        # ---

    async def blink_result_box(self, result_index, participant_index):
        # Ensure indices are valid before accessing elements
        if result_index >= len(self.result_boxes) or participant_index >= len(self.buttons):
            print(f"Error: Invalid indices for blinking - result:{result_index}, participant:{participant_index}")
            return

        original_color = self.result_boxes[result_index].bgcolor
        original_button_color = self.buttons[participant_index].color
        blink_result_color = "yellow"
        blink_button_color = "black"

        for i in range(10):
            is_blink_on = i % 2 == 0
            # Check if controls still exist before modifying
            if result_index < len(self.result_boxes):
                 self.result_boxes[result_index].bgcolor = blink_result_color if is_blink_on else original_color
            if participant_index < len(self.buttons):
                 self.buttons[participant_index].color = blink_button_color if is_blink_on else original_button_color
            self.update()
            await asyncio.sleep(0.2)

        # Restore final state, checking existence again
        if result_index < len(self.result_boxes):
            self.result_boxes[result_index].bgcolor = original_color
        if participant_index < len(self.buttons):
            self.buttons[participant_index].color = original_button_color
        self.update()

    def update(self):
        if self.page is not None:
            # Use try-except for robustness during potentially rapid updates or closing
            try:
                self.page.update()
            except Exception as e:
                print(f"Error during page update: {e}")


    def new_game(self, e):
        self.num_participants = 0
        self.buttons = []
        self.name_entries = []
        self.result_boxes = []
        self.horizontal_lines = [] # Crucial: Clear horizontal lines
        self.vertical_lines = []
        self.current_animations = []
        self.active_animations_count = 0
        self.log_text.value = ""

        self.initial_view_column.visible = True
        # self.main_view.visible = False # Handled by wrapper
        self.main_view_scroll_wrapper.visible = False # Hide the scroll wrapper

        self.canvas.controls.clear()
        self.participant_frame.controls.clear()
        self.result_frame.controls.clear()

        # --- MODIFIED: Reset widths to base ---
        self.participant_frame.width = BASE_WIDTH
        self.canvas_container.width = BASE_WIDTH
        self.result_frame.width = BASE_WIDTH
        self.main_view.width = BASE_WIDTH
        # --- End of MODIFICATION ---

        self.canvas_container.image = self.default_background
        self.is_win_state = False

        # Disable Generate button on new game start
        if self.page and self.page.appbar and len(self.page.appbar.actions) > 0:
            self.page.appbar.actions[0].disabled = True

        self.update()

    async def blink_generate_icon(self):
        """Blinks the 'Generate' icon in the AppBar for 5 seconds."""
        if not (self.page and self.page.appbar and len(self.page.appbar.actions) > 0):
            return

        generate_button = self.page.appbar.actions[0]
        # Use a fallback color if original is None
        original_color = generate_button.icon_color or ft.Colors.WHITE # Assuming default is whiteish
        blink_color = ft.Colors.RED

        for i in range(10):
            is_on = i % 2 == 0
            generate_button.icon_color = blink_color if is_on else original_color
            self.update() # Use self.update for consistency
            await asyncio.sleep(0.25)

        generate_button.icon_color = original_color
        # --- MODIFIED: Keep Generate enabled after blink if no animations ---
        generate_button.disabled = self.active_animations_count > 0
        # --- End of MODIFICATION ---
        self.update()

    def generate_ladder(self, e):
        """Regenerates the ladder view and resets components."""
        if self.main_view.visible: # Check if main view is active
            self.log_text.value = ""
            self.canvas.controls.clear()
            self.horizontal_lines = [] # Clear before generating new ones
            self.vertical_lines = []
            self.current_animations = []
            self.active_animations_count = 0

            # --- MODIFIED: Recalculate and set dynamic width ---
            # This is important if generate is clicked without changing participant count
            dynamic_width = self._calculate_dynamic_width()
            self.participant_frame.width = dynamic_width
            self.canvas_container.width = dynamic_width
            self.result_frame.width = dynamic_width
            self.main_view.width = dynamic_width
            # --- End of MODIFICATION ---

            # Reset name entry appearance (if they were ever used)
            for name_entry in self.name_entries:
                name_entry.color = None # Assuming color indicated state

            # Regenerate default results and update result boxes
            default_results = self.generate_default_results()
            for i, result_box in enumerate(self.result_boxes):
                if i < len(default_results):
                    result_box.value = default_results[i]
                result_box.bgcolor = None
                result_box.border_color = "black"

            # Regenerate the visual ladder lines (this populates self.horizontal_lines)
            self.generate_horizontal_lines() # This now uses the updated width

            # --- MODIFIED: Enable start buttons AFTER generating lines ---
            # Now that lines exist, clicking should start the game.
            for button in self.buttons:
                button.disabled = False
            # --- End of MODIFICATION ---

            # Ensure Generate button in AppBar is enabled (since animation count is 0)
            if self.page and self.page.appbar and len(self.page.appbar.actions) > 0:
                self.page.appbar.actions[0].disabled = False

            # Reset background image and win state
            self.canvas_container.image = self.default_background
            self.is_win_state = False

            self.update() # Update UI with all changes

    def toggle_log_visibility(self, e):
        print(self.log_text.value)

# --- main function (No changes needed here for width/scrolling) ---
def main(page: ft.Page):
    page.title = "사다리 게임"
    # --- Keep window size fixed, rely on internal scrolling ---
    page.window.width = 400
    page.window.height = 800
    # ---
    page.window.resizable = True
    page.vertical_alignment = ft.MainAxisAlignment.CENTER # Use Enum
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER # Use Enum
    page.padding = 20

    def close_any_dialog(dlg, e):
        page.close(dlg)

    info_dlg = ft.AlertDialog(
        title=ft.Text(
            "Game Info.", color="black", size=20, weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        content=ft.Column(
            [
                ft.Text("Email: jaekwonyi@naver.com", color="black", size=16),
                ft.Text("Ver: 1.1.1", color="black", size=16), # Version bump
                ft.Text("Desc.: Ladder game (2-10 players).", color="black", size=16),
                ft.Text("Feat.: Edit buttons before generation.", color="black", size=14),
            ], tight=True,
        ),
        bgcolor="white", title_padding=10, content_padding=10,
        shape=ft.RoundedRectangleBorder(radius=10),
        actions=[ft.TextButton("OK", on_click=lambda e: close_any_dialog(info_dlg, e))],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    ladder_game = LadderGame(page)

    page.appbar = ft.AppBar(
        title=ft.Text("LADDER GAME"), center_title=True, bgcolor="#00796B",
        leading=ft.IconButton(ft.Icons.REFRESH, tooltip="NEW GAME", on_click=ladder_game.new_game),
        actions=[
            ft.IconButton(
                ft.Icons.GRID_GOLDENRATIO, tooltip="Generate a ladder",
                on_click=ladder_game.generate_ladder,
                # --- MODIFIED: Start disabled, enabled after participants confirmed ---
                disabled=True,
                # --- End of MODIFICATION ---
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
    if not os.path.isdir(assets_folder):
        print(f"Warning: Assets directory not found at {assets_folder}")
    ft.app(target=main, assets_dir=assets_folder)

# test_main.py
import unittest
import asyncio
from unittest.mock import patch, Mock, call
import flet as ft

from main import LadderGame

class TestLadderGameBlinkResultBox(unittest.TestCase):

    def setUp(self):
        """Set up the test environment before each test."""
        # Mock the Flet Page object needed by LadderGame
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.update = Mock() # Mock page.update just in case
        # REMOVED THIS LINE: self.mock_page.loop = asyncio.get_event_loop()

        # Instantiate LadderGame with the mocked page
        # If LadderGame's __init__ needs more from page, mock those too
        self.ladder_game = LadderGame(page=self.mock_page)

        # --- Pre-populate necessary attributes for the test ---
        self.ladder_game.num_participants = 3 # Example value
        self.ladder_game.result_boxes = [
            ft.TextField(value="Lose", bgcolor="blue"),
            ft.TextField(value="Win", bgcolor="green"),
            ft.TextField(value="Lose", bgcolor="red")
        ]
        self.ladder_game.buttons = [
            ft.ElevatedButton(text="1", color="blue"),
            ft.ElevatedButton(text="2", color="green"),
            ft.ElevatedButton(text="3", color="red")
        ]
        # Ensure colors list is accessible
        self.ladder_game.colors = ["blue", "green", "red"] # Make sure this matches the number of participants/boxes

    # Use patch to mock asyncio.sleep and the instance's update method
    @patch('asyncio.sleep', return_value=None) # Mock sleep to run instantly
    @patch.object(LadderGame, 'update')        # Mock the self.update method
    def test_blink_result_box_colors_and_restoration(self, mock_update, mock_sleep):
        """
        Test if the result box and button colors blink correctly
        and are restored to their original values.
        """
        result_index_to_test = 1
        participant_index_to_test = 1
        original_result_bgcolor = self.ladder_game.result_boxes[result_index_to_test].bgcolor
        original_button_color = self.ladder_game.buttons[participant_index_to_test].color

        # Run the async method being tested
        asyncio.run(self.ladder_game.blink_result_box(result_index_to_test, participant_index_to_test))

        # --- Assertions ---
        # 1. Check if colors are restored at the end
        self.assertEqual(
            self.ladder_game.result_boxes[result_index_to_test].bgcolor,
            original_result_bgcolor,
            "Result box background color should be restored."
        )
        self.assertEqual(
            self.ladder_game.buttons[participant_index_to_test].color,
            original_button_color,
            "Button color should be restored."
        )

        # 2. Check if sleep was called the correct number of times (10 times in the loop)
        self.assertEqual(
            mock_sleep.call_count,
            10,
            "asyncio.sleep should be called 10 times."
        )
        # Check if sleep was called with the correct duration
        mock_sleep.assert_called_with(0.2) # Checks the argument of the last call

        # 3. Check if update was called the correct number of times
        # (10 times in the loop + 1 time after restoration = 11)
        self.assertEqual(
            mock_update.call_count,
            11,
            "self.update() should be called 11 times (10 in loop + 1 after)."
        )

    @patch('asyncio.sleep', return_value=None)
    @patch.object(LadderGame, 'update')
    def test_blink_result_box_intermediate_colors(self, mock_update, mock_sleep):
        """
        Test the intermediate color changes during the blink cycle.
        This is more complex due to mocking sleep. We'll check the state
        captured by the mock_update calls.
        """
        result_index_to_test = 0
        participant_index_to_test = 0
        original_result_bgcolor = self.ladder_game.result_boxes[result_index_to_test].bgcolor # Should be "blue" based on setUp
        original_button_color = self.ladder_game.buttons[participant_index_to_test].color # Should be "blue" based on setUp
        blink_result_color = "yellow"
        blink_button_color = "black"

        # --- Store colors before each update call ---
        captured_states = []
        def capture_state_side_effect(*args, **kwargs):
            # Capture the state *before* the mocked update would conceptually happen
            captured_states.append(
                (
                    # Make sure to access the *actual* attributes being modified
                    self.ladder_game.result_boxes[result_index_to_test].bgcolor,
                    self.ladder_game.buttons[participant_index_to_test].color
                )
            )
        mock_update.side_effect = capture_state_side_effect

        # Run the async method
        asyncio.run(self.ladder_game.blink_result_box(result_index_to_test, participant_index_to_test))

        # --- Assertions on captured states ---
        self.assertEqual(len(captured_states), 11, "Should have captured 11 states (10 in loop + 1 final)")

        # Check the first 10 states (inside the loop)
        for i in range(10):
            result_color, button_color = captured_states[i]
            # The state is captured *before* the update, reflecting the change made just before it
            if i % 2 == 0: # Iteration 0, 2, 4, 6, 8: Colors changed to blink state
                self.assertEqual(result_color, blink_result_color, f"Loop {i}: Result color should be {blink_result_color}")
                self.assertEqual(button_color, blink_button_color, f"Loop {i}: Button color should be {blink_button_color}")
            else: # Iteration 1, 3, 5, 7, 9: Colors changed back to original state
                self.assertEqual(result_color, original_result_bgcolor, f"Loop {i}: Result color should be {original_result_bgcolor}")
                self.assertEqual(button_color, original_button_color, f"Loop {i}: Button color should be {original_button_color}")

        # Check the final state (captured by the 11th update call, after restoration)
        final_result_color, final_button_color = captured_states[10]
        self.assertEqual(final_result_color, original_result_bgcolor, "Final state: Result color should be restored")
        self.assertEqual(final_button_color, original_button_color, "Final state: Button color should be restored")


# To run the tests:
if __name__ == '__main__':
    unittest.main()
    # You can run this script directly to execute the tests.
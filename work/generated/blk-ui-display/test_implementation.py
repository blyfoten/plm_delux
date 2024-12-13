Certainly, here's a basic set of unit tests for your Python code using `pytest` and `unittest.mock`:

```python
import pytest
import threading
from unittest.mock import patch, call
from your_module import Direction, ElevatorUI

# Fixture for ElevatorUI
@pytest.fixture
def elevator():
    return ElevatorUI(10)

def test_constructor(elevator):
    """
    Test that the ElevatorUI constructor initializes the correct attributes.
    """
    assert elevator._num_floors == 10
    assert elevator._current_floor == 0
    assert elevator._direction == Direction.IDLE
    assert elevator._status == "IDLE"
    assert isinstance(elevator._lock, threading.Lock)

def test_press_floor_button_valid_floor(elevator):
    """
    Test that press_floor_button starts a new thread if the floor is valid.
    """
    with patch('threading.Thread') as mock_thread:
        elevator.press_floor_button(5)
        mock_thread.assert_called_once_with(target=elevator._move_to_floor, args=(5,))

def test_press_floor_button_invalid_floor(elevator):
    """
    Test that press_floor_button raises a ValueError if the floor is invalid.
    """
    with pytest.raises(ValueError, match='Invalid floor'):
        elevator.press_floor_button(11)

def test_move_to_floor_up(elevator):
    """
    Test that _move_to_floor updates the direction, current floor, and status correctly when moving up.
    """
    with patch('logging.info') as mock_log:
        elevator._move_to_floor(5)
        assert elevator._direction == Direction.UP
        assert elevator._current_floor == 5
        assert elevator._status == 'Moving up'
        mock_log.assert_called_once_with("Elevator moving to floor %s", 5)

def test_move_to_floor_down(elevator):
    """
    Test that _move_to_floor updates the direction, current floor, and status correctly when moving down.
    """
    elevator._current_floor = 5
    with patch('logging.info') as mock_log:
        elevator._move_to_floor(3)
        assert elevator._direction == Direction.DOWN
        assert elevator._current_floor == 3
        assert elevator._status == 'Moving down'
        mock_log.assert_called_once_with("Elevator moving to floor %s", 3)

def test_display(elevator):
    """
    Test that display returns the correct string.
    """
    assert elevator.display() == "Floor: 0, Direction: IDLE, Status: IDLE"
```

This test suite covers all the public methods, includes edge cases (like invalid floor numbers), and uses appropriate fixtures and mocks. Each test includes a docstring explaining what it tests, and the test suite as a whole follows testing best practices.

Remember to replace `'your_module'` with the actual name of your Python module that contains the `Direction` and `ElevatorUI` classes. Also, consider additional tests for more complex scenarios.
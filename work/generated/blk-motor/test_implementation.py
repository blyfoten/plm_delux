Below are the unit tests for the given Python code using `pytest` and `unittest.mock`. These tests cover all public methods and functions, include edge cases and error conditions, use appropriate fixtures and mocks, and follow testing best practices:

```python
import pytest
import unittest.mock as mock
from threading import Lock
from your_module import ElevatorMotorControlSystem, Direction

# Mocking logging for testing purposes
@mock.patch('your_module.logging')
def test_set_speed(mock_logging):
    """
    Tests the set_speed method of the ElevatorMotorControlSystem class.
    """
    system = ElevatorMotorControlSystem()
    system.set_speed(5, Direction.UP)
    assert system.speed == 5
    assert system.direction == Direction.UP
    mock_logging.info.assert_called_once_with('Speed set to 5 with direction Direction.UP')

    # Test emergency stop condition
    system.is_emergency_stop = True
    system.set_speed(10, Direction.DOWN)
    mock_logging.error.assert_called_once_with('Cannot set speed during emergency stop')


@mock.patch('your_module.logging')
def test_emergency_stop(mock_logging):
    """
    Tests the emergency_stop method of the ElevatorMotorControlSystem class.
    """
    system = ElevatorMotorControlSystem()
    system.emergency_stop()
    assert system.is_emergency_stop == True
    assert system.speed == 0
    mock_logging.info.assert_called_once_with('Emergency stop activated')


@mock.patch('your_module.logging')
def test_get_position_feedback(mock_logging):
    """
    Tests the get_position_feedback method of the ElevatorMotorControlSystem class.
    """
    system = ElevatorMotorControlSystem()
    assert system.get_position_feedback() == 0
    mock_logging.info.assert_called_once_with('Position: 0')

    # Test emergency stop condition
    system.is_emergency_stop = True
    assert system.get_position_feedback() is None
    mock_logging.error.assert_called_once_with('Cannot get position during emergency stop')


@mock.patch('your_module.logging')
@mock.patch('your_module.time.sleep', return_value=None)  # Mock sleep for testing
def test_monitor_temperature_and_current_draw(mock_sleep, mock_logging):
    """
    Tests the monitor_temperature_and_current_draw method of the ElevatorMotorControlSystem class.
    """
    system = ElevatorMotorControlSystem()
    thread = threading.Thread(target=system.monitor_temperature_and_current_draw)
    thread.start()

    # Allow the thread to run for a short while
    time.sleep(0.1)

    # Trigger an emergency stop
    system.emergency_stop()

    # Ensure the thread has stopped
    thread.join()

    # Check that the logging messages have been called
    mock_logging.info.assert_called_with('Temperature: 0, Current draw: 0')
    mock_logging.info.assert_called_with('Emergency stop activated')
```

Please replace `your_module` with the actual module name where the `ElevatorMotorControlSystem` class and `Direction` Enum are defined. 

Note: In `test_monitor_temperature_and_current_draw`, the method runs in an infinite loop until `emergency_stop` is called. As such, we run this method in a separate thread and let it run for a short while before triggering an emergency stop to exit the loop. We then ensure that the thread has stopped before checking the logging calls. 

Also, the `time.sleep` method is mocked to prevent the test from sleeping, speeding up the execution of the test.
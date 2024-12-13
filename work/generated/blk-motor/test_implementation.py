import pytest
from unittest.mock import patch
from threading import Thread
from MotorControl import MotorControl

def test_set_speed():
    motor_control = MotorControl()
    motor_control.set_speed(5)
    assert motor_control.get_speed() == 5, "Speed should be 5"

def test_set_temperature():
    motor_control = MotorControl()
    motor_control.set_temperature(100)
    assert motor_control.get_temperature() == 100, "Temperature should be 100"

def test_set_current():
    motor_control = MotorControl()
    motor_control.set_current(10)
    assert motor_control.get_current() == 10, "Current should be 10"

def test_set_direction():
    motor_control = MotorControl()
    motor_control.set_direction(1)
    assert motor_control.get_direction() == 1, "Direction should be 1"

def test_set_position():
    motor_control = MotorControl()
    motor_control.set_position(100)
    assert motor_control.get_position() == 100, "Position should be 100"

def test_emergency_stop():
    motor_control = MotorControl()
    motor_control.emergency_stop()
    assert motor_control.stop is True, "Motor should be stopped"

@patch('MotorControl.time.sleep', return_value=None)  # to speed up test
def test_monitor(mock_sleep):
    motor_control = MotorControl()
    motor_control.set_speed(5)
    motor_control.set_temperature(100)
    motor_control.set_current(10)
    motor_control.set_direction(1)
    motor_control.set_position(100)
    with patch('MotorControl.logging.info') as mock_log:
        monitor_thread = Thread(target=motor_control.monitor)
        monitor_thread.start()
        motor_control.emergency_stop()
        monitor_thread.join()
    mock_log.assert_called_with("Motor status: Speed 5, Temperature 100, Current 10, Direction 1, Position 100")

@patch('MotorControl.time.sleep', return_value=None)  # to speed up test
def test_control(mock_sleep):
    motor_control = MotorControl()
    with patch('MotorControl.logging.error') as mock_log:
        control_thread = Thread(target=motor_control.control)
        control_thread.start()
        motor_control.emergency_stop()
        control_thread.join()
    mock_log.assert_not_called()  # since control logic is not implemented, it should not raise an exception
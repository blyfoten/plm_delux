Here is the Python code for the given requirement:

```python
import logging
import threading
import time
from enum import Enum
from typing import Optional

logging.basicConfig(level=logging.INFO)

class Direction(Enum):
    UP = 1
    DOWN = -1

class ElevatorMotorControlSystem:
    """
    Elevator motor control system for vertical movement
    """
    def __init__(self):
        self.speed = 0
        self.direction = None
        self.is_emergency_stop = False
        self.temperature = 0
        self.current_draw = 0
        self.position = 0
        self.lock = threading.Lock()

    def set_speed(self, speed: int, direction: Direction):
        """
        Set speed and direction of the motor
        """
        with self.lock:
            if self.is_emergency_stop:
                logging.error("Cannot set speed during emergency stop")
                return
            self.speed = speed
            self.direction = direction
            logging.info(f"Speed set to {self.speed} with direction {self.direction}")

    def monitor_temperature_and_current_draw(self):
        """
        Monitor temperature and current draw of the motor
        """
        while True:
            with self.lock:
                if self.is_emergency_stop:
                    break
                # Check temperature and current draw from motor's sensors
                # TODO: Integrate with actual sensor data
                self.temperature = 0
                self.current_draw = 0
                logging.info(f"Temperature: {self.temperature}, Current draw: {self.current_draw}")
                time.sleep(1)

    def emergency_stop(self):
        """
        Stop the motor in case of emergency
        """
        with self.lock:
            self.is_emergency_stop = True
            self.speed = 0
            logging.info("Emergency stop activated")

    def get_position_feedback(self) -> Optional[int]:
        """
        Get the position feedback for accurate floor leveling
        """
        with self.lock:
            if self.is_emergency_stop:
                logging.error("Cannot get position during emergency stop")
                return None
            # Get position from motor's sensor
            # TODO: Integrate with actual sensor data
            self.position = 0
            logging.info(f"Position: {self.position}")
            return self.position

def test_ElevatorMotorControlSystem():
    # TODO: Implement test cases
    pass

if __name__ == "__main__":
    test_ElevatorMotorControlSystem()
```

This code assumes that the temperature, current draw, and position are obtained from some type of sensor data which is not included in the code. The `monitor_temperature_and_current_draw` method and `get_position_feedback` method are placeholders to integrate with the actual sensor data.

The `ElevatorMotorControlSystem` class uses a threading lock to ensure thread safety. The lock is used to prevent multiple threads from accessing or changing critical pieces of data at the same time.

The `set_speed` method, `emergency_stop` method, and `get_position_feedback` method provide error recovery by checking for an emergency stop before proceeding.

Please note, this is a simulation and should not be used for real-world applications without proper hardware integration and safety checks.
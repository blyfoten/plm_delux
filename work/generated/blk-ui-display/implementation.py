import threading
import logging
from enum import Enum
from typing import List


class Direction(Enum):
    UP = 1
    DOWN = -1
    IDLE = 0


class ElevatorUI:
    def __init__(self, num_floors: int):
        self._num_floors = num_floors
        self._current_floor = 0
        self._direction = Direction.IDLE
        self._status = "IDLE"
        self._lock = threading.Lock()

    def press_floor_button(self, floor: int):
        if floor < 0 or floor >= self._num_floors:
            logging.error("Invalid floor: %s", floor)
            raise ValueError("Invalid floor")

        threading.Thread(target=self._move_to_floor, args=(floor,)).start()

    def _move_to_floor(self, floor: int):
        with self._lock:
            if floor > self._current_floor:
                self._direction = Direction.UP
            elif floor < self._current_floor:
                self._direction = Direction.DOWN
            else:
                self._direction = Direction.IDLE

            self._current_floor = floor

            if self._direction != Direction.IDLE:
                self._status = "Moving " + ("up" if self._direction == Direction.UP else "down")
            else:
                self._status = "Door Opening"

            logging.info("Elevator moving to floor %s", floor)

    def display(self) -> str:
        with self._lock:
            return f"Floor: {self._current_floor}, Direction: {self._direction.name}, Status: {self._status}"


def main():
    elevator = ElevatorUI(10)
    logging.info(elevator.display())
    elevator.press_floor_button(5)
    logging.info(elevator.display())
    elevator.press_floor_button(2)
    logging.info(elevator.display())


if __name__ == "__main__":
    main()
"""
UI Alarm (BLK-UI-ALARM)

Requirements implemented:
"""


from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum, auto

class DisplayState(Enum):
    IDLE = auto()
    MOVING_UP = auto()
    MOVING_DOWN = auto()
    DOOR_OPENING = auto()
    DOOR_CLOSING = auto()

class UiAlarm:
    def __init__(self):
        self.current_floor: int = 1
        self.state: DisplayState = DisplayState.IDLE



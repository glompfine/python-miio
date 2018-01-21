from .device import Device
import enum
from typing import Optional


class OperationMode(enum.Enum):
    Heat = 0
    Cool = 1
    Auto = 2
    Dehumidify = 3
    Ventilate = 4


class FanSpeed(enum.Enum):
    Low = 0
    Medium = 1
    High = 2
    Auto = 3


class SwingMode(enum.Enum):
    On = 0
    Off = 1


class Power(enum.Enum):
    On = 1
    Off = 0


STORAGE_SLOT_ID = 30
POWER_OFF = 'off'

DEVICE_COMMAND_PRESETS = {
    "fallback": {
        "deviceType": "generic",
        "base": "pomowiswtta0"
    },
    "0180111111": {
        "deviceType": "media_1",
        "base": "pomowiswtt02"
    },
    "0180222221": {
        "deviceType": "gree_1",
        "base": "pomowiswtt02"
    },
    "0100010727": {
        "deviceType": "gree_2",
        "base": "pomowiswtt1100190t1t205002102000t7t0190t1t207002000000t4t0",
        "off": "01011101004000205002112000D04000207002000000A0"
    },
    "0100004795": {
        "deviceType": "gree_8",
        "base": "pomowiswtt0100090900005002"
    },
    "0180333331": {
        "deviceType": "haier_1",
        "base": "pomowiswtt12"
    },
    "0180666661": {
        "deviceType": "aux_1",
        "base": "pomowiswtt12"
    },
    "0180777771": {
        "deviceType": "chigo_1",
        "base": "pomowiswtt12"
    }
}


class AirConditioningCompanionStatus:
    """Container for status reports of the Xiaomi AC Companion."""

    def __init__(self, data):
        # Device model: lumi.acpartner.v2
        #
        # Response of "get_model_and_state":
        # ['010500978022222102', '010201190280222221', '2']
        self.data = data

    @property
    def air_condition_power(self) -> str:
        """Current power state of the air conditioner."""
        return str(self.data[2])

    @property
    def air_condition_model(self) -> str:
        """Model of the air conditioner."""
        return str(self.data[0][0:2] + self.data[0][8:16])

    @property
    def power(self) -> str:
        """Current power state."""
        return 'on' if (self.data[1][2:3] == '1') else 'off'

    @property
    def is_on(self) -> bool:
        """True if the device is turned on."""
        return self.power == 'on'

    @property
    def temperature(self) -> int:
        """Current temperature."""
        return int(self.data[1][6:8], 16)

    @property
    def swing_mode(self) -> bool:
        """True if swing mode is enabled."""
        return self.data[1][5:6] == '0'

    @property
    def fan_speed(self) -> Optional[FanSpeed]:
        """Current fan speed."""
        speed = int(self.data[1][4:5])
        if speed is not None:
            return FanSpeed(speed)

        return None

    @property
    def mode(self) -> Optional[OperationMode]:
        """Current operation mode."""
        mode = int(self.data[1][3:4])
        if mode is not None:
            return OperationMode(mode)

        return None


class AirConditioningCompanion(Device):
    """Main class representing Xiaomi Air Conditioning Companion."""

    def status(self) -> AirConditioningCompanionStatus:
        """Return device status."""
        status = self.send("get_model_and_state", [])
        return AirConditioningCompanionStatus(status)

    def learn(self):
        """Learn an infrared command."""
        return self.send("start_ir_learn", [STORAGE_SLOT_ID])

    def learn_result(self):
        """Read the learned command."""
        return self.send("get_ir_learn_result", [])

    def learn_stop(self):
        """Stop learning of a infrared command."""
        return self.send("end_ir_learn", [STORAGE_SLOT_ID])

    def send_ir_code(self, command: str):
        """Play a captured command.

        :param str command: Command to execute"""
        return self.send("send_ir_code", [str(command)])

    def send_command(self, command: str):
        """Send a command to the air conditioner.

        :param str command: Command to execute"""
        return self.send("send_cmd", [str(command)])

    def send_configuration(self, model: str, power: Power,
                           operation_mode: OperationMode,
                           target_temperature: float, fan_speed: FanSpeed,
                           swing_mode: SwingMode):

        # Static turn off command available?
        if (power == False) and (model in DEVICE_COMMAND_PRESETS) and \
                (POWER_OFF in DEVICE_COMMAND_PRESETS[model]):
            return self.send_command(
                model + DEVICE_COMMAND_PRESETS[model][POWER_OFF])

        if model in DEVICE_COMMAND_PRESETS:
            configuration = model + DEVICE_COMMAND_PRESETS[model]['base']
        else:
            configuration = model + DEVICE_COMMAND_PRESETS['fallback']['base']

        configuration = configuration.replace('po', power.value)
        configuration = configuration.replace('mo', operation_mode.value)
        configuration = configuration.replace('wi', fan_speed.value)
        configuration = configuration.replace('sw', swing_mode.value)
        configuration = configuration.replace('tt', hex(int(target_temperature))[2:])

        temperature = (1 + int(target_temperature) - 17) % 16
        temperature = hex(temperature)[2:].upper()
        configuration = configuration.replace('t1t', temperature)

        temperature = (4 + int(target_temperature) - 17) % 16
        temperature = hex(temperature)[2:].upper()
        configuration = configuration.replace('t4t', temperature)

        temperature = (7 + int(target_temperature) - 17) % 16
        temperature = hex(temperature)[2:].upper()
        configuration = configuration.replace('t7t', temperature)

        return self.send_command(configuration)
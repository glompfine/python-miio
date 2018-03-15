from unittest import TestCase
from miio import Plug
from miio.plug import PlugStatus
from .dummies import DummyDevice
import pytest


class DummyPlug(DummyDevice, Plug):
    def __init__(self, *args, **kwargs):
        self.state = {
            'power': 'on',
            'temperature': 32,
        }
        self.return_values = {
            'get_prop': self._get_state,
            'set_power': lambda x: self._set_state("power", x),
        }
        super().__init__(args, kwargs)


@pytest.fixture(scope="class")
def plug(request):
    request.cls.device = DummyPlug()
    # TODO add ability to test on a real device


@pytest.mark.usefixtures("plug")
class TestPlug(TestCase):
    def is_on(self):
        return self.device.status().is_on

    def state(self):
        return self.device.status()

    def test_on(self):
        self.device.off()  # ensure off
        assert self.is_on() is False

        self.device.on()
        assert self.is_on() is True

    def test_off(self):
        self.device.on()  # ensure on
        assert self.is_on() is True

        self.device.off()
        assert self.is_on() is False

    def test_status(self):
        self.device._reset_state()

        assert repr(self.state()) == repr(PlugStatus(self.device.start_state))

        assert self.is_on() is True
        assert self.state().temperature == self.device.start_state["temperature"]

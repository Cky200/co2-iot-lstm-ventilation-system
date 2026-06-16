from gpiozero import OutputDevice

from src.utils.logger import get_logger

logger = get_logger(__name__)

class VentilationController:
    """
    Controls the ventilation system (e.g., fan) via a GPIO relay module.
    """
    def __init__(self, pin: int, active_high: bool = True):
        """
        Initialize the relay control.
        Some relay modules are active low, so active_high can be set to False.
        """
        try:
            self.relay = OutputDevice(pin, active_high=active_high, initial_value=False)
            self._is_on = False
            logger.info(f"VentilationController initialized on GPIO {pin}.")
        except Exception as e:
            logger.error(f"Failed to initialize VentilationController on GPIO {pin}: {e}")
            raise

    def turn_on(self):
        """Turn on the ventilation."""
        if not self._is_on:
            try:
                self.relay.on()
                self._is_on = True
                logger.info("Ventilation turned ON.")
            except Exception as e:
                logger.error(f"Failed to turn ON ventilation: {e}")

    def turn_off(self):
        """Turn off the ventilation."""
        if self._is_on:
            try:
                self.relay.off()
                self._is_on = False
                logger.info("Ventilation turned OFF.")
            except Exception as e:
                logger.error(f"Failed to turn OFF ventilation: {e}")

    @property
    def is_on(self) -> bool:
        """Returns the current state of the ventilation system."""
        return self._is_on

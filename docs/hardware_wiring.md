# Hardware Wiring Guide

This guide covers wiring the MQ-135 sensor, MCP3008 ADC, and a 5V Relay module to the Raspberry Pi.

## Components Needed
- Raspberry Pi (3, 4, or 5)
- MQ-135 Gas Sensor
- MCP3008 Analog-to-Digital Converter
- 5V Relay Module (1-channel)
- Breadboard & Jumper Wires

## MCP3008 to Raspberry Pi (SPI Interface)
Enable SPI on your Raspberry Pi using `sudo raspi-config` before wiring.

| MCP3008 Pin | Name    | Raspberry Pi Pin       |
|-------------|---------|------------------------|
| 16          | VDD     | 3.3V (Pin 1)           |
| 15          | VREF    | 3.3V (Pin 1)           |
| 14          | AGND    | Ground                 |
| 13          | CLK     | GPIO 11 / SCLK (Pin 23)|
| 12          | DOUT    | GPIO 9 / MISO (Pin 21) |
| 11          | DIN     | GPIO 10 / MOSI (Pin 19)|
| 10          | CS/SHDN | GPIO 8 / CE0 (Pin 24)  |
| 9           | DGND    | Ground                 |

## MQ-135 Sensor to MCP3008
| MQ-135 Pin | Connection                    |
|------------|-------------------------------|
| VCC        | 5V (Pin 2 or 4 on Pi)         |
| GND        | Ground                        |
| A0 (Analog)| MCP3008 CH0 (Pin 1)           |
| D0 (Digital)| Not Used                     |

> [!WARNING]
> The MQ-135 operates at 5V. The analog output (A0) maxes out near 5V, but the MCP3008 is powered by 3.3V. For safety, you should use a voltage divider (e.g., 2kΩ and 3.3kΩ resistors) between MQ-135 A0 and MCP3008 CH0 to step down the 5V signal to a safe ~3.3V.

## Relay Module to Raspberry Pi
This relay controls the ventilation fan.

| Relay Pin | Connection            |
|-----------|-----------------------|
| VCC       | 5V (Pin 2 or 4 on Pi) |
| GND       | Ground                |
| IN        | GPIO 17 (Pin 11)      |

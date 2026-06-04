# Environment Setup Guide

Follow these steps to configure your Raspberry Pi.

## 1. Operating System
Ensure you are running a recent version of Raspberry Pi OS (formerly Raspbian) based on Debian Bullseye or Bookworm.

## 2. Enable Hardware Interfaces
You must enable the SPI interface for the MCP3008 ADC.
```bash
sudo raspi-config
```
Navigate to **Interface Options** -> **SPI** and select **Yes** to enable it.
Reboot your Raspberry Pi if prompted.

## 3. System Dependencies
Update your package list and install necessary system tools:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv i2c-tools spi-tools
```

## 4. Virtual Environment (Recommended)
Create and activate a Python virtual environment to isolate project dependencies.
```bash
cd iot-co2-hardware-setup
python3 -m venv venv
source venv/bin/activate
```

## 5. Install Python Dependencies
Install the required Python packages from the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

## 6. Verify SPI
To check if SPI is active, run:
```bash
ls /dev/spi*
```
You should see `/dev/spidev0.0` listed.

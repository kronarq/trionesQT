# Project Analysis: TrionesQT

TrionesQT is a PyQt6 application that provides a GUI for controlling Triones RGB lights using the `trionesControl` library. The project currently consists of one main Python script (`trionesQT.py`), a Qt Designer UI file (`mainwindow.ui`), and basic documentation in `README.md` and `TODO.md`.

## Structure

- `trionesQT.py` implements the application logic. It defines a `MainWindow` class derived from the Qt designer file, manages a list of Bluetooth light addresses, and allows users to connect, control power, and change colors on one or more lights.
- `mainwindow.ui` defines the Qt widgets used for the interface. It includes controls for listing devices, buttons to manage connections, and a color picker widget.
- `README.md` gives installation and usage instructions, while `TODO.md` lists planned improvements.

## Key Features

- Add/remove multiple lights by Bluetooth MAC address.
- Connect to all configured lights simultaneously.
- Power lights on and off and change their RGB color.
- Persist the device list to a local JSON file (`data.json`).

## Potential Improvements

- **Input validation**: Ensure MAC addresses entered by the user are correctly formatted.
- **Device model**: The TODO list suggests introducing a more robust model to represent lights, which would also help with individual control.
- **Bluetooth scanning**: Integration of a device scanner would simplify adding new lights.
- **Error handling**: Expand error handling for connection and color commands to provide more informative feedback.
- **Dependency update**: The TODO file mentions migrating to the `trionesDevice` package for improved device management.

## Summary

The project is a minimal yet functional PyQt6 interface for controlling Triones lights. Future work could focus on enhancing the device model, improving user experience, and adding features such as Bluetooth scanning.

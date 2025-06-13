#!/usr/bin/env python3
import sys
import re
from dataclasses import dataclass
import serde
import serde.json as serde_json
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtWidgets import QStyle, QMessageBox
from PyQt6.QtCore import Qt
import trionesControl.trionesControl as tc

# Accept colon- or hyphen-separated MAC addresses or 12 hex digits without
# separators.
MAC_RE = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$|^[0-9A-Fa-f]{12}$"
)


qt_creator_file = "mainwindow.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file)
tick = QStyle.StandardPixmap.SP_DialogNoButton


@serde.serialize
@serde.deserialize
@dataclass
class Device:
    """Represent a single Triones light."""

    address: str
    # Connection objects cannot be serialized so skip them.
    connection: object | None = serde.field(default=None, skip=True)

    @property
    def connected(self) -> bool:
        return self.connection is not None

    def connect(self) -> bool:
        if not self.connected:
            self.connection = tc.connect(self.address, False)
        return self.connected

    def disconnect(self):
        if self.connected:
            tc.disconnect(self.connection)
            self.connection = None

    def power_on(self):
        if self.connected:
            tc.powerOn(self.connection)

    def power_off(self):
        if self.connected:
            tc.powerOff(self.connection)

    def set_color(self, r: int, g: int, b: int):
        if self.connected:
            tc.setRGB(r, g, b, self.connection)


class DevModel(QtCore.QAbstractListModel):
    def __init__(self, *args, devices=None, connectedIcon=None, disconnectedIcon=None, **kwargs):
        super(DevModel, self).__init__(*args, **kwargs)
        self.devices = devices or []
        self.connectedIcon = connectedIcon
        self.disconnectedIcon = disconnectedIcon

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.devices[index.row()].address

        if role == Qt.ItemDataRole.DecorationRole:
            device = self.devices[index.row()]
            return self.connectedIcon if device.connected else self.disconnectedIcon



    def rowCount(self, index):
        return len(self.devices)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.connectedIcon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton)
        self.disconnectedIcon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogNoButton)
        self.model = DevModel(connectedIcon=self.connectedIcon,
                              disconnectedIcon=self.disconnectedIcon)
        self.load()
        self.deviceView.setModel(self.model)
        self.addButton.pressed.connect(self.add)
        self.deleteButton.pressed.connect(self.delete)
        self.connectButton.pressed.connect(self.connect)
        self.disconnectButton.pressed.connect(self.disconnect)
        self.onButton.pressed.connect(self.turnOn)
        self.offButton.pressed.connect(self.turnOff)
        self.changeColorButton.pressed.connect(self.chooseColor)

    def validateMac(self, address: str) -> bool:
        """Return True if *address* looks like a valid MAC address."""
        return bool(MAC_RE.match(address.strip()))

    def add(self):
        """
        Add an item to our devices list, getting the text from the QLineEdit .deviceEdit
        and then clearing it.
        """
        text = self.deviceEdit.text()
        if not text:
            return
        if not self.validateMac(text):
            self.mainLog.append(f"Invalid MAC address: {text}")
            self.deviceEdit.setText("")
            return
        # Access the list via the model.
        self.model.devices.append(Device(text))
        # Trigger refresh.
        self.model.layoutChanged.emit()
        # Empty the input
        self.deviceEdit.setText("")
        self.save()
        
    def delete(self):
        indexes = self.deviceView.selectedIndexes()
        if indexes:
            # Indexes is a list of a single item in single-select mode.
            index = indexes[0]
            # Remove the item and refresh.
            del self.model.devices[index.row()]
            self.model.layoutChanged.emit()
            # Clear the selection (as it is no longer valid).
            self.deviceView.clearSelection()
            self.save()
    
    def load(self):
        self.mainLog.append("Loading data")
        try:
            with open('data.json', 'r') as f:
                data = f.read()
                self.model.devices = serde_json.from_json(list[Device], data)
        except Exception:
            self.mainLog.append("Failed to load data")
            pass

    def save(self):
        with open('data.json', 'w') as f:
            f.write(serde_json.to_json(self.model.devices, indent=2))

    def connect(self):
        for device in self.model.devices:
            if device.connected:
                continue
            self.mainLog.append("Connecting to " + device.address)
            if not device.connect():
                self.mainLog.append("Failed to connect to the light " + device.address)
                continue
            self.updateStatus(device.address)
            self.mainLog.append("Connected to " + device.address)

    def disconnect(self):
        for device in self.model.devices:
            if not device.connected:
                continue
            self.mainLog.append("Disconnecting from " + device.address)
            try:
                device.disconnect()
            except Exception:
                self.mainLog.append("Failed to disconnect from " + device.address)
            self.updateStatus(device.address)

    def turnOn(self):
        for device in self.model.devices:
            if device.connected:
                self.mainLog.append("Turning on " + device.address)
                try:
                    device.power_on()
                except Exception:
                    self.mainLog.append("Failed to turn on " + device.address)

    def turnOff(self):
        for device in self.model.devices:
            if device.connected:
                self.mainLog.append("Turning off " + device.address)
                try:
                    device.power_off()
                except Exception:
                    self.mainLog.append("Failed to turn off " + device.address)

    def changeColor(self):
        for device in self.model.devices:
            if device.connected:
                self.mainLog.append("Changing color on " + device.address)
                device.set_color(255, 0, 0)

    def chooseColor(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.colorWidget.setStyleSheet("QWidget { background-color: %s }" % color.name())
            self.colorWidget.color = color
            self.colorWidget.update()
            for device in self.model.devices:
                if device.connected:
                    self.mainLog.append("Changing color on " + device.address)
                    device.set_color(color.red(), color.green(), color.blue())

    def updateStatus(self, address):
        for i, device in enumerate(self.model.devices):
            if device.address == address:
                index = self.model.index(i)
                self.model.dataChanged.emit(index, index)
                self.save()
                break

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QMessageBox.question(self, 'Message', quit_msg, QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.disconnect()
            except Exception:
                self.mainLog.append("Failed to disconnect from lights")
            event.accept()
        else:
            event.ignore()

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()

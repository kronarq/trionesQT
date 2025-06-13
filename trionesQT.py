#!/usr/bin/env python3
import sys
import json
import re
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


class DevModel(QtCore.QAbstractListModel):
    def __init__(self, *args, devices=None, connectedIcon=None, disconnectedIcon=None, **kwargs):
        super(DevModel, self).__init__(*args, **kwargs)
        self.devices = devices or []
        self.connectedIcon = connectedIcon
        self.disconnectedIcon = disconnectedIcon
        
    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            _, text = self.devices[index.row()]
            return text
        
        if role == Qt.ItemDataRole.DecorationRole:
            status, _ = self.devices[index.row()]
            if status:
                return self.connectedIcon
            else:
                return self.disconnectedIcon



    def rowCount(self, index):
        return len(self.devices)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.connectedIcon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton)
        self.disconnectedIcon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogNoButton)
        self.model = DevModel(connectedIcon=self.connectedIcon, disconnectedIcon=self.disconnectedIcon)
        self.connections = [];
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
        self.model.devices.append((False, text))
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
                self.model.devices = json.load(f)
        except Exception:
            self.mainLog.append("Failed to load data")
            pass

    def save(self):
        with open('data.json', 'w') as f:
            json.dump(self.model.devices, f)

    def connect(self):
        if self.connections:
            self.disconnect()
        for _, address in self.model.devices:
            self.mainLog.append("Connecting to " + address)
            light = tc.connect(address, False)
            if light is None:
                self.mainLog.append("Failed to connect to the light " + address)
                continue
            self.updateStatus(True, address)
            self.mainLog.append("Connected to " + address)
            self.connections.append(light)

    def disconnect(self):
        for light in self.connections:
            self.mainLog.append("Disconnecting from " + light._address)
            try:
                tc.disconnect(light)
            except Exception:
                self.mainLog.append("Failed to disconnect from " + light._address)
            self.updateStatus(False, light._address)
        self.connections.clear()

    def turnOn(self):
        for light in self.connections:
            self.mainLog.append("Turning on " + light._address)
            try:
                tc.powerOn(light)
            except Exception:
                self.mainLog.append("Failed to turn on " + light._address)

    def turnOff(self):
        for light in self.connections:
            self.mainLog.append("Turning off " + light._address)
            try:
                tc.powerOff(light)
            except Exception:
                self.mainLog.append("Failed to turn off " + light._address)

    def changeColor(self):
        for light in self.connections:
            self.mainLog.append("Changing color on " + light._address)
            tc.setRGB(255, 0, 0, light)

    def chooseColor(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.colorWidget.setStyleSheet("QWidget { background-color: %s }" % color.name())
            self.colorWidget.color = color
            self.colorWidget.update()
            for light in self.connections:
                self.mainLog.append("Changing color on " + light._address)
                tc.setRGB(color.red(), color.green(), color.blue(), light)

    def updateStatus(self, status, address):
        for i, (_, a) in enumerate(self.model.devices):
            if a == address:
                self.model.devices[i] = (status, address)
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
            for i, (status, address) in enumerate(self.model.devices):
                    self.model.devices[i] = (False, address)
                    index = self.model.index(i)
                    self.model.dataChanged.emit(index, index)
                    self.save()
            event.accept()
        else:
            event.ignore()

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()

# MASTER PROJECT - Milos Rasic

#region Libraries
from PyQt5.QtWidgets import QApplication, QPushButton, QLineEdit, QLabel, QWidget, QSlider, QSpinBox, QComboBox, QMainWindow
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QBrush, QIntValidator
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtWidgets
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import os
import sys
import re
import threading
import time
import serial
from random import randint
import csv
#endregion

#region Variables
arduino_data = ''
#arduino = serial.Serial("COM3", 115200)
comm_port = serial.Serial()
sr_ecg  = 0
last_ecg = 0
sr_time = 0
sr_id   = 0

# Serial communication
COM_ports = []
old_ports = []
ports_found = False
connection = False
data_stream_flag = False

# Paint parameters
line_color = QColor(180, 180, 180)
line_width = 1

# Graph parameters
history_depth       = 10                # [s]       - Time in seconds of how much history depth should be shown on a graph
ppg_max_list        = 5000              # [#]       - Max number of items in a list stored for the PPG sensor - should contain at least the history_depth interval
ppg_color           = (255, 95, 31)     # [R,G,B]   - Neon Orange color for the PPG plot
aux_color           = (248, 255, 0)
aux_max_list        = 20000
bpm_color           = (77, 77, 255)
bpm_max_list        = 20000
ecg_color           = (255, 7, 58)
ecg_max_list        = 20000

# ECG variables
ecg_adc_buffer      = [] 
ecg_time_buffer     = []
ecg_id_buffer       = []
ecg_data_flag       = False
ecg_hw_active       = False
ecg_stream_active   = False
ecg_last_timestamp  = 0 

# PPG variables
ppg_ir_buffer       = [] 
ppg_time_buffer     = []
ppg_id_buffer       = []
ppg_data_flag       = False
ppg_hw_active       = False
ppg_stream_active   = False
ppg_last_timestamp  = 0
ppg_last_id         = 0

# BPM variables
bpm_adc_buffer      = []
bpm_stream_active   = False
bpm_time_buffer     = []
bpm_last_timestamp  = 0
bpm_data_flag       = False
bpm_hw_active       = False

# AUX variables
aux_adc_buffer      = []
aux_hw_active       = False
aux_stream_active   = False
aux_data_flag       = False
aux_last_timestamp  = 0
aux_time_buffer     = []

# Data recording variables
data_ecg_adc        = []
data_aux_adc        = []
data_bpm_adc        = []
data_time_ecg       = []
data_time_bpm       = []
data_time_aux       = []
data_time_ppg       = []
data_ppg            = []
recording_flag      = False
data_storing_flag   = False
dir_name            = 'Recorded_Data'

# BPM variables
bpm_active_flag     = False
data_bpm_session    = []
data_bpm_block      = []
data_bpm_single     = []
bpm_algorithms      = ['Algorithm 1', 'Algorithm 2', 'Algorithm 3']
bpm_block_id        = 1
bpm_num_meas        = 1
bpm_time            = 0
bpm_active_measure  = False
bpm_pump_status     = False
bpm_valve_status    = False
bpm_k               = 0.07688
bpm_n               = -13.16872

# Different commands
cmd_start_stream    = 'C7 1'
cmd_stop_stream     = 'C7 0'
cmd_ecg_start       = 'C6 1'
cmd_ecg_stop        = 'C6 0'
cmd_beep            = 'C10 100'
cmd_ppg_start       = 'C11 1'
cmd_ppg_stop        = 'C11 0'
cmd_aux_start       = 'C12 1'
cmd_aux_stop        = 'C12 0'
cmd_bpm_start       = 'C13 1'
cmd_bpm_stop        = 'C13 0'
cmd_pump_start      = 'C2 100'
cmd_pump_stop       = 'C2 0'
cmd_valve_start     = 'C3 100'
cmd_valve_stop      = 'C3 0'
#endregion

#region Obsolete Function
def DecodeSerialData(data):
    global sr_ecg, sr_time, sr_id
    try:
        sr_ecg  = int(data[data.find('$') + 1 : data.find(',')])
        sr_time = int(data[data.find(',') + 1 : data.find('%')])
        sr_id   = int(data[data.find('%') + 1 : data.find('#')])
    except:
        pass

def DecodeSerialData2(data):
    global sr_ecg, sr_time, sr_id
    var = 1
    new_ecg = 0
    new_time = 0
    new_id = 0
    for d in data:
        if d == '$':
            continue
        elif d == ',':
            var = 2
        elif d == '%':
            var = 3
        elif d == '#':
            continue
        else:
            if var == 1:
                new_ecg = new_ecg * 10 + int(d)
            elif var == 2:
                new_time = new_time * 10 + int(d)
            else:
                new_id = new_id * 10 + int(d)
    sr_ecg = new_ecg
    sr_time = new_time
    sr_id = new_id

def DecodeSerialData_PPG(data):
    global ppg_ir_buffer, ppg_time_buffer, ppg_id_buffer, ppg_data_flag
    var             = 0
    new_ppg_ir      = 0
    new_ppg_time    = 0
    new_ppg_id      = 0
    for d in data:
        if d == '$':
            # This is the case where we have reached the end of the message
            continue
        elif d == ',':
            # This indicates that we're changing the variable that we're parsing
            var += 1
        elif d == '#':
            # This just indicates that this is the start of the message
            continue
        else:
            if var == 1:
                # This is the PPG IR variable
                new_ppg_ir = new_ppg_ir * 10 + int(d)
            elif var == 2:
                # This is the PPG Time variable
                new_ppg_time = new_ppg_time * 10 + int(d)
            else:
                new_ppg_id = new_ppg_id * 10 + int(d)

    # When out of the loop, add those values to the end of the lists
    ppg_ir_buffer.append(new_ppg_ir)
    ppg_time_buffer.append(new_ppg_time)
    ppg_id_buffer.append(new_ppg_id)

    # Update the PPG data flag to True
    ppg_data_flag = True
#endregion

# Function for decoding the ADC message
def DecodeSerialData_ADC(data):
    global ecg_adc_buffer, ecg_time_buffer, ecg_id_buffer, ecg_data_flag, bpm_adc_buffer, aux_adc_buffer
    # Local variables
    var             = 0
    new_ecg_adc     = 0
    new_ecg_time    = 0
    new_ecg_id      = 0
    new_bpm_adc     = 0
    new_aux_adc     = 0
    # Going through the data
    for d in data:
        if d == '$':
            # This is the case where we have reached the end of the message
            continue
        elif d == ',':
            # This indicates that we're changing the variable that we're parsing
            var += 1
        elif d == '#':
            # This just indicates that this is the start of the message
            continue
        else:
            if var == 1:
                # This is the ECG ADC variable
                new_ecg_adc = new_ecg_adc * 10 + int(d)
            elif var == 2:
                # This is the BPM ADC variable
                new_bpm_adc = new_bpm_adc * 10 + int(d)
            elif var == 3:
                # This is the AUX ADC variable
                new_aux_adc = new_aux_adc * 10 + int(d)
            elif var == 4:
                new_ecg_time = new_ecg_time * 10 + int(d)
            else:
                new_ecg_id = new_ecg_id * 10 + int(d)

    # When out of the loop, add those values to the end of the lists
    ecg_adc_buffer.append(new_ecg_adc)
    ecg_time_buffer.append(new_ecg_time)
    ecg_id_buffer.append(new_ecg_id)

    # Update the ECG data flag to True
    ecg_data_flag = True

# Function for decoding the unified data Serial message
def DecodeSerialData_Unified(data):
    # Global variables
    global ecg_adc_buffer, ecg_time_buffer, ecg_id_buffer, ecg_data_flag, bpm_adc_buffer, aux_adc_buffer, ppg_ir_buffer, ppg_time_buffer, ppg_id_buffer, ppg_data_flag, ppg_last_id, aux_data_flag, aux_time_buffer, bpm_adc_buffer, bpm_time_buffer, bpm_data_flag
    global bpm_k, bpm_n
    # Local variables
    var             = 0
    new_ecg_adc     = 0
    new_ecg_time    = 0
    new_ecg_id      = 0
    new_bpm_adc     = 0
    new_aux_adc     = 0
    new_ppg_ir      = 0
    new_ppg_time    = 0
    new_ppg_id      = 0
    new_ppg_flag    = 0

    # Going through the data
    for d in data:
        if d == '$':
            # This is the case where we have reached the end of the message
            continue
        elif d == ',':
            # This indicates that we're changing the variable that we're parsing
            var += 1
        elif d == '#':
            # This just indicates that this is the start of the message
            continue
        else:
            if var == 1:
                # This is the ECG ADC variable
                new_ecg_adc = new_ecg_adc * 10 + int(d)
            elif var == 2:
                # This is the BPM ADC variable
                new_bpm_adc = new_bpm_adc * 10 + int(d)
            elif var == 3:
                # This is the AUX ADC variable
                new_aux_adc = new_aux_adc * 10 + int(d)
            elif var == 4:
                # This is the ADC read time in ms
                new_ecg_time = new_ecg_time * 10 + int(d)
            elif var == 5:
                # This is the ADC ID
                new_ecg_id = new_ecg_id * 10 + int(d)
            elif var == 6:
                # This is the PPG IR value
                new_ppg_ir = new_ppg_ir * 10 + int(d)
            elif var == 7:
                # This is the PPG time reading
                new_ppg_time = new_ppg_time * 10 + int(d)
            elif var == 8:
                # This is the PPG ID reading
                new_ppg_id = new_ppg_id * 10 + int(d)
            else:
                new_ppg_flag = int(d)
    #print(new_ecg_id)
    # Check whether we have a new PPG message as well
    if new_ppg_id > ppg_last_id:
        #print('New PPG message')
        # Update the flag
        ppg_data_flag = True
        # Update the last ID
        ppg_last_id = new_ppg_id
        # Add the values to the arrays
        ppg_ir_buffer.append(new_ppg_ir)
        ppg_time_buffer.append(new_ppg_time)
        ppg_id_buffer.append(new_ppg_id)

    # When out of the loop, add those values to the end of the lists
    # ECG
    ecg_adc_buffer.append(new_ecg_adc)
    ecg_time_buffer.append(new_ecg_time)
    ecg_id_buffer.append(new_ecg_id)
    # AUX
    aux_adc_buffer.append(new_aux_adc)
    aux_time_buffer.append(new_ecg_time)
    # BPM
    bpm_adc_buffer.append(bpm_k * new_bpm_adc + bpm_n)
    bpm_time_buffer.append(new_ecg_time)

    # Update the ECG data flag to True
    ecg_data_flag = True

    # Update the AUX data flag to True
    aux_data_flag = True

    # Update the BPM data flag to True
    bpm_data_flag = True

# Function for unpacking the data
def UnpackDataSingle(array1):
    # array1 and array2 need to have the same length
    arr1 = []
    # Go through all of the sublists
    for i  in range(0, len(array1)):
        try:
            arr1 += array1[i]
        except:
            print('Error in unpacking data')
    # Return arr1 and arr2 as elements of an array
    return arr1

# Function for unpacking the data
def UnpackData(array1, array2):
    # array1 and array2 need to have the same length
    arr1 = []
    arr2 = []
    # Go through all of the sublists
    for i  in range(0, len(array1)):
        try:
            arr1 += array1[i]
            arr2 += array2[i]
        except:
            print('Error in unpacking data')
    # Return arr1 and arr2 as elements of an array
    return [arr1, arr2]

# Function for storing all of the recorded data
def StoreData(file_name):
    # Since there can be different amounts od data points for each of the measurements, and each measurement comes with its own timestamp, the data will be saved in separate blocks
    # CSV File data structure
    # ECG - ECG TIME - BPM - BPM TIME - AUX - AUX TIME - PPG - PPG TIME
    global data_storing_flag, data_aux_adc, data_bpm_adc, data_ecg_adc, data_ppg, data_time_aux, data_time_bpm, data_time_ecg, data_time_ppg, dir_name, bpm_active_flag, data_bpm_session
    print('Recording has ended, starting the data storing process.')
    # Variable for storing the file path of the data file
    data_file_path = ''
    # Change the data_storing_flag to True so the data can't be overwriten while trying to store it
    data_storing_flag = True

    # First check whether the folder for storing data exists
    if os.path.exists(os.getcwd() + '/' + dir_name) == False:
        print('The ' + dir_name + 'does not exist, creating it now.')
        os.mkdir(os.getcwd() + '/' + dir_name)
        print('Directory created, all future data recordings will be saved in this directory.')

    # Check to see whether the typed filename is available, if not, keep adding number to the desired filename in _X fashion until an available name has been reached
    print('Creating the data storing file.')
    if os.path.isfile(os.getcwd() + '/' + dir_name + '/' + file_name + '.csv') == False:
        # This is the case where this file does not exist
        data_file_path = os.getcwd() + '/' + dir_name + '/' + file_name + '.csv'
    else:
        # This is the case where this file already exists, and we need to create versions that have _X after the name
        file_counter = 1
        file_found = False
        # Iterate until an available filename has been found
        while file_found == False:
            if os.path.isfile(os.getcwd() + '/' + dir_name + '/' + file_name + '_' + str(file_counter) + '.csv') == True:
                # Increase the file counter in every loop
                file_counter += 1
            else:
                # This is the case where we have found the file name
                file_found = True
        data_file_path = os.getcwd() + '/' + dir_name + '/' + file_name + '_' + str(file_counter) + '.csv'

    # Data is stored as an array of arrays, first unpack it into only an array
    print('Unpacking the data.')
    # Unpacking ECG data
    [data_ecg_adc, data_time_ecg]   = UnpackData(data_ecg_adc, data_time_ecg)
    # Unpacking BPM data
    [data_bpm_adc, data_time_bpm]   = UnpackData(data_bpm_adc, data_time_bpm)
    # Unpacking AUX data
    [data_aux_adc, data_time_aux]   = UnpackData(data_aux_adc, data_time_aux)
    # Unpacking PPG data
    [data_ppg, data_time_ppg]       = UnpackData(data_ppg, data_time_ppg)

    # If there was an active BPM during the recording session, unpack and add that data as well
    data_bpm_session                = UnpackDataSingle(data_bpm_session)

    # Write data to the file in the next order
    # ECG -> BPM -> AUX -> PPG
    with open(data_file_path, 'w', newline = '') as data_file:

        # Create csv writer
        writer = csv.writer(data_file)

        # Empty header row variable
        header_row = []

        # Depending on if there were BPMs during this recording session, add an additonal row
        if bpm_active_flag == True:
            # This is the case where there was at leasy one BPM during the recording session
            header_row = ['ECG_VALUE', 'ECG_TIME', 'BPM_VALUE', 'BPM_TIME', 'AUX_VALUE', 'AUX_TIME', 'PPG_VALUE', 'PPG_TIME', 'BPM']
        else:
            # This is the case where there were no BPMs during the recording session
            # Writing the header row
            header_row = ['ECG_VALUE', 'ECG_TIME', 'BPM_VALUE', 'BPM_TIME', 'AUX_VALUE', 'AUX_TIME', 'PPG_VALUE', 'PPG_TIME']

        # Write the header row
        writer.writerow(header_row)

        # Find the max length between all of the different arrays that need to be stored
        max_length = max(len(data_ecg_adc), len(data_bpm_adc), len(data_aux_adc), len(data_ppg))

        # Go through all arrays in order appenind the data, if the index is larger than the length, append blank
        for i in range(0, max_length):
            # Variable for storing the current row
            row = []

            # ECG value and time
            if i < len(data_ecg_adc):
                # Append Data
                row.append(str(data_ecg_adc[i]))
                row.append(str(data_time_ecg[i]))
            else:
                # Append blank spaces
                row.append('')
                row.append('')

            # BPM value and time
            if i < len(data_bpm_adc):
                # Append Data
                row.append(str(data_bpm_adc[i]))
                row.append(str(data_time_bpm[i]))
            else:
                # Append blank spaces
                row.append('')
                row.append('')

            # AUX value and time
            if i < len(data_aux_adc):
                # Append Data
                row.append(str(data_aux_adc[i]))
                row.append(str(data_time_aux[i]))
            else:
                # Append blank spaces
                row.append('')
                row.append('')

            # PPG value and time
            if i < len(data_ppg):
                # Append Data
                row.append(str(data_ppg[i]))
                row.append(str(data_time_ppg[i]))
            else:
                # Append blank spaces
                row.append('')
                row.append('')

            # If a BPM was active, add an empty column at the end
            if i < len(data_bpm_session):
                # Append the next value from the BPM array
                row.append(str(data_bpm_session[i]))
            else:
                # Append a blank space
                row.append('')

            # After appending all of that data, write the whole row and go through the loop
            writer.writerow(row)

    # Reset the data storing flag to Falae
    print('Finished saving the data to the CSV file.')
    data_storing_flag = False

# Function for finding all of the available COM ports
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    global COM_ports
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    COM_ports = result
    return result

# All GUI elements
class App(QWidget):
    
    # Init
    def __init__(self):       
        super().__init__()
        self.title = 'Heart Analyzer'
        self.left = 200
        self.top = 200
        self.width = 2560
        self.height = 1440
        self.qTimer = QTimer()
        self.qTimer.setInterval(10)    
        self.qTimer.timeout.connect(self.updateEvent)
        self.qTimer.timeout.connect(self.update_ppg_graph)
        self.qTimer.timeout.connect(self.update_ecg_graph)
        self.qTimer.timeout.connect(self.update_aux_graph)
        self.qTimer.timeout.connect(self.update_bpm_graph)
        self.qTimer.start()
        self.initUI()
        
    # InitUI Function
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(25, 25, 25))
        self.setPalette(p)        
    
        #region   TITLE

        # Title Label
        self.label_title = QLabel(self)
        self.label_title.setText('HEART SIGNAL MONITOR')
        self.label_title.setGeometry(35, 20, 600, 80)
        self.label_title.setFont(QFont('Arial', 36))
        self.label_title.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')
        #endregion
        
        #region   SERIAL CONNECTION

        # Serial Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Serial Connection')
        self.label_serial.setGeometry(20, 80, 250, 80)
        self.label_serial.setFont(QFont('Arial', 20))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # COM Port Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('COM Port:')
        self.label_serial.setGeometry(20, 120, 250, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # COM Port ComboBox
        self.Com_port = QComboBox(self)
        self.Com_port.addItems(COM_ports)
        self.Com_port.setGeometry(105, 145, 100, 30)
        self.Com_port.setFont(QFont("Arial", 12))
        self.Com_port.setStyleSheet("QComboBox {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150)}")

        # Baudrate Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Baudrate:')
        self.label_serial.setGeometry(20, 160, 250, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Baudrate ComboBox
        self.baudrate_cb = QComboBox(self)
        self.baudrate_cb.addItems(['9600', '19200', '38400', '57600', '74880', '115200', '230400', '250000'])
        self.baudrate_cb.setGeometry(105, 185, 100, 30)
        self.baudrate_cb.setFont(QFont("Arial", 12))
        self.baudrate_cb.setStyleSheet("QComboBox {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150)}")

        # Baudrate Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Press Button to Connect to Hardware:')
        self.label_serial.setGeometry(240, 120, 300, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Start Connection BUTTON
        self.buttonConnect = QPushButton("CONNECT", self)
        self.buttonConnect.resize(110, 30)
        self.buttonConnect.move(530, 145)
        self.buttonConnect.clicked.connect(self.buttonConnectFunction)
        self.buttonConnect.setFont(QFont("Arial", 12))
        self.buttonConnect.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # Status Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Connection Status:')
        self.label_serial.setGeometry(240, 160, 300, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Stop Connection BUTTON
        self.buttonStopConn = QPushButton("STOP", self)
        self.buttonStopConn.resize(110, 30)
        self.buttonStopConn.move(530, 185)
        self.buttonStopConn.clicked.connect(self.buttonDisconnectFunction)
        self.buttonStopConn.setFont(QFont("Arial", 12))
        self.buttonStopConn.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # Status Label
        self.label_con_status = QLabel(self)
        self.label_con_status.setText('DISCONNECTED')
        self.label_con_status.setGeometry(380, 160, 130, 80)
        self.label_con_status.setFont(QFont('Arial', 12))
        self.label_con_status.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
        #endregion
        
        #region   DATA STREAM
        
        # Data Stream Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Data Stream')
        self.label_serial.setGeometry(20, 210, 250, 80)
        self.label_serial.setFont(QFont('Arial', 20))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Data Stream Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Press Button to Enable or Disable the Data Stream:')
        self.label_serial.setGeometry(20, 250, 355, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Data Stream Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Data Stream Status:')
        self.label_serial.setGeometry(20, 290, 355, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Start DataStream BUTTON
        self.buttonData = QPushButton("ENABLE", self)
        self.buttonData.resize(110, 30)
        self.buttonData.move(400, 275)
        self.buttonData.clicked.connect(self.buttonDataFunction)
        self.buttonData.setFont(QFont("Arial", 12))
        self.buttonData.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # Stop DataStream BUTTON
        self.buttonDataStop = QPushButton("DISABLE", self)
        self.buttonDataStop.resize(110, 30)
        self.buttonDataStop.move(530, 275)
        self.buttonDataStop.clicked.connect(self.buttonDataStopFunction)
        self.buttonDataStop.setFont(QFont("Arial", 12))
        self.buttonDataStop.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # Data Stream Label ENABLE/DISABLE
        self.label_stream_flag = QLabel(self)
        self.label_stream_flag.setText('DISABLED')
        self.label_stream_flag.setGeometry(170, 290, 150, 80)
        self.label_stream_flag.setFont(QFont('Arial', 12))
        self.label_stream_flag.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
        #endregion

        #region Record Data

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Record Data')
        self.label_serial.setGeometry(20, 330, 250, 80)
        self.label_serial.setFont(QFont('Arial', 20))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Enter the file name for the recorded data:')
        self.label_serial.setGeometry(20, 370, 300, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Record Data File Name Textbox
        self.record_file_name = QLineEdit(self)
        self.record_file_name.move(320, 390)
        self.record_file_name.resize(275, 30)
        self.record_file_name.setStyleSheet("""QLineEdit { background-color: rgb(25, 25, 25); color: rgb(150, 150, 150) }""")
        self.record_file_name.setFont(QFont('Arial', 12))

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('.CSV')
        self.label_serial.setGeometry(600, 370, 50, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Press Button to Enable or Disable the Recording:')
        self.label_serial.setGeometry(20, 410, 350, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Start Recording BUTTON
        self.buttonRecordStart = QPushButton("ENABLE", self)
        self.buttonRecordStart.resize(110, 30)
        self.buttonRecordStart.move(400, 435)
        self.buttonRecordStart.clicked.connect(self.buttonStartRecordingFunction)
        self.buttonRecordStart.setFont(QFont("Arial", 12))
        self.buttonRecordStart.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # Stop Recording BUTTON
        self.buttonRecordStop = QPushButton("DISABLE", self)
        self.buttonRecordStop.resize(110, 30)
        self.buttonRecordStop.move(530, 435)
        self.buttonRecordStop.clicked.connect(self.buttonStopRecordingFunction)
        self.buttonRecordStop.setFont(QFont("Arial", 12))
        self.buttonRecordStop.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # Data Stream Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Data Recording Status:')
        self.label_serial.setGeometry(20, 450, 250, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Data Stream Label ENABLE/DISABLE
        self.label_record_flag = QLabel(self)
        self.label_record_flag.setText('NOT RECORDING')
        self.label_record_flag.setGeometry(190, 450, 150, 80)
        self.label_record_flag.setFont(QFont('Arial', 12))
        self.label_record_flag.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        #endregion

        #region Blood Preasure Measurement

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Blood Pressure Measurement')
        self.label_serial.setGeometry(20, 825, 370, 80)
        self.label_serial.setFont(QFont('Arial', 20))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Number of consecutive measurements:')
        self.label_serial.setGeometry(20, 865, 300, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Consecutive Measurements Number LineEdit
        self.bpm_num_measurements = QLineEdit(self)
        range_num_meas = QIntValidator()
        range_num_meas.setRange(1, 5)
        self.bpm_num_measurements.setValidator(range_num_meas)
        self.bpm_num_measurements.move(300, 890)
        self.bpm_num_measurements.resize(50, 30)
        self.bpm_num_measurements.setStyleSheet("""QLineEdit { background-color: rgb(25, 25, 25); color: rgb(150, 150, 150) }""")
        self.bpm_num_measurements.setFont(QFont('Arial', 12))
        self.bpm_num_measurements.setText('1')

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Time between measurements:')
        self.label_serial.setGeometry(20, 905, 300, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Consecutive Measurements Number LineEdit
        self.bpm_time = QLineEdit(self)
        range_bpm_time = QIntValidator()
        range_bpm_time.setRange(0, 600)
        self.bpm_time.setValidator(range_bpm_time)
        self.bpm_time.move(235, 930)
        self.bpm_time.resize(50, 30)
        self.bpm_time.setStyleSheet("""QLineEdit { background-color: rgb(25, 25, 25); color: rgb(150, 150, 150) }""")
        self.bpm_time.setFont(QFont('Arial', 12))
        self.bpm_time.setText('60')

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('s')
        self.label_serial.setGeometry(290, 905, 30, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('BPM Algorithm:')
        self.label_serial.setGeometry(20, 945, 300, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        global bpm_algorithms

        # BPM Algorithm ComboBox
        self.bpm_algo = QComboBox(self)
        self.bpm_algo.addItems(bpm_algorithms)
        self.bpm_algo.setGeometry(130, 970, 400, 30)
        self.bpm_algo.setFont(QFont("Arial", 12))
        self.bpm_algo.setStyleSheet("QComboBox {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150)}")

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Blood Pressure Measurement data file integration')
        self.label_serial.setGeometry(20, 985, 350, 80)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Enable BPM data file integration
        self.buttonBPM_file_EN = QPushButton("ENABLE", self)
        self.buttonBPM_file_EN.resize(110, 30)
        self.buttonBPM_file_EN.move(400, 1015)
        self.buttonBPM_file_EN.clicked.connect(self.buttonBPM_EN_DATA_fun)
        self.buttonBPM_file_EN.setFont(QFont("Arial", 12))
        self.buttonBPM_file_EN.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # Disable BPM data file integration
        self.buttonBPM_file_DIS = QPushButton("DISABLE", self)
        self.buttonBPM_file_DIS.resize(110, 30)
        self.buttonBPM_file_DIS.move(530, 1015)
        self.buttonBPM_file_DIS.clicked.connect(self.buttonBPM_DIS_DATA_fun)
        self.buttonBPM_file_DIS.setFont(QFont("Arial", 12))
        self.buttonBPM_file_DIS.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Blood Pressure Measurement data file integration status:')
        self.label_serial.setGeometry(20, 1045, 400, 40)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Data Stream Label ENABLE/DISABLE
        self.label_bpm_file_en = QLabel(self)
        self.label_bpm_file_en.setText('DISABLED')
        self.label_bpm_file_en.setGeometry(420, 1045, 150, 40)
        self.label_bpm_file_en.setFont(QFont('Arial', 12))
        self.label_bpm_file_en.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Automatic blood pressure measurement routine')
        self.label_serial.setGeometry(20, 1085, 400, 40)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Enable BPM data file integration
        self.buttonBPM_start = QPushButton("START", self)
        self.buttonBPM_start.resize(110, 30)
        self.buttonBPM_start.move(400, 1085)
        #self.buttonBPM_start.clicked.connect(self.buttonBPM_START_fun)
        self.buttonBPM_start.setFont(QFont("Arial", 12))
        self.buttonBPM_start.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # Disable BPM data file integration
        self.buttonBPM_stop = QPushButton("STOP", self)
        self.buttonBPM_stop.resize(110, 30)
        self.buttonBPM_stop.move(530, 1085)
        #self.buttonBPM_stop.clicked.connect(self.buttonBPM_STOP_fun)
        self.buttonBPM_stop.setFont(QFont("Arial", 12))
        self.buttonBPM_stop.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # Record Data Label
        self.label_serial = QLabel(self)
        self.label_serial.setText('Automatic blood pressure measurement routine status:')
        self.label_serial.setGeometry(20, 1125, 400, 40)
        self.label_serial.setFont(QFont('Arial', 12))
        self.label_serial.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # Data Stream Label ENABLE/DISABLE
        self.label_bpm_status = QLabel(self)
        self.label_bpm_status.setText('NOT RUNNING')
        self.label_bpm_status.setGeometry(420, 1125, 150, 40)
        self.label_bpm_status.setFont(QFont('Arial', 12))
        self.label_bpm_status.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        #endregion

        #region   ECG

        # ECG Label
        self.label_ecg = QLabel(self)
        self.label_ecg.setText('ECG')
        self.label_ecg.setGeometry(660, 30, 100, 20)
        self.label_ecg.setFont(QFont('Arial', 20))
        self.label_ecg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

         # ECG Hardware Label
        self.label_ecg = QLabel(self)
        self.label_ecg.setText('Hardware:')
        self.label_ecg.setGeometry(660, 70, 100, 20)
        self.label_ecg.setFont(QFont('Arial', 12))
        self.label_ecg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # ECG Hardware ON Button
        self.button_ecg_hw_on = QPushButton("ON", self)
        self.button_ecg_hw_on.resize(60, 30)
        self.button_ecg_hw_on.move(740, 65)
        self.button_ecg_hw_on.clicked.connect(self.buttonECG_HW_ON)
        self.button_ecg_hw_on.setFont(QFont("Arial", 12))
        self.button_ecg_hw_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # ECG Hardware OFF Button
        self.button_ecg_hw_off = QPushButton("OFF", self)
        self.button_ecg_hw_off.resize(60, 30)
        self.button_ecg_hw_off.move(810, 65)
        self.button_ecg_hw_off.clicked.connect(self.buttonECG_HW_OFF)
        self.button_ecg_hw_off.setFont(QFont("Arial", 12))
        self.button_ecg_hw_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # ECG Hardware Status Label
        self.label_ecg = QLabel(self)
        self.label_ecg.setText('Hardware Status:')
        self.label_ecg.setGeometry(660, 110, 200, 20)
        self.label_ecg.setFont(QFont('Arial', 12))
        self.label_ecg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # ECG Hardware Status Label ON/OFF
        self.label_ecg_hw = QLabel(self)
        self.label_ecg_hw.setText('OFF')
        self.label_ecg_hw.setGeometry(790, 110, 200, 20)
        self.label_ecg_hw.setFont(QFont('Arial', 12))
        self.label_ecg_hw.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        # ECG Stream Label
        self.label_ecg = QLabel(self)
        self.label_ecg.setText('Stream:')
        self.label_ecg.setGeometry(660, 150, 200, 20)
        self.label_ecg.setFont(QFont('Arial', 12))
        self.label_ecg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # ECG Stream ON Button
        self.button_ecg_stream_on = QPushButton("ON", self)
        self.button_ecg_stream_on.resize(60, 30)
        self.button_ecg_stream_on.move(740, 145)
        self.button_ecg_stream_on.clicked.connect(self.buttonECG_STR_ON)
        self.button_ecg_stream_on.setFont(QFont("Arial", 12))
        self.button_ecg_stream_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # ECG Hardware OFF Button
        self.button_ecg_stream_off = QPushButton("OFF", self)
        self.button_ecg_stream_off.resize(60, 30)
        self.button_ecg_stream_off.move(810, 145)
        self.button_ecg_stream_off.clicked.connect(self.buttonECG_STR_OFF)
        self.button_ecg_stream_off.setFont(QFont("Arial", 12))
        self.button_ecg_stream_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # ECG Stream Status Label
        self.label_ecg = QLabel(self)
        self.label_ecg.setText('Stream Status:')
        self.label_ecg.setGeometry(660, 190, 200, 20)
        self.label_ecg.setFont(QFont('Arial', 12))
        self.label_ecg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # ECG Stream Status Label ON/OFF
        self.label_ecg_stream = QLabel(self)
        self.label_ecg_stream.setText('OFF')
        self.label_ecg_stream.setGeometry(770, 190, 200, 20)
        self.label_ecg_stream.setFont(QFont('Arial', 12))
        self.label_ecg_stream.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        # ECG Record Label
        self.label_ecg = QLabel(self)
        self.label_ecg.setText('Record:')
        self.label_ecg.setGeometry(660, 230, 200, 20)
        self.label_ecg.setFont(QFont('Arial', 12))
        self.label_ecg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # ECG Record ON Button
        self.button_ecg_record_on = QPushButton("ON", self)
        self.button_ecg_record_on.resize(60, 30)
        self.button_ecg_record_on.move(740, 225)
        #self.button_ecg_record_on.clicked.connect(self.buttonDataFunction)
        self.button_ecg_record_on.setFont(QFont("Arial", 12))
        self.button_ecg_record_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # ECG Record OFF Button
        self.button_ecg_record_off = QPushButton("OFF", self)
        self.button_ecg_record_off.resize(60, 30)
        self.button_ecg_record_off.move(810, 225)
        #self.button_ecg_record_off.clicked.connect(self.buttonDataFunction)
        self.button_ecg_record_off.setFont(QFont("Arial", 12))
        self.button_ecg_record_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # ECG Record Status Label
        self.label_ppg = QLabel(self)
        self.label_ppg.setText('Record Status:')
        self.label_ppg.setGeometry(660, 270, 200, 20)
        self.label_ppg.setFont(QFont('Arial', 12))
        self.label_ppg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # ECG Record Status Label ON/OFF
        self.label_ecg_record = QLabel(self)
        self.label_ecg_record.setText('OFF')
        self.label_ecg_record.setGeometry(770, 270, 200, 20)
        self.label_ecg_record.setFont(QFont('Arial', 12))
        self.label_ecg_record.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        ### GRAPH ECG
        self.x_ecg      = list(range(ecg_max_list))
        self.y_ecg      = list(randint(0, 0) for _ in range(ecg_max_list)) 
        self.graph_ecg  = pg.PlotWidget(self)
        self.graph_ecg.setGeometry(900, 30, 1650, 310)
        self.graph_ecg.setBackground(None)
        self.graph_ecg.setXRange(-history_depth * 1000, 0, padding = 0.01)
        self.graph_ecg.setYRange(min(self.y_ecg), max(self.y_ecg), padding = 0.03)
        self.graph_ecg.showGrid(x = True, y = True, alpha = 0.6)
        pen_ecg         = pg.mkPen(color = ecg_color, width = 3)
        self.ecg_data   = self.graph_ecg.plot(self.x_ecg, self.y_ecg, pen = pen_ecg)
        #endregion
        
        #region   PPG

        # PPG Label
        self.label_ppg = QLabel(self)
        self.label_ppg.setText('PPG')
        self.label_ppg.setGeometry(660, 360, 100, 20)
        self.label_ppg.setFont(QFont('Arial', 20))
        self.label_ppg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # PPG Hardware Label
        self.label_ppg = QLabel(self)
        self.label_ppg.setText('Hardware:')
        self.label_ppg.setGeometry(660, 400, 100, 20)
        self.label_ppg.setFont(QFont('Arial', 12))
        self.label_ppg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # PPG Hardware ON Button
        self.button_ppg_hw_on = QPushButton("ON", self)
        self.button_ppg_hw_on.resize(60, 30)
        self.button_ppg_hw_on.move(740, 395)
        self.button_ppg_hw_on.clicked.connect(self.buttonPPG_HW_ON)
        self.button_ppg_hw_on.setFont(QFont("Arial", 12))
        self.button_ppg_hw_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # PPG Hardware OFF Button
        self.button_ppg_hw_off = QPushButton("OFF", self)
        self.button_ppg_hw_off.resize(60, 30)
        self.button_ppg_hw_off.move(810, 395)
        self.button_ppg_hw_off.clicked.connect(self.buttonPPG_HW_OFF)
        self.button_ppg_hw_off.setFont(QFont("Arial", 12))
        self.button_ppg_hw_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # PPG Hardware Status Label
        self.label_ppg = QLabel(self)
        self.label_ppg.setText('Hardware Status:')
        self.label_ppg.setGeometry(660, 440, 200, 20)
        self.label_ppg.setFont(QFont('Arial', 12))
        self.label_ppg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # PPG Hardware Status Label ON/OFF
        self.label_ppg_hw = QLabel(self)
        self.label_ppg_hw.setText('OFF')
        self.label_ppg_hw.setGeometry(790, 440, 200, 20)
        self.label_ppg_hw.setFont(QFont('Arial', 12))
        self.label_ppg_hw.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        # PPG Stream Label
        self.label_ppg = QLabel(self)
        self.label_ppg.setText('Stream:')
        self.label_ppg.setGeometry(660, 480, 200, 20)
        self.label_ppg.setFont(QFont('Arial', 12))
        self.label_ppg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # PPG Stream ON Button
        self.button_ppg_stream_on = QPushButton("ON", self)
        self.button_ppg_stream_on.resize(60, 30)
        self.button_ppg_stream_on.move(740, 475)
        self.button_ppg_stream_on.clicked.connect(self.buttonPPG_STR_ON)
        self.button_ppg_stream_on.setFont(QFont("Arial", 12))
        self.button_ppg_stream_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # PPG Hardware OFF Button
        self.button_ppg_stream_off = QPushButton("OFF", self)
        self.button_ppg_stream_off.resize(60, 30)
        self.button_ppg_stream_off.move(810, 475)
        self.button_ppg_stream_off.clicked.connect(self.buttonPPG_STR_OFF)
        self.button_ppg_stream_off.setFont(QFont("Arial", 12))
        self.button_ppg_stream_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # PPG Stream Status Label
        self.label_ppg = QLabel(self)
        self.label_ppg.setText('Stream Status:')
        self.label_ppg.setGeometry(660, 520, 200, 20)
        self.label_ppg.setFont(QFont('Arial', 12))
        self.label_ppg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # PPG Stream Status Label ON/OFF
        self.label_ppg_stream = QLabel(self)
        self.label_ppg_stream.setText('OFF')
        self.label_ppg_stream.setGeometry(770, 520, 200, 20)
        self.label_ppg_stream.setFont(QFont('Arial', 12))
        self.label_ppg_stream.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        # PPG Record Label
        self.label_ppg = QLabel(self)
        self.label_ppg.setText('Record:')
        self.label_ppg.setGeometry(660, 560, 200, 20)
        self.label_ppg.setFont(QFont('Arial', 12))
        self.label_ppg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # PPG Record ON Button
        self.button_ppg_record_on = QPushButton("ON", self)
        self.button_ppg_record_on.resize(60, 30)
        self.button_ppg_record_on.move(740, 555)
        #self.button_ppg_record_on.clicked.connect(self.buttonDataFunction)
        self.button_ppg_record_on.setFont(QFont("Arial", 12))
        self.button_ppg_record_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # PPG Record OFF Button
        self.button_ppg_record_off = QPushButton("OFF", self)
        self.button_ppg_record_off.resize(60, 30)
        self.button_ppg_record_off.move(810, 555)
        #self.button_ppg_record_off.clicked.connect(self.buttonDataFunction)
        self.button_ppg_record_off.setFont(QFont("Arial", 12))
        self.button_ppg_record_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # PPG Record Status Label
        self.label_ppg = QLabel(self)
        self.label_ppg.setText('Record Status:')
        self.label_ppg.setGeometry(660, 600, 200, 20)
        self.label_ppg.setFont(QFont('Arial', 12))
        self.label_ppg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # PPG Record Status Label ON/OFF
        self.label_ppg_record = QLabel(self)
        self.label_ppg_record.setText('OFF')
        self.label_ppg_record.setGeometry(770, 600, 200, 20)
        self.label_ppg_record.setFont(QFont('Arial', 12))
        self.label_ppg_record.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
        
        # PPG Message ID Label
        self.label_ppg = QLabel(self)
        self.label_ppg.setText('Message ID:')
        self.label_ppg.setGeometry(660, 640, 200, 20)
        self.label_ppg.setFont(QFont('Arial', 12))
        self.label_ppg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        ### GRAPH PPG
        self.x_ppg      = list(range(ppg_max_list))
        self.y_ppg      = list(randint(0, 0) for _ in range(ppg_max_list)) 
        self.graph_ppg  = pg.PlotWidget(self)
        self.graph_ppg.setGeometry(900, 360, 1650, 310)
        self.graph_ppg.setBackground(None)
        self.graph_ppg.setXRange(-history_depth * 1000, 0, padding = 0.01)
        self.graph_ppg.setYRange(min(self.y_ppg), max(self.y_ppg), padding = 0.03)
        self.graph_ppg.showGrid(x = True, y = True, alpha = 0.6)
        pen_ppg         = pg.mkPen(color = ppg_color, width = 3)
        self.ppg_data   = self.graph_ppg.plot(self.x_ppg, self.y_ppg, pen = pen_ppg)
        #endregion

        #region   Stethoscope

        # Stethoscope Label
        self.label_ecg = QLabel(self)
        self.label_ecg.setText('STETHOSCOPE')
        self.label_ecg.setGeometry(660, 690, 250, 20)
        self.label_ecg.setFont(QFont('Arial', 20))
        self.label_ecg.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # AUX Hardware Label
        self.label_aux = QLabel(self)
        self.label_aux.setText('Hardware:')
        self.label_aux.setGeometry(660, 730, 100, 20)
        self.label_aux.setFont(QFont('Arial', 12))
        self.label_aux.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # AUX Hardware ON Button
        self.button_aux_hw_on = QPushButton("ON", self)
        self.button_aux_hw_on.resize(60, 30)
        self.button_aux_hw_on.move(740, 725)
        self.button_aux_hw_on.clicked.connect(self.buttonAUX_HW_ON)
        self.button_aux_hw_on.setFont(QFont("Arial", 12))
        self.button_aux_hw_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # AUX Hardware OFF Button
        self.button_aux_hw_off = QPushButton("OFF", self)
        self.button_aux_hw_off.resize(60, 30)
        self.button_aux_hw_off.move(810, 725)
        self.button_aux_hw_off.clicked.connect(self.buttonAUX_HW_OFF)
        self.button_aux_hw_off.setFont(QFont("Arial", 12))
        self.button_aux_hw_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # AUX Hardware Status Label
        self.label_aux = QLabel(self)
        self.label_aux.setText('Hardware Status:')
        self.label_aux.setGeometry(660, 770, 200, 20)
        self.label_aux.setFont(QFont('Arial', 12))
        self.label_aux.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # AUX Hardware Status Label ON/OFF
        self.label_aux_hw = QLabel(self)
        self.label_aux_hw.setText('OFF')
        self.label_aux_hw.setGeometry(790, 770, 200, 20)
        self.label_aux_hw.setFont(QFont('Arial', 12))
        self.label_aux_hw.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        # AUX Stream Label
        self.label_aux = QLabel(self)
        self.label_aux.setText('Stream:')
        self.label_aux.setGeometry(660, 810, 200, 20)
        self.label_aux.setFont(QFont('Arial', 12))
        self.label_aux.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # AUX Stream ON Button
        self.button_aux_stream_on = QPushButton("ON", self)
        self.button_aux_stream_on.resize(60, 30)
        self.button_aux_stream_on.move(740, 805)
        self.button_aux_stream_on.clicked.connect(self.buttonAUX_STR_ON)
        self.button_aux_stream_on.setFont(QFont("Arial", 12))
        self.button_aux_stream_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # AUX Hardware OFF Button
        self.button_aux_stream_off = QPushButton("OFF", self)
        self.button_aux_stream_off.resize(60, 30)
        self.button_aux_stream_off.move(810, 805)
        self.button_aux_stream_off.clicked.connect(self.buttonAUX_STR_OFF)
        self.button_aux_stream_off.setFont(QFont("Arial", 12))
        self.button_aux_stream_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # AUX Stream Status Label
        self.label_aux = QLabel(self)
        self.label_aux.setText('Stream Status:')
        self.label_aux.setGeometry(660, 850, 200, 20)
        self.label_aux.setFont(QFont('Arial', 12))
        self.label_aux.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # AUX Stream Status Label ON/OFF
        self.label_aux_stream = QLabel(self)
        self.label_aux_stream.setText('OFF')
        self.label_aux_stream.setGeometry(770, 850, 200, 20)
        self.label_aux_stream.setFont(QFont('Arial', 12))
        self.label_aux_stream.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        # AUX Record Label
        self.label_aux = QLabel(self)
        self.label_aux.setText('Record:')
        self.label_aux.setGeometry(660, 890, 200, 20)
        self.label_aux.setFont(QFont('Arial', 12))
        self.label_aux.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # AUX Record ON Button
        self.button_aux_record_on = QPushButton("ON", self)
        self.button_aux_record_on.resize(60, 30)
        self.button_aux_record_on.move(740, 885)
        #self.button_aux_record_on.clicked.connect(self.buttonDataFunction)
        self.button_aux_record_on.setFont(QFont("Arial", 12))
        self.button_aux_record_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # AUX Record OFF Button
        self.button_aux_record_off = QPushButton("OFF", self)
        self.button_aux_record_off.resize(60, 30)
        self.button_aux_record_off.move(810, 885)
        #self.button_aux_record_off.clicked.connect(self.buttonDataFunction)
        self.button_aux_record_off.setFont(QFont("Arial", 12))
        self.button_aux_record_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # AUX Record Status Label
        self.label_aux = QLabel(self)
        self.label_aux.setText('Record Status:')
        self.label_aux.setGeometry(660, 930, 200, 20)
        self.label_aux.setFont(QFont('Arial', 12))
        self.label_aux.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # AUX Record Status Label ON/OFF
        self.label_aux_record = QLabel(self)
        self.label_aux_record.setText('OFF')
        self.label_aux_record.setGeometry(770, 930, 200, 20)
        self.label_aux_record.setFont(QFont('Arial', 12))
        self.label_aux_record.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
        
        # AUX Message ID Label
        self.label_aux = QLabel(self)
        self.label_aux.setText('Message ID:')
        self.label_aux.setGeometry(660, 970, 200, 20)
        self.label_aux.setFont(QFont('Arial', 12))
        self.label_aux.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        ### GRAPH AUX
        self.x_aux      = list(range(aux_max_list))
        self.y_aux      = list(randint(0, 0) for _ in range(aux_max_list)) 
        self.graph_aux  = pg.PlotWidget(self)
        self.graph_aux.setGeometry(900, 690, 1650, 310)
        self.graph_aux.setBackground(None)
        self.graph_aux.setXRange(-history_depth * 1000, 0, padding = 0.01)
        self.graph_aux.setYRange(min(self.y_aux), max(self.y_aux), padding = 0.03)
        self.graph_aux.showGrid(x = True, y = True, alpha = 0.6)
        pen_aux         = pg.mkPen(color = aux_color, width = 3)
        self.aux_data   = self.graph_aux.plot(self.x_aux, self.y_aux, pen = pen_aux)
        #endregion

        #region   BPM MANUAL

        # BPM Label
        self.label_bpm = QLabel(self)
        self.label_bpm.setText('BPM MANUAL')
        self.label_bpm.setGeometry(660, 1020, 250, 20)
        self.label_bpm.setFont(QFont('Arial', 20))
        self.label_bpm.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # BPM Stream Label
        self.label_bpm = QLabel(self)
        self.label_bpm.setText('Stream:')
        self.label_bpm.setGeometry(660, 1060, 200, 20)
        self.label_bpm.setFont(QFont('Arial', 12))
        self.label_bpm.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # BPM Stream ON Button
        self.button_bpm_stream_on = QPushButton("ON", self)
        self.button_bpm_stream_on.resize(60, 30)
        self.button_bpm_stream_on.move(740, 1055)
        self.button_bpm_stream_on.clicked.connect(self.buttonBPM_STR_ON)
        self.button_bpm_stream_on.setFont(QFont("Arial", 12))
        self.button_bpm_stream_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # BPM Hardware OFF Button
        self.button_bpm_stream_off = QPushButton("OFF", self)
        self.button_bpm_stream_off.resize(60, 30)
        self.button_bpm_stream_off.move(810, 1055)
        self.button_bpm_stream_off.clicked.connect(self.buttonBPM_STR_OFF)
        self.button_bpm_stream_off.setFont(QFont("Arial", 12))
        self.button_bpm_stream_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # BPM Stream Status Label
        self.label_bpm = QLabel(self)
        self.label_bpm.setText('Stream Status:')
        self.label_bpm.setGeometry(660, 1100, 200, 20)
        self.label_bpm.setFont(QFont('Arial', 12))
        self.label_bpm.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # BPM Stream Status Label ON/OFF
        self.label_bpm_stream = QLabel(self)
        self.label_bpm_stream.setText('OFF')
        self.label_bpm_stream.setGeometry(770, 1100, 200, 20)
        self.label_bpm_stream.setFont(QFont('Arial', 12))
        self.label_bpm_stream.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        # BPM Record Label
        self.label_bpm = QLabel(self)
        self.label_bpm.setText('PUMP:')
        self.label_bpm.setGeometry(660, 1140, 200, 20)
        self.label_bpm.setFont(QFont('Arial', 12))
        self.label_bpm.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # BPM Record ON Button
        self.button_bpm_pump_on = QPushButton("ON", self)
        self.button_bpm_pump_on.resize(60, 30)
        self.button_bpm_pump_on.move(740, 1135)
        self.button_bpm_pump_on.clicked.connect(self.buttonBPM_PUMP_ON_fun)
        self.button_bpm_pump_on.setFont(QFont("Arial", 12))
        self.button_bpm_pump_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # BPM Record OFF Button
        self.button_bpm_pump_off = QPushButton("OFF", self)
        self.button_bpm_pump_off.resize(60, 30)
        self.button_bpm_pump_off.move(810, 1135)
        self.button_bpm_pump_off.clicked.connect(self.buttonBPM_PUMP_OFF_fun)
        self.button_bpm_pump_off.setFont(QFont("Arial", 12))
        self.button_bpm_pump_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # BPM Record Status Label
        self.label_bpm = QLabel(self)
        self.label_bpm.setText('Pump Status:')
        self.label_bpm.setGeometry(660, 1180, 200, 20)
        self.label_bpm.setFont(QFont('Arial', 12))
        self.label_bpm.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # BPM Record Status Label ON/OFF
        self.label_bpm_pump_status = QLabel(self)
        self.label_bpm_pump_status.setText('OFF')
        self.label_bpm_pump_status.setGeometry(770, 1180, 200, 20)
        self.label_bpm_pump_status.setFont(QFont('Arial', 12))
        self.label_bpm_pump_status.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

        # BPM Record Label
        self.label_bpm = QLabel(self)
        self.label_bpm.setText('VALVE:')
        self.label_bpm.setGeometry(660, 1220, 200, 20)
        self.label_bpm.setFont(QFont('Arial', 12))
        self.label_bpm.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # BPM Record ON Button
        self.button_bpm_valve_on = QPushButton("ON", self)
        self.button_bpm_valve_on.resize(60, 30)
        self.button_bpm_valve_on.move(740, 1215)
        self.button_bpm_valve_on.clicked.connect(self.buttonBPM_VALVE_ON_fun)
        self.button_bpm_valve_on.setFont(QFont("Arial", 12))
        self.button_bpm_valve_on.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # BPM Record OFF Button
        self.button_bpm_valve_off = QPushButton("OFF", self)
        self.button_bpm_valve_off.resize(60, 30)
        self.button_bpm_valve_off.move(810, 1215)
        self.button_bpm_valve_off.clicked.connect(self.buttonBPM_VALVE_OFF_fun)
        self.button_bpm_valve_off.setFont(QFont("Arial", 12))
        self.button_bpm_valve_off.setStyleSheet("QPushButton {background-color : rgb(45, 50, 60); color : rgb(150, 150, 150); font-weight: bold}")

        # BPM Record Status Label
        self.label_bpm = QLabel(self)
        self.label_bpm.setText('Valve Status:')
        self.label_bpm.setGeometry(660, 1260, 200, 20)
        self.label_bpm.setFont(QFont('Arial', 12))
        self.label_bpm.setStyleSheet('QLabel {color : rgb(150, 150, 150)}')

        # BPM Record Status Label ON/OFF
        self.label_bpm_valve_status = QLabel(self)
        self.label_bpm_valve_status.setText('OFF')
        self.label_bpm_valve_status.setGeometry(770, 1260, 200, 20)
        self.label_bpm_valve_status.setFont(QFont('Arial', 12))
        self.label_bpm_valve_status.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
        
        ### GRAPH BPM
        self.x_bpm      = list(range(bpm_max_list))
        self.y_bpm      = list(randint(0, 0) for _ in range(bpm_max_list)) 
        self.graph_bpm  = pg.PlotWidget(self)
        self.graph_bpm.setGeometry(900, 1020, 1650, 330)
        self.graph_bpm.setBackground(None)
        self.graph_bpm.setXRange(-history_depth * 1000, 0, padding = 0.01)
        self.graph_bpm.setYRange(min(self.y_aux), max(self.y_aux), padding = 0.03)
        self.graph_bpm.showGrid(x = True, y = True, alpha = 0.6)
        pen_bpm         = pg.mkPen(color = bpm_color, width = 3)
        self.bpm_data   = self.graph_bpm.plot(self.x_bpm, self.y_bpm, pen = pen_bpm)
        #endregion

        # Keep above all functions
        self.show()

    # Function for updating the ECG Graph
    def update_ecg_graph(self):
        # Global variables/parameters needed for this function
        global ecg_adc_buffer, ecg_time_buffer, ecg_id_buffer, ecg_data_flag, history_depth, ecg_last_timestamp, data_stream_flag, ecg_stream_active, recording_flag, data_ecg_adc, data_time_ecg
        #print(ppg_ir_buffer)
        if data_stream_flag == True and ecg_stream_active == True:
            # Check whether there is new data with which we want to update the graph
            if ecg_data_flag == True:
                # Reset the flag
                ecg_data_flag = False
                # Calculate what's the oldest acceptable timestamp
                oldest_timestamp = ecg_time_buffer[-1] - history_depth * 1000
                # Increase all element of self.x_ppg by the last timestamp from last cycle
                self.x_ecg = [x + ecg_last_timestamp for x in self.x_ecg]
                # Make the desired time axis using the previous time axis plus the new buffer
                new_time_axis = self.x_ecg + ecg_time_buffer
                # Find the index from which you should use the data
                new_time_axis_index = 0
                for i in range(0, len(new_time_axis)):
                    if new_time_axis[i] >= oldest_timestamp:
                        new_time_axis_index = i
                        break
                # Update the new time axis using the found index
                new_time_axis = new_time_axis[new_time_axis_index :]
                # Find the new last timestamp
                ecg_last_timestamp = new_time_axis[-1]
                new_time_axis = [x - ecg_last_timestamp for x in new_time_axis]
                # Construct the new y axis
                new_ecg_axis = self.y_ecg + ecg_adc_buffer
                # Update the new ppg axis using the found time index
                new_ecg_axis = new_ecg_axis[new_time_axis_index :]

                # Update the self.x_ppg and self.y_ppg
                self.x_ecg = new_time_axis
                self.y_ecg = new_ecg_axis

                # Update the X and Y range of the graph
                self.graph_ecg.setXRange(-history_depth * 1000, 0, padding = 0.01)
                self.graph_ecg.setYRange(min(self.y_ecg), max(self.y_ecg), padding = 0.03)

                # Update the plot data
                self.ecg_data.setData(self.x_ecg, self.y_ecg)

                # Before resetting the buffers, if the record flag is on, store the small buffers into the data storage buffers
                if recording_flag == True:
                    # Append the small buffers to the data buffers
                    data_ecg_adc.append(ecg_adc_buffer)
                    data_time_ecg.append(ecg_time_buffer)

                # Reset all of the buffers
                ecg_adc_buffer  = []
                ecg_id_buffer   = []
                ecg_time_buffer = []  

    # Function for updating the PPG Graph
    def update_ppg_graph(self):
        # Global variables/parameters needed for this function
        global ppg_ir_buffer, ppg_time_buffer, ppg_id_buffer, ppg_data_flag, history_depth, ppg_last_timestamp, data_stream_flag, ppg_stream_active, recording_flag, data_time_ppg, data_ppg
        #print(ppg_ir_buffer)
        if data_stream_flag == True and ppg_stream_active == True:
            # Check whether there is new data with which we want to update the graph
            if ppg_data_flag == True:
                # Reset the flag
                ppg_data_flag = False
                # Calculate what's the oldest acceptable timestamp
                oldest_timestamp = ppg_time_buffer[-1] - history_depth * 1000
                # Increase all element of self.x_ppg by the last timestamp from last cycle
                self.x_ppg = [x + ppg_last_timestamp for x in self.x_ppg]
                # Make the desired time axis using the previous time axis plus the new buffer
                new_time_axis = self.x_ppg + ppg_time_buffer
                # Find the index from which you should use the data
                new_time_axis_index = 0
                for i in range(0, len(new_time_axis)):
                    if new_time_axis[i] >= oldest_timestamp:
                        new_time_axis_index = i
                        break
                # Update the new time axis using the found index
                new_time_axis = new_time_axis[new_time_axis_index :]
                # Find the new last timestamp
                ppg_last_timestamp = new_time_axis[-1]
                new_time_axis = [x - ppg_last_timestamp for x in new_time_axis]
                # Construct the new y axis
                new_ppg_axis = self.y_ppg + ppg_ir_buffer
                # Update the new ppg axis using the found time index
                new_ppg_axis = new_ppg_axis[new_time_axis_index :]

                # Update the self.x_ppg and self.y_ppg
                self.x_ppg = new_time_axis
                self.y_ppg = new_ppg_axis

                # Update the X and Y range of the graph
                self.graph_ppg.setXRange(-history_depth * 1000, 0, padding = 0.01)
                self.graph_ppg.setYRange(min(self.y_ppg), max(self.y_ppg), padding = 0.03)

                # Update the plot data
                self.ppg_data.setData(self.x_ppg, self.y_ppg)

                # Before resetting the buffers, if the record flag is on, store the small buffers into the data storage buffers
                if recording_flag == True:
                    # Append the small buffers to the data buffers
                    data_ppg.append(ppg_ir_buffer)
                    data_time_ppg.append(ppg_time_buffer)

                # Reset all of the buffers
                ppg_ir_buffer   = []
                ppg_id_buffer   = []
                ppg_time_buffer = []   

    # Function for updating the BPM Graph
    def update_bpm_graph(self):
        # Global variables/parameters needed for this function
        global bpm_adc_buffer, bpm_time_buffer, bpm_data_flag, history_depth, bpm_last_timestamp, data_stream_flag, bpm_stream_active, recording_flag, data_bpm_adc, data_time_bpm
        #print(ppg_ir_buffer)
        if data_stream_flag == True and bpm_stream_active == True:
            # Check whether there is new data with which we want to update the graph
            if bpm_data_flag == True:
                # Reset the flag
                bpm_data_flag = False
                # Calculate what's the oldest acceptable timestamp
                oldest_timestamp = bpm_time_buffer[-1] - history_depth * 1000
                # Increase all element of self.x_ppg by the last timestamp from last cycle
                self.x_bpm = [x + bpm_last_timestamp for x in self.x_bpm]
                # Make the desired time axis using the previous time axis plus the new buffer
                new_time_axis = self.x_bpm + bpm_time_buffer
                # Find the index from which you should use the data
                new_time_axis_index = 0
                for i in range(0, len(new_time_axis)):
                    if new_time_axis[i] >= oldest_timestamp:
                        new_time_axis_index = i
                        break
                # Update the new time axis using the found index
                new_time_axis = new_time_axis[new_time_axis_index :]
                # Find the new last timestamp
                bpm_last_timestamp = new_time_axis[-1]
                new_time_axis = [x - bpm_last_timestamp for x in new_time_axis]
                # Construct the new y axis
                new_bpm_axis = self.y_bpm + bpm_adc_buffer
                # Update the new ppg axis using the found time index
                new_bpm_axis = new_bpm_axis[new_time_axis_index :]

                # Update the self.x_ppg and self.y_ppg
                self.x_bpm = new_time_axis
                self.y_bpm = new_bpm_axis

                # Update the X and Y range of the graph
                self.graph_bpm.setXRange(-history_depth * 1000, 0, padding = 0.01)
                self.graph_bpm.setYRange(min(self.y_bpm), max(self.y_bpm), padding = 0.03)

                # Update the plot data
                self.bpm_data.setData(self.x_bpm, self.y_bpm)

                # Before resetting the buffers, if the record flag is on, store the small buffers into the data storage buffers
                if recording_flag == True:
                    # Append the small buffers to the data buffers
                    data_bpm_adc.append(bpm_adc_buffer)
                    data_time_bpm.append(bpm_time_buffer)

                # Reset all of the buffers
                bpm_adc_buffer  = []
                bpm_time_buffer = [] 

    # Function for updating the AUX Graph
    def update_aux_graph(self):
        # Global variables/parameters needed for this function
        global aux_adc_buffer, aux_time_buffer, aux_data_flag, history_depth, aux_last_timestamp, data_stream_flag, aux_stream_active, recording_flag, data_aux_adc, data_time_aux
        #print(ppg_ir_buffer)
        if data_stream_flag == True and aux_stream_active == True:
            # Check whether there is new data with which we want to update the graph
            if aux_data_flag == True:
                # Reset the flag
                aux_data_flag = False
                # Calculate what's the oldest acceptable timestamp
                oldest_timestamp = aux_time_buffer[-1] - history_depth * 1000
                # Increase all element of self.x_ppg by the last timestamp from last cycle
                self.x_aux = [x + aux_last_timestamp for x in self.x_aux]
                # Make the desired time axis using the previous time axis plus the new buffer
                new_time_axis = self.x_aux + aux_time_buffer
                # Find the index from which you should use the data
                new_time_axis_index = 0
                for i in range(0, len(new_time_axis)):
                    if new_time_axis[i] >= oldest_timestamp:
                        new_time_axis_index = i
                        break
                # Update the new time axis using the found index
                new_time_axis = new_time_axis[new_time_axis_index :]
                # Find the new last timestamp
                aux_last_timestamp = new_time_axis[-1]
                new_time_axis = [x - aux_last_timestamp for x in new_time_axis]
                # Construct the new y axis
                new_aux_axis = self.y_aux + aux_adc_buffer
                # Update the new ppg axis using the found time index
                new_aux_axis = new_aux_axis[new_time_axis_index :]

                # Update the self.x_ppg and self.y_ppg
                self.x_aux = new_time_axis
                self.y_aux = new_aux_axis

                # Update the X and Y range of the graph
                self.graph_aux.setXRange(-history_depth * 1000, 0, padding = 0.01)
                self.graph_aux.setYRange(min(self.y_aux), max(self.y_aux), padding = 0.03)

                # Update the plot data
                self.aux_data.setData(self.x_aux, self.y_aux)

                # Before resetting the buffers, if the record flag is on, store the small buffers into the data storage buffers
                if recording_flag == True:
                    # Append the small buffers to the data buffers
                    data_aux_adc.append(aux_adc_buffer)
                    data_time_aux.append(aux_time_buffer)

                # Reset all of the buffers
                aux_adc_buffer  = []
                aux_time_buffer = [] 

    # Update Function
    def updateEvent(self):
        global ports_found, old_ports, COM_ports, connection
        if ports_found == True and connection == False:
            ports_found = False
            self.Com_port.clear()
            self.Com_port.addItems(COM_ports)
            old_ports = COM_ports
        self.update()

    # Function for Painting Lines
    def paintEvent(self, event):

        global line_color, line_width

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(line_color, line_width))

        # Lines

        # Horizontal lines
        painter.drawLine(10, 20, 2550, 20)
        painter.drawLine(650, 350, 2550, 350)
        painter.drawLine(650, 680, 2550, 680)  
        painter.drawLine(650, 1010, 2550, 1010)
        painter.drawLine(10, 1350, 2550, 1350)
        painter.drawLine(10, 100, 650, 100)
        painter.drawLine(10, 230, 650, 230)
        painter.drawLine(10, 350, 650, 350)
        painter.drawLine(10, 515, 650, 515)
        painter.drawLine(10, 845, 650, 845)


        # Vertical lines
        painter.drawLine(650, 20, 650, 1350)
        painter.drawLine(10, 20, 10, 1350)
        painter.drawLine(2550, 20, 2550, 1350)
        painter.drawLine(895, 20, 895, 1350)

    # Data Stream Start Button Function
    def buttonDataFunction(self):
        global comm_port, data_stream_flag, connection
        print('Button for Starting the Data Stream pressed.')
        if data_stream_flag == False and connection == True:
            print('Enabling the Data Stream.')
            comm_port.write(cmd_start_stream.encode())
            data_stream_flag = True
            self.label_stream_flag.setText('ENABLED')
            self.label_stream_flag.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            time.sleep(0.5)

    # Data Stream Stop Button Function
    def buttonDataStopFunction(self):
        global comm_port, data_stream_flag
        print('Button for Stopping the Data Stream Pressed.')
        if data_stream_flag == True and connection == True:
            print('Disabling the Data Stream.')
            comm_port.write(cmd_stop_stream.encode())
            data_stream_flag = False
            self.label_stream_flag.setText('DISABLED')
            self.label_stream_flag.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            time.sleep(0.5)

    # Button Connect to Serial Port Function
    def buttonConnectFunction(self):
        global connection, comm_port
        comm_port.port      = str(self.Com_port.currentText())
        comm_port.baudrate  = int(self.baudrate_cb.currentText())
        if comm_port.is_open == False:
            comm_port.open()
        time.sleep(0.1)
        if comm_port.is_open == True:
            self.label_con_status.setText('CONNECTED')
            self.label_con_status.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            print('Opening COM port connection with current parameters:')
            print('Port: ' + str(self.Com_port.currentText()))
            print('Baudrate: ' + str(self.baudrate_cb.currentText()))
            connection = True
        else:
            print('Error opening the port')

    # Button Disconnect from Serial Port Function
    def buttonDisconnectFunction(self):
        global connection, comm_port
        connection = False
        time.sleep(0.1)
        if comm_port.is_open == True:
            print('Closing the connection')
            self.label_con_status.setText('DISCONNECTED')
            self.label_con_status.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            comm_port.close()
        else:
            print('No connection to close')

    # Button Start Recording
    def buttonStartRecordingFunction(self):
        global recording_flag, data_stream_flag, data_storing_flag
        time.sleep(0.1)
        if recording_flag == True:
            print('Recording has already been started, stop the current recording to start a new one')
        else:
            # This is the case where we want to turn ON the recording, we need to:
            # 1. Change the recording_flag to True
            # 2. Change the label to green and the text to RECORDING
            # 3. Disable changing the text in the LineEdit
            print('Start Recording button pressed')
            if data_stream_flag == True:
                if data_storing_flag == False:
                    if self.record_file_name.text() != '':
                        recording_flag = True
                        self.label_record_flag.setText('RECORDING')
                        self.label_record_flag.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
                        self.record_file_name.setReadOnly(True)
                    else:
                        print('To start recording, enter a non empty filename.')
                else:
                    print('Data storing process currently running, recording is disabled until the storing process has been completed')
            else:
                print('Recording session not started because there is no active data stream to record.')

    # Button Stop Recording
    def buttonStopRecordingFunction(self):
        global recording_flag
        time.sleep(0.1)
        if recording_flag == False:
            print('There is not an active recording session to stop.')
        else:
            # This is the case where we want to turn ON the recording, we need to:
            # 1. Change the recording_flag to False
            # 2. Change the label to green and the text to NOT RECORDING
            # 3. Enable changing the text in the LineEdit
            # 4. Run the data storing function
            recording_flag = False
            self.label_record_flag.setText('NOT RECORDING')
            self.label_record_flag.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            self.record_file_name.setReadOnly(False)
            StoreData(self.record_file_name.text())

    #region ECG BUTTONS

    # ECG HW ON BUTTON   
    def buttonECG_HW_ON(self):
        global connection, comm_port, ecg_hw_active
        print('Button for turning the ECG ON pressed.')
        # Check if connection is established
        if comm_port.is_open == True and connection == True and ecg_hw_active == False:
            print('Sending command to turn ON the ECG.')
            # Print out the message
            comm_port.write(cmd_ecg_start.encode())
            # Change the label
            self.label_ecg_hw.setText('ON')
            self.label_ecg_hw.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            # Change the flag
            ecg_hw_active = True
        elif ecg_hw_active == False:
            # This is the case where the ECG is already turned ON
            print('ECG is already turned ON')
        else:
            # In this case we don't want to send command becasue we don't have a connection to the hardware
            print('Comm port error, can not send a command to the hardware.')

    # ECG HW OFF BUTTON
    def buttonECG_HW_OFF(self):
        global connection, comm_port, ecg_hw_active
        print('Button for turning the ECG OFF pressed.')
        # Check if connection is established
        if comm_port.is_open == True and connection == True and ecg_hw_active == True:
            print('Sending command to turn OFF the ECG.')
            # Print out the message
            comm_port.write(cmd_ecg_stop.encode())
            # Change the label
            self.label_ecg_hw.setText('OFF')
            self.label_ecg_hw.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            # Change the flag
            ecg_hw_active = False
        elif ecg_hw_active == True:
            # This is the case where the ECG is already turned ON
            print('ECG is already turned OFF')
        else:
            # In this case we don't want to send command becasue we don't have a connection to the hardware
            print('Comm port error, can not send a command to the hardware.')

    # ECG STREAM ON BUTTON
    def buttonECG_STR_ON(self):
        global ecg_stream_active
        print('ECG Stream ON Button Pressed.')
        if ecg_stream_active == True:
            print('ECG Stream already turned ON.')
        else:
            print('Turning ECG Stream ON.')
            self.label_ecg_stream.setText('ON')
            self.label_ecg_stream.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            ecg_stream_active = True

    # ECG STREAM OFF BUTTON
    def buttonECG_STR_OFF(self):
        global ecg_stream_active
        print('ECG Stream OFF Button Pressed.')
        if ecg_stream_active == False:
            print('ECG Stream already turned OFF.')
        else:
            print('Turning ECG Stream OFF.')
            self.label_ecg_stream.setText('OFF')
            self.label_ecg_stream.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            ecg_stream_active = False
    #endregion

    #region PPG BUTTONS

    # PPG HW ON BUTTON   
    def buttonPPG_HW_ON(self):
        global connection, comm_port, ppg_hw_active
        print('Button for turning the PPG ON pressed.')
        # Check if connection is established
        if comm_port.is_open == True and connection == True and ppg_hw_active == False:
            print('Sending command to turn ON the PPG.')
            # Print out the message
            comm_port.write(cmd_ppg_start.encode())
            # Change the label
            self.label_ppg_hw.setText('ON')
            self.label_ppg_hw.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            # Change the flag
            ppg_hw_active = True
        elif ppg_hw_active == False:
            # This is the case where the PPG is already turned ON
            print('PPG is already turned ON')
        else:
            # In this case we don't want to send command becasue we don't have a connection to the hardware
            print('Comm port error, can not send a command to the hardware.')

    # PPG HW OFF BUTTON
    def buttonPPG_HW_OFF(self):
        global connection, comm_port, ppg_hw_active
        print('Button for turning the PPG OFF pressed.')
        # Check if connection is established
        if comm_port.is_open == True and connection == True and ppg_hw_active == True:
            print('Sending command to turn OFF the PPG.')
            # Print out the message
            comm_port.write(cmd_ppg_stop.encode())
            # Change the label
            self.label_ppg_hw.setText('OFF')
            self.label_ppg_hw.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            # Change the flag
            ppg_hw_active = False
        elif ppg_hw_active == True:
            # This is the case where the PPG is already turned ON
            print('PPG is already turned OFF')
        else:
            # In this case we don't want to send command becasue we don't have a connection to the hardware
            print('Comm port error, can not send a command to the hardware.')

    # PPG STREAM ON BUTTON
    def buttonPPG_STR_ON(self):
        global ppg_stream_active
        print('PPG Stream ON Button Pressed.')
        if ppg_stream_active == True:
            print('PPG Stream already turned ON.')
        else:
            print('Turning PPG Stream ON.')
            self.label_ppg_stream.setText('ON')
            self.label_ppg_stream.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            ppg_stream_active = True

    # PPG STREAM OFF BUTTON
    def buttonPPG_STR_OFF(self):
        global ppg_stream_active
        print('PPG Stream OFF Button Pressed.')
        if ppg_stream_active == False:
            print('PPG Stream already turned OFF.')
        else:
            print('Turning PPG Stream OFF.')
            self.label_ppg_stream.setText('OFF')
            self.label_ppg_stream.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            ppg_stream_active = False

    #endregion    

    #region AUX BUTTONS

    # AUX HW ON BUTTON   
    def buttonAUX_HW_ON(self):
        global connection, comm_port, aux_hw_active
        print('Button for turning the AUX ON pressed.')
        # Check if connection is established
        if comm_port.is_open == True and connection == True and aux_hw_active == False:
            print('Sending command to turn ON the AUX.')
            # Print out the message
            comm_port.write(cmd_aux_start.encode())
            # Change the label
            self.label_aux_hw.setText('ON')
            self.label_aux_hw.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            # Change the flag
            aux_hw_active = True
        elif aux_hw_active == False:
            # This is the case where the AUX is already turned ON
            print('AUX is already turned ON')
        else:
            # In this case we don't want to send command becasue we don't have a connection to the hardware
            print('Comm port error, can not send a command to the hardware.')

    # AUX HW OFF BUTTON
    def buttonAUX_HW_OFF(self):
        global connection, comm_port, aux_hw_active
        print('Button for turning the AUX OFF pressed.')
        # Check if connection is established
        if comm_port.is_open == True and connection == True and aux_hw_active == True:
            print('Sending command to turn OFF the AUX.')
            # Print out the message
            comm_port.write(cmd_aux_stop.encode())
            # Change the label
            self.label_aux_hw.setText('OFF')
            self.label_aux_hw.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            # Change the flag
            aux_hw_active = False
        elif aux_hw_active == True:
            # This is the case where the AUX is already turned ON
            print('AUX is already turned OFF')
        else:
            # In this case we don't want to send command becasue we don't have a connection to the hardware
            print('Comm port error, can not send a command to the hardware.')

    # AUX STREAM ON BUTTON
    def buttonAUX_STR_ON(self):
        global aux_stream_active
        print('AUX Stream ON Button Pressed.')
        if aux_stream_active == True:
            print('AUX Stream already turned ON.')
        else:
            print('Turning AUX Stream ON.')
            self.label_aux_stream.setText('ON')
            self.label_aux_stream.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            aux_stream_active = True

    # AUX STREAM OFF BUTTON
    def buttonAUX_STR_OFF(self):
        global aux_stream_active
        print('AUX Stream OFF Button Pressed.')
        if aux_stream_active == False:
            print('AUX Stream already turned OFF.')
        else:
            print('Turning AUX Stream OFF.')
            self.label_aux_stream.setText('OFF')
            self.label_aux_stream.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            aux_stream_active = False
    #endregion

    #region BPM BUTTONS

    # BPM STREAM ON BUTTON
    def buttonBPM_STR_ON(self):
        global bpm_stream_active, bpm_hw_active
        print('BPM Stream ON Button Pressed.')
        if bpm_stream_active == True:
            print('BPM Stream already turned ON.')
        else:
            print('Turning BPM Stream ON.')
            self.label_bpm_stream.setText('ON')
            self.label_bpm_stream.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            bpm_stream_active = True
            if comm_port.is_open == True and connection == True and bpm_hw_active == False:
                print('Sending command to turn ON the BPM.')
                # Print out the message
                comm_port.write(cmd_bpm_start.encode())
                bpm_hw_active = True

    # BPM STREAM OFF BUTTON
    def buttonBPM_STR_OFF(self):
        global bpm_stream_active, bpm_hw_active
        print('BPM Stream OFF Button Pressed.')
        if bpm_stream_active == False:
            print('BPM Stream already turned OFF.')
        else:
            print('Turning BPM Stream OFF.')
            self.label_bpm_stream.setText('OFF')
            self.label_bpm_stream.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            bpm_stream_active = False
            if comm_port.is_open == True and connection == True and bpm_hw_active == True:
                print('Sending command to turn OFF the BPM.')
                # Print out the message
                comm_port.write(cmd_bpm_stop.encode())
                bpm_hw_active = False

    # BPM PUMP ON BUTTON
    def buttonBPM_PUMP_ON_fun(self):
        global bpm_active_measure, connection, comm_port, cmd_pump_start, bpm_pump_status
        if bpm_active_measure == True:
            print('Manual controls unavailable during an automatic blood pressure measurement')
        else:
            # This is the case where we are sending the command to turn on the pump at 100%
            if comm_port.is_open == True and connection == True:
                print('Sending command to turn ON the pump')
                # Send command
                comm_port.write(cmd_pump_start.encode())
                # Change the flag for the pump status
                bpm_pump_status = True
                # Change the label
                self.label_bpm_pump_status.setText('ON')
                self.label_bpm_pump_status.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            else:
                # In this case we don't want to send command becasue we don't have a connection to the hardware
                print('Comm port error, can not send a command to the hardware.')

    # BPM PUMP OFF BUTTON
    def buttonBPM_PUMP_OFF_fun(self):
        global bpm_active_measure, connection, comm_port, cmd_pump_stop, bpm_pump_status
        if bpm_active_measure == True:
            print('Manual controls unavailable during an automatic blood pressure measurement')
        else:
            # This is the case where we are sending the command to turn on the pump at 100%
            if comm_port.is_open == True and connection == True:
                print('Sending command to turn OFF the pump')
                # Send command
                comm_port.write(cmd_pump_stop.encode())
                # Change the flag for the pump status
                bpm_pump_status = False
                # Change the label
                self.label_bpm_pump_status.setText('OFF')
                self.label_bpm_pump_status.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            else:
                # In this case we don't want to send command becasue we don't have a connection to the hardware
                print('Comm port error, can not send a command to the hardware.')

    # BPM VALVE ON BUTTON
    def buttonBPM_VALVE_ON_fun(self):
        global bpm_active_measure, connection, comm_port, cmd_valve_start, bpm_valve_status
        if bpm_active_measure == True:
            print('Manual controls unavailable during an automatic blood pressure measurement')
        else:
            # This is the case where we are sending the command to turn on the valve at 100%
            if comm_port.is_open == True and connection == True:
                print('Sending command to turn ON the valve')
                # Send command
                comm_port.write(cmd_valve_start.encode())
                # Change the flag for the pump status
                bpm_valve_status = True
                # Change the label
                self.label_bpm_valve_status.setText('ON')
                self.label_bpm_valve_status.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')
            else:
                # In this case we don't want to send command becasue we don't have a connection to the hardware
                print('Comm port error, can not send a command to the hardware.')

    # BPM VALVE OFF BUTTON
    def buttonBPM_VALVE_OFF_fun(self):
        global bpm_active_measure, connection, comm_port, cmd_valve_stop, bpm_valve_status
        if bpm_active_measure == True:
            print('Manual controls unavailable during an automatic blood pressure measurement')
        else:
            # This is the case where we are sending the command to turn on the valve at 100%
            if comm_port.is_open == True and connection == True:
                print('Sending command to turn ON the valve')
                # Send command
                comm_port.write(cmd_valve_stop.encode())
                # Change the flag for the pump status
                bpm_valve_status = False
                # Change the label
                self.label_bpm_valve_status.setText('OFF')
                self.label_bpm_valve_status.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')
            else:
                # In this case we don't want to send command becasue we don't have a connection to the hardware
                print('Comm port error, can not send a command to the hardware.')

    # BPM ENABLE DATA FILE INTEGRATION
    def buttonBPM_EN_DATA_fun(self):
        global bpm_active_flag
        if bpm_active_flag == True:
            print('BPM file integration already enabled')
        else:
            print('Enabling BPM data file integration.')
            # Update the flag
            bpm_active_flag = True
            # Update the label
            self.label_bpm_file_en.setText('ENABLED')
            self.label_bpm_file_en.setStyleSheet('QLabel {color : rgb(150, 250, 150); font-weight: bold}')

    # BPM DISABLE DATA FILE INTEGRATION
    def buttonBPM_DIS_DATA_fun(self):
        global bpm_active_flag, recording_flag
        if bpm_active_flag == False:
            print('BPM file integration already disabled')
        else:
            if recording_flag == True:
                print('Not able to disable file integration during a recording session')
            else:
                print('Disabling BPM data file integration.')
                # Update the flag
                bpm_active_flag = False
                # Update the label
                self.label_bpm_file_en.setText('DISABLED')
                self.label_bpm_file_en.setStyleSheet('QLabel {color : rgb(250, 150, 150); font-weight: bold}')

    #endregion

# GUI Thread
def fun1():
    app = QApplication(sys.argv)
    ex = App()
    app.exec_()

# Old Thread 2
def fun22():
    while True:
        global comm_port
        val1 = comm_port.readline().decode()
        #print(val1)
        if val1[0] == '$':
            DecodeSerialData(val1)

# Data parser thread
def fun2():
    global ppg_hw_active, connection, comm_port, ecg_hw_active
    buffer = ''
    while True:
        if connection == True:
            waiting = comm_port.in_waiting  # find num of bytes currently waiting in hardware
            buffer = [chr(c) for c in comm_port.read(waiting)] # read them, convert to ascii
            #print(buffer)
            try:
                ind = buffer.index('#')
                if buffer[ind + 1] == '1':
                    ecg_hw_active = True
                    DecodeSerialData_ADC(buffer)
                if buffer[ind + 1] == '2':
                    print(2)
                    # If we get a message like this, it means that the HW is enabled in one way or the other on the HW side
                    ppg_hw_active = True
                    DecodeSerialData_PPG(buffer)
                elif buffer[ind + 1] == '3':
                    print(buffer)
                elif buffer[ind + 1] == '9':
                    # This is the unified message, and it needs its own special decoder function
                    DecodeSerialData_Unified(buffer)
                else:
                    continue
                buffer = ''
            except:
                pass
        else:
            time.sleep(0.1)

# COM port checker thread     
def fun3():
    global COM_ports, old_ports, ports_found, connection
    while True:
        if connection == False:
            serial_ports()
            if COM_ports != old_ports:
                ports_found = True
            time.sleep(1)
        else:
            time.sleep(0.1)

#region Threading
t1 = threading.Thread(target = fun1)
t2 = threading.Thread(target = fun2)
t3 = threading.Thread(target = fun3)

t1.start()
t2.start()
t3.start()
#endregion
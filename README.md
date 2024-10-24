# OpenCardiographySignalMeasuringDevice

This repository covers the development process of hardware and software and results analysis, for an open-source Cardiography Signal Measuring Device. On this page, you will be able to find all of the CAD files for the 3D printed parts, Gerber files for PCB fabrication, all of the code needed for the project, and test results of the data analysis. If you have any questions or comments, feel free to contact me! The main goal of the project was to be able to record, store, and analyze these signals:

1. Arm Cuff Air Pressure Signals
2. Electrocardiography Signals (ECG)
3. Phonocardiography Signals (Stethoscope)
4. Photoplethysmography Signals (PPG)

Through this project, I wanted to test out different algorithms for measuring blood pressure either by using just the air pressure signals from the arm cuff or those signals in combination with the other measurements, at the bottom of this page, you can take a look at the results. This project was developed as my Master's Thesis project at the University of Belgrade—School of Electrical Engineering (www.etf.bg.ac.rs), under the mentorship of Prof. Nadica Miljković. In the two pictures below you can see how the finished device looks and the design of the graphical interface for controlling the device.

For things like the BOM and the implemented commands, please check this Google Sheet which is updated as soon as something new is added: https://docs.google.com/spreadsheets/d/1H5B5Kw3XJPlpduM7bu2WPejcbya2c3x0Nj9kcexb-uc/edit?usp=sharing

![finishedproject](https://github.com/user-attachments/assets/3d7f81b8-b60e-4c6c-960e-c398776fe47c)

![ThePerfectScreenshot](https://github.com/user-attachments/assets/368944a1-6a58-4c0e-9c11-c1480826d5d4)

## Mechanical Design

The case and all of the necessary components have been 3D printed out of PLA on the Creality K1C, you can find all of the STL files as well as STEP files in the CAD files directory. Since everything was printed on a single-color 3D printer, all of the different colored inlays were glued in during the assembly process. At the back of the device GX12 connectors are used, while there are two additional USB ports, type C for charging, and type B for data (charging currently not validated, more on that later). The case houses the main custom PCB, the 18650 LION battery, and the whole pneumatic setup needed for blood pressure measurement. In the pictures below, you can see the pneumatic setup, as well as how everything is packed inside the case.

![cad_pneumatics](https://github.com/user-attachments/assets/0068a236-9ace-494b-942d-5aa89fd84bef)

![cad_inside1](https://github.com/user-attachments/assets/d5a23c0a-00c2-4006-a3b3-4df7a2ca2e3a)

## Electronics

For electronics, a custom 4-layer PCB has been developed that uses the Raspberry Pi Pico W as the microcontroller for controlling everything. In the electronics directory, you can find the full schematics and also find the Gerber files necessary for manufacturing this PCB. The device is controlled over serial communication, and that is also how the data is sent over to the PC. These are some of the main features of the electronics:

1. Isolated USB communication - The USB data connector is galvanically isolated from the rest of the electronics so that it's safe to use, it will act as a normal USB device when connected to a PC.
2. 3V3 Buck-Boost regulator - Ensures that the device stays operational when the battery voltage drops below 3.3 V.
3. 6V boost regulator - Powering the air pump and air valve for the blood pressure measurement process.
4. Pressure Sensor Amplification - For amplifying the signal from the pressure sensor, an instrumentation INA826 amplifier has been used.
5. Stethoscope Conditioning Signals - The original idea was to use a stethoscope with an AUX output, 3 different circuits are present on the PCB for conditioning the signal so that it can be safely measured with the Pi Pico W ADC. There is a DIP switch for disabling individual circuits.
6. AD8232 ECG - The AD8232 is used for measuring the ECG signals, it was designed according to the datasheet for measuring ECG with 3 electrodes so that the signal can be analyzed for morphology.

The PCB can be powered ON by either using a switch or a button and then latching the EN pin on the buck-boost converter using the Raspberry Pi Pico W. The finished PCB design (V1) is shown in the picture below.

![pcb2d](https://github.com/user-attachments/assets/b3934740-72e7-4d4e-a0ad-a4e98b39c532)

For the sake of proper USB isolation and noise reduction around the switching converters, PCB cutouts, and plane breaks were added where necessary, as can be seen in the pictures below.

![usbiso](https://github.com/user-attachments/assets/1ee0c37c-d08e-4a92-b32e-d6448bd9122e)

![buckboost_layout](https://github.com/user-attachments/assets/b0917c2f-190f-4caa-b961-5bff3c1d4d24)

### ERRORS

If you plan on pursuing this project further, below are the mistakes found during the testing process.
1. The Q6 transistor in schematic 1-Power has been flipped, meaning that the protection circuit is not validated. A quick fix is to solder a wire from BAT- to GND.
2. The isolated power supply was not working as it was supposed to. - Needs further testing.
3. The pinout on the pressure sensor is wrong.

## Software

The software for this project is currently split into three different codes and is written in C++ and Python. You can find all of the codes in the directory Software on this GitHub repo.

1. Raspberry Pi Pico Firmware - C++ - Arduino IDE -  Code that communicates with the PC over serial, controls all actuators and gathers data from the sensors.
2. Graphical Interface - Python - Visual Studio Code - Code that enables easy use of the device and shows all of the measurements in real-time. It also enables users to record all of the data into a CSV file.
3. Data Analysis - Python - Google Colaboratory - Code that analyses all of the data recorded and stored in the CSV directories.

## Testing





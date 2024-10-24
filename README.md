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

The PCB can be powered ON by either using a switch or a button and then latching the EN pin on the buck-boost converter using the Raspberry Pi Pico W. The finished PCB design (V1) is shown in the picture below and below that is the PCB during the testing process.

![pcb2d](https://github.com/user-attachments/assets/b3934740-72e7-4d4e-a0ad-a4e98b39c532)

![PXL_20240524_074411466~2](https://github.com/user-attachments/assets/475f9fa1-d02b-4ce4-ae06-ecb358f0e528)

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

## Additional Hardware

Besides the main device that has been shown above, there are three more things developed that are used with this device. These include the PPG clamp, a custom stethoscope, and an apparatus for calibrating the pressure sensor. If you intend only to measure ECG signals, none of these are needed, however, if you want to measure the air pressure inside the arm cuff, you'll need a way to calibrate the system, for which the apparatus is used. Also, if you want to have PPG or stethoscope measurements, you'll need them as well.

### PPG Clamp

The mechanical parts of the PPG clamp are 3D printed out of PLA as well, and the clamp is made around a MikroElektronika Oxy 5 Click, which interfaces with the system over I2C. While the outside clamp is not necessary, it provides constant pressure of the finger on the sensor, and it also blocks out outside light which helps with having better measurements. The clamp is shown in the picture below.

![ppg_joines](https://github.com/user-attachments/assets/a397b254-113d-4a96-87e0-3dc1f6c6ab3c)

### Stethoscope

The stethoscope that everyone has seen is an analog device that amplifies the sound so that the doctor can listen to different things such as breathing or listen to how the heart is beating. To connect this analog device to the rest of the system, the earphones were removed and a small piezo microphone was inserted into a tube so that it forms an air-tight seal. This microphone was then connected to an amplifier circuit that then goes to the analog pin of our device. The stethoscope is shown in the picture below.

![stethoscope_merged](https://github.com/user-attachments/assets/2669d604-1499-4c28-bb0e-495e3579502d)

### Pressure Sensor Calibration Apparatus

When looking at the pressure sensor datasheet, the main thing we can see is that it has a linear response to the pressure. The problem here is that we are using a potentiometer to adjust the amplification, so we don't know what voltage translates to what pressure (We can always do calculations based on the potentiometer resistance and the INA826 datasheet, but it's more accurate to confirm using a calibration apparatus). This is why the calibration apparatus has been made, it can be seen in the pictures below.

![PXL_20240521_131159092 MV~2](https://github.com/user-attachments/assets/5a342343-4d18-4d1e-a9f0-82be679fcd40)

![PXL_20240521_131219779 MV~2](https://github.com/user-attachments/assets/0cc5a80f-6ffd-4447-9dba-f9c1b239adb5)

The way the apparatus works is by being able to keep a constant pressure in the system that can be adjusted using the two screws pushing the two plungers of the syringes. In the front, there are three air pressure gauges (one is enough, three were used to do cross-validation). We want to use this apparatus by first connecting the apparatus to the pressure sensor on our PCB and then slowly adjusting the potentiometer and the apparatus so that we get to the point where we are reading 3.3 V at 40 kPa (300 mmHg). This ensures that we can cover the whole possible range while measuring blood pressure while also maximizing the capabilities of the ADC on the Pico W. While it would be enough to test in two points since the manufacturer specified a linear response, calibration was done in 40 points to ensure the sensor is working properly. Results of the calibration process are shown below, where the dots show the individual measurements, and the line is estimated using the least mean square method.

![GrafikKalibracije](https://github.com/user-attachments/assets/f93ad959-a090-4e92-8087-e2f8b5380a89)

## Testing Process

The testing was done by comparing the results to a commercially available device. For this, the Wellue BP2 was used since it gives the Mean Arterial Pressure (MAP) measurement, besides the Systolic (SYS), Diastolic (DIA), and heart rate (HR) measurements. The person is supposed to first sit on a chair for at least 5 minutes with legs on the floor. After that, the initial measurement with the commercial device should be conducted. When that is complete, there should be at least a minute between consecutive measurements. For properly measuring the signals, follow the picture below.

![ElectrodePlacement](https://github.com/user-attachments/assets/70e31256-a3b0-45ab-a292-b72a4421442c)

When everything is connected as shown in the picture below, connect the system using a USB cable. In the GUI connect to the device by selecting the proper COM port and setting the baud rate to 115200. After that, enable the signals you want to record, and start the stream. When you want to start recording the measurements, enter the CSV file name and click record. This can be seen in a short demo video below, click on the picture to open the video.

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/Ox0LqK-V76g/0.jpg)](https://www.youtube.com/watch?v=Ox0LqK-V76g)

## Results

In this section, I will showcase the results calculated based on the measurements with the device. Before I start showing graphs, I'll give a short introduction to how blood pressure is measured both manually and automatically. This of course is only considering non-invasive methods, and even in 2024, the gold standard for blood pressure measurement is still the manual approach which includes a regular stethoscope and a hand pump.

### Manual Blood Pressure Measurement

Manual blood pressure measurement takes advantage of what is known as Korotkoff sounds. These are the sounds that can be heard using the stethoscope during the process of measuring blood pressure. This process works by putting an arm cuff above the elbow and starting to inflate it using the hand pump. As the pressure inside the cuff goes up, the cuff squeezes the arm and constricts blood flow through the brachial artery, until the pressure in the cuff goes above the SYS pressure. At that moment, blood circulation is cut off. The doctor measuring blood pressure can recognize this by hearing no sounds on the stethoscope, at that moment, he starts opening a small manual valve to slowly let the air out of the cuff. At the moment that the pressure in the cuff equalizes with the SYS pressure, Korotkoff sounds appear, which present themselves as "banging" noises on the stethoscope. The moment the sounds appear is the moment when we look at the gauge and read the SYS pressure. As the pressure continues to drop in the cuff, the Korotkoff sounds will persist as long as the pressure in the cuff is above the DIA pressure. During this time, the blood flow is turbulent. As the pressure in the cuff falls below the DIA pressure, the blood flow becomes linear and the Korotkoff sounds disappear. This is the moment where we read the DIA pressure on the gauge. This process is illustrated in the picture below, where the blue line represents the air pressure in the cuff, while the red line shows the blood pressure we are measuring.

![ManualBPM](https://github.com/user-attachments/assets/24752d29-4685-4240-a08c-645cf9203214)

### Automatic Blood Pressure Measurement

With the advance of technology, many devices with different algorithms have been developed for measuring blood pressure automatically, and are something that can be found in pretty much every household today. One thing to note here is that these devices work on completely unknown algorithms, and there is no proper way of validating the results they calculate. This is why the manual method is still considered a gold standard in 2024 and also why the criteria for blood pressure monitors is rather low. A blood pressure monitor is considered to be in class A (highest class) if its measurements are in +/- 15 mmHg for the SYS pressure in 85% of the measurements. Considering that if the SYS is 135 mmHg, the device is considered working properly if it's between 120 mmHg and 150 mmHg, this poses a big issue of how trustworthy these devices are.

I'll explain here one of the more well-known algorithms for estimating blood pressure which works by analysing the envelope of the signal. 

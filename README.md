# OpenCardiographySignalMeasuringDevice

**VIDEO OUT WITH DETAILED PROJECT EXPLANATIONS - CHECK BELOW!**

**DISCLAIMER: THIS IS A DEVICE INTENDED SOLELY FOR RESEARCH PURPOSES AND NOT A MEDICAL DEVICE INTENDED FOR CLINICAL OR DIAGNOSIS USE.**

This repository covers the development process of hardware and software and results analysis, for an open-source Cardiography Signal Measuring Device. On this page, you will be able to find all of the CAD files for the 3D printed parts, Gerber files for PCB fabrication, all of the code needed for the project, and test results of the data analysis. If you have any questions or comments, feel free to contact me! The main goal of the project was to be able to record, store, and analyze these signals:

1. Arm Cuff Air Pressure Signals
2. Electrocardiography Signals (ECG)
3. Phonocardiography Signals (Stethoscope)
4. Photoplethysmography Signals (PPG)

Through this project, I wanted to test out different algorithms for measuring blood pressure either by using just the air pressure signals from the arm cuff or those signals in combination with the other measurements, at the bottom of this page, you can take a look at the results. This project was developed as my Master's Thesis project at the University of Belgrade—School of Electrical Engineering (www.etf.bg.ac.rs), under the mentorship of Prof. Nadica Miljković. In the two pictures below you can see how the finished device looks and the design of the graphical interface for controlling the device.

For more detailed explanations about everything from electronics, to 3D printing, to measurements and data analysis, click the thumbnail below to check out the video!

[![Watch the video](https://img.youtube.com/vi/5UgFEHPnKJY/hqdefault.jpg)](https://www.youtube.com/watch?v=5UgFEHPnKJY)

Details and discussion about the project can be found on the Element14 Community: [E14 - CardiographyProject](https://community.element14.com/challenges-projects/element14-presents/project-videos/w/documents/71947/building-an-open-source-blood-pressure-heart-signal-monitor----episode-674?ICID=HP-674-Building-an-Open-Source-Blood-Pressure-Signal-Monitor-JULY25-WF4122160)

For things like the BOM and the implemented commands, please check this Google Sheet which is updated as soon as something new is added: https://docs.google.com/spreadsheets/d/1H5B5Kw3XJPlpduM7bu2WPejcbya2c3x0Nj9kcexb-uc/edit?usp=sharing

The project is featured in the MagPi Magazine issue 150, you can check it out here: https://magpi.raspberrypi.com/issues/150

You can take a look at the CAD models and download them from Printables as well:
1. Main Device: https://www.printables.com/model/1052466-open-cardiography-signal-measuring-device 
2. PPG Clamp: https://www.printables.com/model/1052459-ppg-clamp 

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

The testing was done by comparing the results to a commercially available device. For this, the Wellue BP2 was used since it gives the Mean Arterial Pressure (MAP) measurement, besides the Systolic (SYS), Diastolic (DIA), and heart rate (HR) measurements. The person is supposed to first sit on a chair for at least 5 minutes with legs on the floor. After that, the initial measurement with the commercial device should be conducted. When that is complete, there should be at least a minute between consecutive measurements. To properly measure the signals, follow the picture below.

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

I'll explain here one of the more well-known algorithms for estimating blood pressure which works by analysing the envelope of the signal. To give you a better idea of what I'm talking about, I'll first show you the pressure measurement in the cuff during a blood pressure measurement test, which is shown in the picture below.

![BPM_fig2_PritisakUTokuIspumpavanja](https://github.com/user-attachments/assets/edb67015-6d90-4b62-b7e1-aea8b05a95bd)

The picture above shows only the part of the signal while the arm cuff is deflating. If you take a closer look at the signal, you can see that pulsations start appearing as the pressure decreased, their amplitudes grow, and at one point the amplitude starts going down. This is what we want to analyze but to do that, we need to pass the signal through a high pass filter and detrend the signal. Once we do that, we can estimate an envelope for that signal and continue with the algorithm. The moment in which the envelope reaches its maximum value is the moment in which the air pressure in the cuff is equal to the MAP. Now, according to the algorithm I am using (Sapinsky) we take the value of the MAP amplitude and find the moments in time where the envelope is equal to 40% of MAP and 80% of MAP. These are the moments at which we measure the SYS and DIA pressures. This is illustrated in the picture below.

![AutomaticBPM](https://github.com/user-attachments/assets/ffeb5840-62f6-49e7-a1d0-152e4b1f08b9)

### Signal Analysis

In this section, I'll give a short demonstration of signal analysis on the measurements I recorded during testing. This will include analyzing the data from the arm cuff, PPG, stethoscope, and ECG. The code I used for analyzing this data as well as a data set that was analyzed here can be found in this GitHub repository, so you can play around with the data if you want! At the end of the signal analysis, I'll show how the results hold up to the commercial device.

#### Arm Cuff Pressure Signal

I'll begin by analyzing the arm cuff pressure signal since that was the main focus of my work. First, in the picture below is the signal in the arm cuff during the whole blood pressure measuring procedure. You can see the pressure rising steeply while the pump is turned on, as well as the pressure going down as the cuff slowly deflates with a sudden release at the very end when the electromagnetic valve is triggered.

![BPM_fig1_PritisakUManzetniUTokuMerenja](https://github.com/user-attachments/assets/5363fde4-081a-4c7a-b530-de0fd1c9e5f0)

As mentioned in the algorithm explanation above, we are interested in the part of the signal where the arm cuff is being slowly deflated, as this part of the signal contains the data we are interested in. For this test, the arm cuff was inflated manually to a high pressure, modern devices do a rough estimate of the SYS pressure while inflating the cuff and they inflate it about 30 mmHg above that value and then they start the deflation process. This is done for patient comfort since high pressures can be painful on the arm. In the picture, you can see the part of the signal where the arm cuff is deflating.

![BPM_fig2_PritisakUTokuIspumpavanja](https://github.com/user-attachments/assets/310fdd0b-8ae9-4315-b164-2fd0e11c0c1f)

Before estimating the envelope, we need to filter the signal first. The two pictures below show the signal filtering process, if you're interested in the details about the filter, check the code where you can see the filter type, order, and cut-off frequency.

![BPM_fig8_Detrending](https://github.com/user-attachments/assets/13281cae-77a5-48d1-b97e-b01cec59c660)

![BPM_fig3_PritisakUTokuIspumpavanja-Filtriran](https://github.com/user-attachments/assets/b517456d-27ce-4f35-8acd-59282fc07b37)

Now that the signal has been filtered, we can estimate the envelope of the signal. Besides the envelope, we can find the peaks in the signal which correlate to the heart beats, so we can calculate the heart rate from them.

![BPM_fig5_PritisakUTokuIspumpavanja-Filtriran-Pikovi-Anvelopa](https://github.com/user-attachments/assets/e269a0bf-bc72-417c-9adf-310e1cf658c1)

As you can see from the picture above, the signal is not ideal. We don't have the ideal envelope as expected and as was shown in the drawing above. Nevertheless, this signal can still be used for estimating the SYS and DIA pressures. Before we do that, we need to find the max value of the envelope to find the moments for measuring the SYS and DIA pressures. This is shown in the picture below.

![BPM_fig6_PritisakUTokuIspumpavanja-Filtriran-Pikovi-Anvelopa-SYS-DIA-MAP](https://github.com/user-attachments/assets/868a057b-6a79-49d7-a978-32d2e0f42948)

Using those time moments that we calculated based on the graph in the picture above, we can return to the original pressure signal, and see what was the pressure in the arm cuff in those moments. This is how we calculate the MAP, SYS, and DIA, while we use the peaks for calculating the HR. Below is the picture of that, you can see the final results at the bottom of this section with the comparison.

![BPM_fig7_PritisakUTokuIspumpavanja-SYS-DIA-MAP](https://github.com/user-attachments/assets/e79769bb-91e0-456d-a241-4b57a61d02c2)

#### Stethoscope Signal Analysis

I wanted to use the signal from the stethoscope as an experimental way of estimating the SYS pressure based on the description of how we measure blood pressure using Korotkoff sounds. My idea was to try and see when the pulsations become somewhat regular, or better said when they start matching the heart rhythm and taking the beginning of that as the moment for reading the SYS pressure. In the two pictures below, you can see the signal from the stethoscope recorded at the same time as the air pressure signal above as well as the stethoscope signal during the arm cuff deflation phase.

![AUX_fig1_CeloMerenjePritiska](https://github.com/user-attachments/assets/17796d6d-8121-4c76-9fd7-9a017eb5448e)

![AUX_fig2_Ispumpavanje](https://github.com/user-attachments/assets/130c2d55-15ad-4c34-b0f6-44098bddf6b7)

Here I detected the peaks, and you can see a clear difference from the third peak and how there are no missed pulsations. This is the time moment I wanted to use for the SYS pressure and we can also use those peaks to calculate the HR. 

![AUX_fig3_Ispumpavanje-Vrhovi](https://github.com/user-attachments/assets/f9b699d2-f293-4fad-9cf9-65bb352ac630)

Using the time moment of the third peak, we return to the pressure signal in the arm cuff to read the pressure at that moment.

![AUX_fig5_MerenjeSistolnogPritiska](https://github.com/user-attachments/assets/785828ee-978c-4273-a7fa-b166f86adeb3)

#### PPG Signal Analysis

PPG works by measuring the reflected light at different wavelengths, and based on that signal, we can calculate both the HR and the blood oxygen saturation. For now, I will only look at the signal for measuring the HR, because we can use it really nicely for estimating the DIA pressure. As I've mentioned above when the pressure in the arm cuff is dropping, the blood flow in the arm goes from turbulent to laminar, and the PPG sensor is designed for measurements when the blood flow is laminar. We can see this in the signal by the first flatlining signal, followed by pulsations as the laminar blood flow returns to the arm. In the two pictures below, you can see the PPG signal from the whole measurement and then only from the section where the arm cuff is deflating.

![PPG_fig1_FotopletizmografskiSignalUTokuMerenjaKrvnogPritiska](https://github.com/user-attachments/assets/a34fee89-4184-4ea3-97cf-27d64e998c86)

![PPG_fig2_FotopletizmografskiSignalUTokuIspumpavanjaManzetne](https://github.com/user-attachments/assets/d5800a85-d2e2-47a1-b832-5798001e40a8)

I then passed the signal through a filter in the same way I did with the pressure signal shown above. So the two pictures below show the signal filtering process.

![PPG_fig6_Detrending](https://github.com/user-attachments/assets/d3823d6c-d476-4dfe-94c9-522e364e0526)

![PPG_fig3_FiltriranPPGSignal](https://github.com/user-attachments/assets/70c069b3-11d8-4c3d-a84e-83fa14bc6e08)

What we want to do now is find the peaks in the signal to find the moment when the pulsations appear again. This is the moment we will use to measure the DIA pressure. This is shown in the pictures below.

![PPG_fig4_FiltriranPPGSignal-Vrhovi](https://github.com/user-attachments/assets/e2acf14b-1d3c-451e-8a21-f4086f1bf892)

![PPG_fig5_PPG-IzmerenDijastolniPritisak](https://github.com/user-attachments/assets/65913a88-d0f6-488b-b91d-069b91505ccf)

#### ECG Signal Analysis

In the end, we have the ECG signal. While there is some experimental work for measuring blood pressure by measuring the time delay between R peaks in the ECG signal and the pulsations on the PPG, I will only use the ECG to validate the HR measurement of the other methods and show the morphology of a recorded heartbeat. A section of the measurement is shown in the picture below.

![ECG_fig2_EKG_DeoMerenja](https://github.com/user-attachments/assets/446184a1-a563-4384-9586-4103bc573527)

By detecting the R peaks, we can easily calculate the HR. We can also use that data from ECG to analyze heart rate variability which is a topic I won't be getting into here. But you can see the time between heartbeats in the picture below.

![ECG_fig3_EKG_HRV](https://github.com/user-attachments/assets/b12a4b75-b067-488c-b454-e41e8de237a5)

And in the end, you can see a single heartbeat that was extracted from the measurement.

![ECG_fig4_EKG_JedanOtkucaj](https://github.com/user-attachments/assets/16c3c4b9-9f44-4418-aea6-440927cfe108)

### Final Results

Before showing you the final results from the signal analysis, let's take a look at the measurement done with the Wellue BP2 Blood Pressure monitor. Its results are shown in the picture below.

![Screenshot_20240812-110924](https://github.com/user-attachments/assets/c944af50-86e1-464f-b8f0-904b45fe2380)

Now, let's compare that to the results we estimated from our measurements, this is shown in the table below.

| | Mean Arterial Pressure (MAP) [mmHg] | Systolic Pressure (SYS) [mmHg]  | Diastolic Pressure (DIA) [mmHg] | Heart Rate (HR) [BPM] |
| ------------- | ------------- | ------------- | ------------- | ------------- |
| Wellue BP2 | 93 | 130 | 72 | 81 |
| Arm Cuff Air Pressure | 91 | 132 | 79 | 78 |
| Stethoscope | X | 143 | X | 80 |
| PPG | X | X | 75 | 80 |
| ECG | X | X | X | 80 |

As you can see from the table, the results obtained from the data analysis are pretty good when compared to the commercial device. This is of course one data set and all of this requires much more testing, but it's still rewarding to see promising results. Estimating the SYS pressure using the stethoscope didn't give the best estimation, but this needs more experimenting with things like stethoscope placement, pressure, and so on. One thing that gave really good results was the PPG estimation of the DIA pressure, it's more spot-on than the analysis of the pressure in the arm cuff.

If you have any comments or questions about anything you've seen here, feel free to write to me! Some of the pictures have writing in Serbian but the graphs should be clear based on the units, if you're still struggling with any of that, feel free to contact me!

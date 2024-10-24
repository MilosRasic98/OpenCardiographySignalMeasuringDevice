// Function for decoding the Serial message coming from the user
void DecodeSerialMessage(String msg)
{
  // First we check the type of command that is being sent to the Soft Robot
  // For a full list of commands please check: https://docs.google.com/spreadsheets/d/1j4l9SDbZnH_yYO-BC3xJZ4RkYJjM1L0_M2_zAHDFm0k/edit?usp=sharing

  // Command 0 [C0] - Stop all
  // Command format:      C0
  // Command example:     C0
  // Command description: When driver receives this command, it stops all motors and changed the LED-s from GREEN to RED
  // This is the only command that will be executed immediatelly here
  if (msg.startsWith("C0") == true)
  {
    sprintln("Received command C0 to turn OFF the device");
    // Update the flag to disable all of the LEDs
    led_disable     = true;
    // Turn OFF all of the LEDs before turning OFF the device
    LED_OFF();
    // This is the case where we turn OFF the device
    // Update the flag for the power latch pin
    flag_pwr_latch  = false;
    // Update the flag for updating the digital pins
    flag_pin_cng    = true;
    return;
  }

  // Command 1 [C1] - Enable / Disable 6V Boost Converter
  // Command format:      C1 1/0
  // Command example:     C1 1
  // Command description: Enable or Disable the Boost Converter responsible for the 6V rail
  if (msg.startsWith("C1 ") == true)
  {
    sprintln("INFO - Received command C1.");
    // We need to check whether we need to enable or disable the boost converter
    if (msg.startsWith("C1 1") == true)
    {
      // This is the case where we enable the boost converter
      if (flag_en_6V == true)
      {
        sprintln("WARNING - The boost converter is already enabled.");
        return;
      }
      flag_en_6V = true;
      flag_pin_cng = true;
      sprintln("SUCCESS - The boost converter is enabled.");
      return;
    }
    else if (msg.startsWith("C1 0") == true)
    {
      // This is the case where we disable the boost converter
      if (flag_en_6V == false)
      {
        sprintln("WARNING - The boost converter is already disabled.");
        return;
      }
      flag_en_6V = false;
      flag_pin_cng = true;
      sprintln("SUCCESS - The boost converter is disabled.");
      // If the 6V rail gets disabled, make sure to set all of the relevant duty cycles/outputs to 0
      bpm_pump_duty = 0;
      bpm_valve     = 0;
      //TODO BUZZER
      return;
    }
    // If we're here, that means that the command was sent properly
    sprintln("ERROR - Command C1 was sent with a bad argument, double check the code.");
    return;
  }

  // Command 2 [C2] - Manual Pump Control
  // Command format:      C1 X
  // Command example:     C1 60
  // Command description: Control the pump with a set PWM duty cycle if the 6V power rail is enabled
  if (msg.startsWith("C2 ") == true)
  {
    sprintln("INFO - Received command C2.");

    // To update the duty cycle, first the 6V rail needs to be enabled
    if (flag_en_6V == false)
    {
      sprintln("ERROR - C2 command error - Can't change BPM pump duty cycle, 6V rail not enabled.");
      return;
    }

    // Parsing the value from the Serial message
    int new_duty = msg.substring(3).toInt();

    // Check if the data is correct
    if (bpm_pump_duty == -1)
    {
      sprintln("ERROR - C2 command error - A number was not provided for the duty cycle");
      return;
    }

    if (bpm_pump_duty > BPM_MAX_PUMP_DUTY)
    {
      sprintln("ERROR - C2 command error - BPM pump duty cycle value too large.");
      return;
    }
    
    if (bpm_pump_duty < BPM_MIN_PUMP_DUTY)
    {
      sprintln("ERROR - C2 command error - BPM pump duty cycle value too small.");
      return;
    }

    // Set the flags so the PWM updates
    bpm_pump_duty = new_duty;
    flag_pin_cng = true;
    return;
  }

  // Command 3 [C3] - Open / Close Valve
  // Command format:      C3 1/0
  // Command example:     C3 1
  // Command description: Open or close the valve
  if (msg.startsWith("C3 ") == true)
  {
    sprintln("INFO - Received command C3.");
    // We need to check whether we need to open or close the valve
    if (msg.startsWith("C3 1") == true)
    {
      // This is the case where we open the valve
      if (bpm_valve == 1)
      {
        sprintln("WARNING - The valve is already open.");
        return;
      }
      bpm_valve = 1;
      flag_pin_cng = true;
      sprintln("SUCCESS - The valve is open.");
      return;
    }
    else if (msg.startsWith("C3 0") == true)
    {
      // This is the case where we close the valve
      if (bpm_valve == 0)
      {
        sprintln("WARNING - The valve is already closed.");
        return;
      }
      bpm_valve = 0;
      flag_pin_cng = true;
      sprintln("SUCCESS - The valve is closed.");
      return;
    }
    // If we're here, that means that the command was sent properly
    sprintln("ERROR - Command C3 was sent with a bad argument, double check the code.");
    return;
  }


  // Command 4 [C4] - ON / OFF Optocoupler
  // Command format:      C4 1/0
  // Command example:     C4 1
  // Command description: Turn ON or OFF the optocoupler
  if (msg.startsWith("C4 ") == true)
  {
    sprintln("INFO - Received command C4.");
    // We need to check whether we need to open or close the valve
    if (msg.startsWith("C4 1") == true)
    {
      // This is the case where we open the valve
      if (bpm_opto == 1)
      {
        sprintln("WARNING - The optocoupler is already ON.");
        return;
      }
      bpm_opto = 1;
      flag_pin_cng = true;
      sprintln("SUCCESS - The optocoupler is ON.");
      return;
    }
    else if (msg.startsWith("C4 0") == true)
    {
      // This is the case where we close the valve
      if (bpm_opto == 0)
      {
        sprintln("WARNING - The optocoupler is already OFF.");
        return;
      }
      bpm_opto = 0;
      flag_pin_cng = true;
      sprintln("SUCCESS - The optocoupler is OFF.");
      return;
    }
    // If we're here, that means that the command was sent properly
    sprintln("ERROR - Command C4 was sent with a bad argument, double check the code.");
    return;
  }


  // Command 5 [C5] - Manual Buzzer Control
  // Command format:      C5 X
  // Command example:     C5 60
  // Command description: Control the buzzer with a set PWM duty cycle if the 6V power rail is enabled
  if (msg.startsWith("C5 ") == true)
  {
    sprintln("INFO - Received command C5.");

    // To update the duty cycle, first the 6V rail needs to be enabled
    if (flag_en_6V == false)
    {
      sprintln("ERROR - C5 command error - Can't change Buzzer duty cycle, 6V rail not enabled.");
      return;
    }

    // Parsing the value from the Serial message
    int new_duty = msg.substring(3).toInt();

    // Check if the data is correct
    if (buzz_duty == -1)
    {
      sprintln("ERROR - C5 command error - A number was not provided for the duty cycle");
      return;
    }

    if (buzz_duty > AUX_MAX_BUZZ_DUTY)
    {
      sprintln("ERROR - C5 command error - Buzzer duty cycle value too large.");
      return;
    }
    
    if (buzz_duty < AUX_MIN_BUZZ_DUTY)
    {
      sprintln("ERROR - C5 command error - Buzzer duty cycle value too small.");
      return;
    }

    // Set the flags so the PWM updates
    buzz_duty = new_duty;
    flag_pin_cng = true;
    return;
  }

  // Command 6 [C6] - ON / OFF ECG
  // Command format:      C6 1/0
  // Command example:     C6 1
  // Command description: Turn ON or OFF the ECG chip
  if (msg.startsWith("C6 ") == true)
  {
    sprintln("INFO - Received command C6.");
    // We need to check whether we need to turn ON or OFF the ECG chip
    if (msg.startsWith("C6 1") == true)
    {
      // This is the case where we turn ON the ECG chip
      if (flag_en_ecg == true)
      {
        sprintln("WARNING - The ECG is already ON.");
        return;
      }
      flag_en_ecg = 1;
      flag_pin_cng = true;
      LED_control(5, 0, 10, 0);
      sprintln("SUCCESS - The ECG is ON.");
      return;
    }
    else if (msg.startsWith("C6 0") == true)
    {
      // This is the case where we close the valve
      if (flag_en_ecg == 0)
      {
        sprintln("WARNING - The ECG is already OFF.");
        return;
      }
      flag_en_ecg = 0;
      flag_pin_cng = true;
      LED_control(5, 0, 0, 0);
      ecg_lp = -1;
      ecg_ln = -1;
      sprintln("SUCCESS - The ECG is OFF.");
      return;
    }
    // If we're here, that means that the command was sent properly
    sprintln("ERROR - Command C6 was sent with a bad argument, double check the code.");
    return;
  }

  // Command 7 [C7] - ON / OFF DataStream
  // Command format:      C7 1/0
  // Command example:     C7 1
  // Command description: Turn ON or OFF the DataStream
  if (msg.startsWith("C7 ") == true)
  {
    sprintln("INFO - Received command C7.");
    // We need to check whether we need to turn ON or OFF the DataStream
    if (msg.startsWith("C7 1") == true)
    {
      // This is the case where we turn ON the DataStream
      if (data_stream == true)
      {
        sprintln("WARNING - The DataStream is already ON.");
        return;
      }
      data_stream = true;
      sprintln("SUCCESS - The DataStream is ON.");
      return;
    }
    else if (msg.startsWith("C7 0") == true)
    {
      // This is the case where we close the DataStream
      if (data_stream == false)
      {
        sprintln("WARNING - The DataStream is already OFF.");
        return;
      }
      data_stream = false;
      sprintln("SUCCESS - The DataStream is OFF.");
      return;
    }
    // If we're here, that means that the command was sent properly
    sprintln("ERROR - Command C7 was sent with a bad argument, double check the code.");
    return;
  }

  // Command 10 [C10] - Beep Command
  // Command format:      C10 X
  // Command example:     C10 100
  // Command description: Beep of certain length using the buzzer
  if (msg.startsWith("C10 ") == true)
  {
    sprintln("INFO - Received command C10.");

    // To beep the buzzer, first the 6V rail needs to be enabled
    if (flag_en_6V == false)
    {
      sprintln("ERROR - C10 command error - Can't change Buzzer duty cycle, 6V rail not enabled.");
      return;
    }

    // Parsing the value from the Serial message
    int new_beep = msg.substring(3).toInt();

    // Check if the data is correct
    if (new_beep == -1)
    {
      sprintln("ERROR - C10 command error - A number was not provided for the duty cycle");
      return;
    }

    if (new_beep > AUX_BUZZ_BEEP_MAX)
    {
      sprintln("ERROR - C10 command error - Beep length too long.");
      return;
    }
    
    if (new_beep < AUX_BUZZ_BEEP_MIN)
    {
      sprintln("ERROR - C10 command error - Beep length too short.");
      return;
    }

    // Set the flags so the beep starts
    beep_flag = true;
    beep_length = new_beep;
    beep_start = millis();
    return;
  }

  // Command 11 [C11] - ON / OFF SpO2
  // Command format:      C11 1/0
  // Command example:     C11 1
  // Command description: Turn ON or OFF the AUX
  if (msg.startsWith("C11 ") == true)
  {
    sprintln("INFO - Received command C11.");
    // We need to check whether we need to turn ON or OFF the MAX30102
    if (msg.startsWith("C11 1") == true)
    {
      // This is the case where we turn ON the SpO2 Sensor
      if (spo2_active == true)
      {
        sprintln("WARNING - The SpO2 sensor is already ON.");
        return;
      }
      spo2_active = PPG_SENSOR();
      if (spo2_active == true)
      {
        sprintln("SUCCESS - The SpO2 sensor is ON.");
        LED_control(8, 0, 10, 0);
        return;
      }
      else
      {
        sprintln("ERROR - The SpO2 sensor couldn't be found.");
        LED_control(8, 10, 0, 0);
        return;
      }
    }
    else if (msg.startsWith("C11 0") == true)
    {
      // This is the case where we close the SpO2 Sensor
      if (spo2_active == false)
      {
        sprintln("WARNING - The SpO2 sensor is already OFF.");
        LED_control(8, 0, 0, 0);
        return;
      }
      spo2_active = false;
      sprintln("SUCCESS - The SpO2 sensor is OFF.");
      LED_control(8, 0, 0, 0);
      return;
    }
    // If we're here, that means that the command was sent properly
    sprintln("ERROR - Command C11 was sent with a bad argument, double check the code.");
    return;
  }

  // Command 12 [C12] - ON / OFF AUX
  // Command format:      C12 1/0
  // Command example:     C12 1
  // Command description: Turn ON or OFF the AUX
  if (msg.startsWith("C12 ") == true)
  {
    sprintln("INFO - Received command C12.");
    // We need to check whether we need to turn ON or OFF the SpO2 Sensor
    if (msg.startsWith("C12 1") == true)
    {
      // This is the case where we turn ON the SpO2 Sensor
      if (aux_enable == true)
      {
        sprintln("WARNING - The AUX is already ON.");
        return;
      }
      aux_enable = true;
      sprintln("SUCCESS - AUX Turned ON.");
      return;
    }
    else if (msg.startsWith("C12 0") == true)
    {
      // This is the case where we stop the AUX readings
      if (aux_enable == false)
      {
        sprintln("WARNING - The AUX is already OFF.");
        return;
      }
      aux_enable = false;
      sprintln("SUCCESS - The AUX is OFF.");
      return;
    }
    // If we're here, that means that the command was sent properly
    sprintln("ERROR - Command C12 was sent with a bad argument, double check the code.");
    return;
  }

  // Command 13 [C13] - ON / OFF BPM
  // Command format:      C13 1/0
  // Command example:     C13 1
  // Command description: Turn ON or OFF the BPM
  if (msg.startsWith("C13 ") == true)
  {
    sprintln("INFO - Received command C13.");
    // We need to check whether we need to turn ON or OFF the BPM
    if (msg.startsWith("C13 1") == true)
    {
      // This is the case where we turn ON the SpO2 Sensor
      if (bpm_enable == true)
      {
        sprintln("WARNING - The BPM is already ON.");
        return;
      }
      bpm_enable = true;
      sprintln("SUCCESS - BPM Turned ON.");
      return;
    }
    else if (msg.startsWith("C13 0") == true)
    {
      // This is the case where we stop the AUX readings
      if (bpm_enable == false)
      {
        sprintln("WARNING - The BPM is already OFF.");
        return;
      }
      bpm_enable = false;
      sprintln("SUCCESS - The BPM is OFF.");
      return;
    }
    // If we're here, that means that the command was sent properly
    sprintln("ERROR - Command C13 was sent with a bad argument, double check the code.");
    return;
  }

  // Command 14 [C11] - Check Battery Level
  // Command format:      C14
  // Command example:     C14
  // Command description: Print out battery voltage
  if (msg.startsWith("C14 ") == true)
  {
    sprintln("INFO - Received command C14.");
    Serial.print("The measured battery votlage is: ");
    Serial.print(battery_voltage);
    Serial.println("V");
    return;
  }

  sprintln("ERROR - This command is not configured yet");
}

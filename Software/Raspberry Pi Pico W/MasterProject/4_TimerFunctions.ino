/*
 *      LED TIMER 
 */
bool LEDHandler(struct repeating_timer *t)
{
  (void) t;
  // Normal operation LED should be 1 second ON 1 second OFF
  // In error state, the frequency should go to 5Hz

  // Increment the LED counter
  led_counter++;

  // Check in what state we are
  if (error_state == false)
  {
    // This is the normal state
    if (led_counter >= LED_TICKS)
    {
      // Reset the counter
      led_counter = 0;
      // Toggle the LED (or LEDs)
      ToggleLED();
    }
  }
  else
  {
    // This is the error state
    if (led_counter >= LED_TICKS_ERROR)
    {
      // Reset the counter
      led_counter = 0;
      // Toggle the LED (or LEDs)
      ToggleLED();
    }
  }

  if (beep_flag == true)
  {
    // Change the duty cycle to AUX_BUZZ_BEEP_DUTY if were in the beep timeframe and the duty is at 0%
    if (millis() - beep_start <= beep_length)
    {
      if (buzz_duty == 0)
      {
        buzz_duty = AUX_BUZZ_BEEP_DUTY;
        flag_pin_cng = true;
      }
    }
    else
    {
      buzz_duty = 0;
      beep_flag = false;
      flag_pin_cng = true;
    }
    
  }


  // Blue button handling
  blue_btn_state = digitalRead(PIN_ENC_BTN);
  // Turning the device OFF
  if (blue_btn_state == false)
  {
    blue_btn_start = millis();
  }
  else if (millis() - blue_btn_start >= PWR_OFF_HOLD)
  {
    // This is the case where we turn OFF the device
    // Update the flag for the power latch pin
    flag_pwr_latch  = false;
    // Update the flag for updating the digital pins
    flag_pin_cng    = true;
    // Update the flag to disable all of the LEDs
    led_disable     = true;
    // Turn OFF all of the LEDs before turning OFF the device
    LED_OFF();
  }

  // Measuring the battery voltage
  // Configuring the MUX pins first
  digitalWrite(PIN_MUX_A, LOW);
  digitalWrite(PIN_MUX_B, HIGH);
  digitalWrite(PIN_MUX_C, LOW);
  battery_voltage = 0.001409912 * analogRead(PIN_AUX_ANALOG);
  // Configure the MUX for the aux analog reading
  digitalWrite(PIN_MUX_A, HIGH);
  digitalWrite(PIN_MUX_B, LOW);
  digitalWrite(PIN_MUX_C, LOW);
  BatteryIndicator(battery_voltage);
  

  
  return true;
  
}

/*
 *      COM TIMER 
 */
bool CommunicationHandler(struct repeating_timer *t)
{
  (void) t;
  
  // Check if there are any commands that need to be executed
  if (flag_new_msg == true)
  {
    // Reset the new message flag
    flag_new_msg = false;
    
    // Print out the received message if the debug mode is enabled
    sprintln(serial_msg);
    
    // Decoding the message based on the table of commands
    DecodeSerialMessage(serial_msg);
    
  }
  else
  {
    CheckSerial();
  }

  // DataStream
  if (data_stream == true)
  {
    // If the flag is set to true, we check what messages we are supposed to send out
    if (UNIFIED_MESSAGE == true)
    {
      /*
       *  Unified message combines all of the high throughput messages such as ADC and PPG readings into a single message
       *  Message will be classified as #9
       *  Format: #9,ECG_ADC,BPM_ADC,AUX_ADC,ECG_TIME,ECG_ID,PPG_IR,PPG_TIME,PPG_ID,PPG_FLAG
       */
       if (flag_adc_msg == true || flag_ppg_msg_ir == true)
       {
        // Reset the flags
        flag_adc_msg    = false;
        flag_ppg_msg_ir = false;
        // Increment the IDs
        message1_id++;
        message2_id++;
        // Construct the message
        stream_msg = "#9," + String(ecg_adc) + "," + String(bpm_adc) + "," + String(aux_adc) + "," + String(ecg_msg_time) + "," + String(message1_id) + "," + String(spo2_ir) + "," + String(spo2_ir_time) + "," + String(message2_id) + "," + String(ppg_msg_ind) + "$";
        if (ppg_msg_ind == 1) ppg_msg_ind = 0;
        // Send the message
        Serial.println(stream_msg);
       }
    }
    else
    {
      // MESSAGE ID #1
      if (flag_adc_msg == true)
      {
        // Reset the flag
        flag_adc_msg = false;
        // Update the counter
        message1_id++;
        // Construct the message
        stream_msg = "#1," + String(ecg_adc) + "," + String(bpm_adc) + "," + String(aux_adc) + "," + String(ecg_msg_time) + "," + String(message1_id) + "$";
        // Send the message
        Serial.println(stream_msg);
      }
  
      // MESSAGE ID #2
      if (flag_ppg_msg_ir == true)
      {
        flag_adc_msg = false;
        // Reset the flag
        flag_ppg_msg_ir = false;
        // Update the counter
        message2_id++;
        // Construct the message
        stream_msg = "#2," + String(spo2_ir) + "," + String(spo2_ir_time) + "," + String(message2_id) + "$";
        // Send the message
        Serial.println(stream_msg);
      }
  
      // MESSAGE ID #3
      if (flag_ppg_msg_o2 == true)
      {
        // Reset the flag
        flag_ppg_msg_o2 = false;
        // Update the counter
        message3_id++;
        // Construct the message
        stream_msg = "#3," + String(spo2_o2) + "," + String(spo2_hr) + "," + String(spo2_o2_time) + "," + String(message3_id) + "$";
        // Send the message
        Serial.println(stream_msg);
      }
    }
    
  }
  else
  {
    // Clear the message
    stream_msg = "";
    // Reset message ID-s
    message_id  = 0;
    message1_id = 0;
    message2_id = 0;
    message3_id = 0;
  }
  
  return true;
  
}


/*
 *      SEN TIMER 
 */
bool SenHandler(struct repeating_timer *t)
{
  (void) t;
  // ECG
  // We read the values only if the ECG is enabled
  if (flag_en_ecg == true)
  {
    ecg_adc = analogRead(PIN_ECG_ANALOG);
  }
  else
  {
    // Set to 0 so that the rest of the program can easily interpret this as ECG not active
    ecg_adc = 0;
  }

  if (aux_enable == true)
  {
    digitalWrite(PIN_MUX_A, HIGH);
    digitalWrite(PIN_MUX_B, LOW);
    digitalWrite(PIN_MUX_C, LOW);
    aux_adc = analogRead(PIN_AUX_ANALOG);
  }
  else
  {
    // Reset the value to 0
    aux_adc = 0;
  }

  if (bpm_enable == true)
  {
    bpm_adc = analogRead(PIN_BPM_ANALOG);
  }
  else
  {
    bpm_adc = 0;
  }

  // If the datastream is enabled, always send over the message #1
  if (data_stream == true && (flag_en_ecg == true || aux_enable == true || bpm_enable == true))
  {
    flag_adc_msg = true;
    ecg_msg_time = millis();
  }
  else
  {
    // If datastream is not enabled, make sure to reset the flag to false
    flag_adc_msg = false;
  }
  return true;
}

/*
 *      PPG TIMER 
 */
bool PPGHandler(struct repeating_timer *t)
{
  (void) t;/*
  if (ppg_in_loop == false)
  {
    // PPG
    // We read the values only if the PPG is enabled
    if (spo2_active == true)
    {
      // First we need to increment the different counters
      spo2_count++;
      spo2_ir_count++;
      // After incrementing the counters, check whether they are overflowing the max values
      
      // SPO2
      if (spo2_count >= PPG_SPO2_COUNT)
      {
        flag_adc_msg = false;
        // Read the values and reset the counter
        spo2_sensor.heartrateAndOxygenSaturation(&spo2_o2, &spo2_o2_valid, &spo2_hr, &spo2_hr_valid);
        spo2_count = 0;
        spo2_ir_count = 0;
        // If the flags aren't showing that the measurements are valid, reset them to 0
        if (spo2_o2_valid == 0) spo2_o2 = 0;
        if (spo2_hr_valid == 0) spo2_hr = 0;
        // If of one of the flags is valid, toggle the send data flag to true and update the read time
        if (spo2_o2_valid == 1 || spo2_hr_valid == 1) 
        {
          flag_ppg_msg_o2 = true;
          spo2_o2_time = millis();
        }
      } // IR
      else if (spo2_ir_count >= PPG_IR_COUNT)
      {
        flag_adc_msg = false;
        // Because one reading is at 100Hz and the other one at 1Hz, don't read them in the same cycle when they align
        spo2_ir = spo2_sensor.getIR();
        // Update the read time
        spo2_ir_time = millis();
        // Update the print flag
        flag_ppg_msg_ir = true;
        ppg_msg_ind = 1;
        // Reset the counters
        spo2_ir_count = 0;
        spo2_count = 0;
      }      
    }
    else
    {
      spo2_ir = 0;
      spo2_o2 = 0;
      spo2_hr = 0;
      // Reset the counters
      spo2_count = 0;
      spo2_ir_count = 0;
      // Reset the print flags
      flag_ppg_msg_ir = false;
      flag_ppg_msg_o2 = false;
    }
  }*/
  return true;
}

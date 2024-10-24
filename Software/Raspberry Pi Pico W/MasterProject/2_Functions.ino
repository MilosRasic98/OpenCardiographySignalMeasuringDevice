void sprint(String msg)
{
  if(SERIAL_DEBUG == true) Serial.print(msg);
  return;
}

// Function for the debug print on the Serial
void sprintln(String msg)
{
  if(SERIAL_DEBUG == true) Serial.println(msg);
  return;
}

// Function for checking if there is any Serial data
void CheckSerial()
{
  if (Serial.available() <= 0) return;
  serial_msg    = "";
  flag_new_msg  = true;
  while (Serial.available() > 0)
  {
    char c = (char)Serial.read();
    if (c != '\n' && c != '\r') serial_msg = serial_msg + c;
  }
  return;
}

//  Function for controlling and updating all of the digital pins on the device
void DigitalPinUpdate()
{
  //  All digital pin control should go through this function
  // Turn OFF the LEDs if the flag_pwr_latch is false
  if (flag_pwr_latch == false) LED_OFF();
  /*
   * Updating the LEDs
  */
  // Pump LED
  // If the duty cycle is above 0 turn ON the LED, if it's zero turn it OFF
    if (bpm_pump_duty == BPM_MIN_PUMP_DUTY || flag_pwr_latch == false)
    {
      LED_control(7, 0, 0, 0);
    }
    else
    {
      LED_control(7, 0, 10, 0);
    }
  // Valve LED
    if (bpm_valve == 0 || flag_pwr_latch == false)
    {
      LED_control(6, 0, 0, 0);
    }
    else
    {
      LED_control(6, 0, 10, 0);
    }
  // Regular Pins
  digitalWrite(PIN_BPM_PWR,   flag_en_6V);
  digitalWrite(PIN_ECG_EN,    flag_en_ecg);
  digitalWrite(PIN_BPM_VALVE, bpm_valve);
  digitalWrite(PIN_BPM_BTN,   bpm_opto);
  digitalWrite(PIN_PWR_LATCH, flag_pwr_latch);
  // PWM Pins
  PWM_Instance[0]->setPWM(PIN_BPM_PUMP, PWM_FREQUENCY, bpm_pump_duty);
  PWM_Instance[1]->setPWM(PIN_BUZZ,     PWM_FREQUENCY, buzz_duty);
  return;
}

//  Function used for toggling the LED (or LEDs) to show the current state of the system (HBEAT LEDs)
void ToggleLED()
{
  // Toggle the flag for the builtin LED
  if (pico_led == 0)
  {
    pico_led = 1;
    // Turn ON the LED if the led_disable flag is false, if not, turn it OFF
    if (led_disable == false) LED_control(2, 0, 10, 0);
    if (led_disable == true)  LED_control(2, 0, 0, 0);
  }
  else
  {
    pico_led = 0;
    LED_control(2, 0, 0, 0);
  }
  // Turn on the flag for updating the pins
  //flag_pin_cng = true;
  return;
}

// Function for starting the MAX30102 sensor
bool PPG_SENSOR()
{
  bool ppg_flag = spo2_sensor.begin();
  if (ppg_flag == true)
  {
    // This is the case where the sensor has started succesfully
    sprintln("SUCCESS - MAX30102 SpO2 sensor started.");
    // If we have succesfully started the sensor, we also need to configure it
    // These are the available parameters
    /*
    Macro definition options in sensor configuration 
    sampleAverage: SAMPLEAVG_1 SAMPLEAVG_2 SAMPLEAVG_4 
                   SAMPLEAVG_8 SAMPLEAVG_16 SAMPLEAVG_32
    ledMode:       MODE_REDONLY  MODE_RED_IR  MODE_MULTILED
    pulseWidth:    PULSEWIDTH_69 PULSEWIDTH_118 PULSEWIDTH_215 PULSEWIDTH_411
    sampleRate:    SAMPLERATE_50 SAMPLERATE_100 SAMPLERATE_200 SAMPLERATE_400
                   SAMPLERATE_800 SAMPLERATE_1000 SAMPLERATE_1600 SAMPLERATE_3200
    adcRange:      ADCRANGE_2048 ADCRANGE_4096 ADCRANGE_8192 ADCRANGE_16384
    */
    spo2_sensor.sensorConfiguration(/*ledBrightness=*/60, /*sampleAverage=*/SAMPLEAVG_2, \
                                  /*ledMode=*/MODE_MULTILED, /*sampleRate=*/SAMPLERATE_3200, \
                                  /*pulseWidth=*/PULSEWIDTH_411, /*adcRange=*/ADCRANGE_16384);
    return true;
  }
  else
  {
    // This is the case where the sensor didn't start succesfully
    sprintln("ERROR - MAX30102 SpO2 sensor starting error.");
    return false;
  }
}

// Function for turning OFF all of the LEDs
void LED_OFF()
{
  // Go through all LEDs and set them to 0
  for (int i = 0; i < NUM_LEDS; i++)
  {
    leds[i] = CRGB(0, 0, 0);
  }
  // Show the LEDs
  FastLED.show();
}

// Function for controlling the LEDs
void LED_control(int led, int r, int g, int b)
{
  /*
   *  LED Legend
   *  Index   -   Name    -     Purpose
   *  0           HBEAT         Detected heartbeats
   *  1           BAT           Battery voltage indicator
   *  2           HW            Indicator for the hardware state
   *  3           LOD-          Leads Off Detection -
   *  4           LOD+          Leads Off Detection +
   *  5           ECG           Indicator for whether the ECG has been enabled or not
   *  6           VALVE         Indicator for showing whether the BPM valve is ON or OFF
   *  7           PUMP          Indicator for showing whether the BPM pump is ON or OFF
   *  8           PPG           Indicator for showing whether the PPG has been enabled or not
   */
  // Before turning ON the LED, check whether the LEDs are enabled or not
  if (led_disable == false)
  {
    leds[led] = CRGB(g, r, b);
    FastLED.show();
  }
}

// Function for controlling the battery LED to show the current charge
void BatteryIndicator(float voltage)
{
  /*
   * Depending on the voltage of the battery we want to change the color of the LED
   * PURPLE - > 4.3V
   * GREEN  - 3.7V - 4.3V
   * YELLOW - 3.3V - 3.7V
   * ORANGE - 3.1V - 3.3V
   * RED    - < 3.1V
   * PURPLE - < 2.7V
   */
   // Check whether the LEDs are enabled or not
   if (led_disable == false)
   {
     if (voltage >= 4.3)
     {
        LED_control(1, 10, 0, 10);
     }
     else if (voltage >= 3.7 && voltage < 4.3)
     {
        LED_control(1, 0, 10, 0);
     }
     else if (voltage >= 3.3 && voltage < 3.7)
     {
        LED_control(1, 10, 10, 0);
     }
     else if (voltage >= 3.1 && voltage < 4.3)
     {
        LED_control(1, 10, 5, 0);
     }
     else if (voltage >= 2.7 && voltage < 3.1)
     {
        LED_control(1, 10, 0, 0);
     }
     else
     {
        LED_control(1, 10, 0, 10);
     }
     FastLED.show();
   }
   else
   {
     LED_control(1, 0, 0, 0);
     FastLED.show();
   }
}

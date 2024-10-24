void setup() {
  // Starting up the Serial Monitor
  Serial.begin(SERIAL_BAUDRATE);
  delay(500);
  Serial.println("Starting the configuration...");
  
  // Setting up the ADC resolution
  analogReadResolution(ADC_RES);

  // Configuring all of the pins
  pinMode(PIN_PWR_BTN,    INPUT);
  pinMode(PIN_PWR_LATCH,  OUTPUT);
  pinMode(PIN_SIG_CHARGE, INPUT);
  pinMode(PIN_MCP_CHARGE, INPUT);
  pinMode(PIN_BPM_PWR,    OUTPUT);
  pinMode(PIN_BPM_BTN,    OUTPUT);
  pinMode(PIN_BPM_PUMP,   OUTPUT);
  pinMode(PIN_BPM_VALVE,  OUTPUT);
  pinMode(PIN_MUX_A,      OUTPUT);
  pinMode(PIN_MUX_B,      OUTPUT);
  pinMode(PIN_MUX_C,      OUTPUT);
  pinMode(PIN_ECG_EN,     OUTPUT);
  pinMode(PIN_NEO_LED,    OUTPUT);
  pinMode(PIN_BUZZ,       OUTPUT);
  pinMode(PIN_ENC_A,      INPUT);
  pinMode(PIN_ENC_B,      INPUT);
  pinMode(PIN_ENC_BTN,    INPUT);
  pinMode(PIN_BPM_ANALOG, INPUT);
  pinMode(PIN_ECG_ANALOG, INPUT);
  pinMode(PIN_AUX_ANALOG, INPUT);

  // Configuring I2C0 Pins
  Wire.setSDA(PIN_I2C0_SDA);
  Wire.setSCL(PIN_I2C0_SCL);

  // Configuring I2C0 Pins
  Wire1.setSDA(PIN_I2C1_SDA);
  Wire1.setSCL(PIN_I2C1_SCL);

  // Default pin states that need to be set
  DigitalPinUpdate();

  // Configuring timers

  // LED Timer (LED) - Frequency set in the Parameters section
  if (TimerLED.attachInterruptInterval(LED_PERIOD, LEDHandler))
  {
    sprint("Starting LED Timer OK, millis() = ");
    sprintln(String(millis()));
    sprint("LED timer frequency: ");
    sprintln(String(LED_FREQUENCY));
    sprint("LED timer period: ");
    sprintln(String(LED_PERIOD));
  }
  else
    sprintln("Can't set LED Timer. Select another freq. or timer");
  
  // COM Timer (Communication) - Frequency set in the Parameters section
  if (TimerCOM.attachInterruptInterval(COMM_PERIOD, CommunicationHandler))
  {
    sprint("Starting COM Timer OK, millis() = ");
    sprintln(String(millis()));
    sprint("COM timer frequency: ");
    sprintln(String(COMM_FREQUENCY));
    sprint("COM timer period: ");
    sprintln(String(COMM_PERIOD));
  }
  else
    sprintln("Can't set COM Timer. Select another freq. or timer");

  // SEN Timer (Sensor) - Frequency set in the Parameters section
  if (TimerSEN.attachInterruptInterval(SEN_PERIOD, SenHandler))
  {
    sprint("Starting SEN Timer OK, millis() = ");
    sprintln(String(millis()));
    sprint("SEN timer frequency: ");
    sprintln(String(SAMPLING_FREQUENCY));
    sprint("SEN timer period: ");
    sprintln(String(SEN_PERIOD));
  }
  else
    sprintln("Can't set COM Timer. Select another freq. or timer");
  /*
  // PPG Timer (PPG) - Frequency set in the Parameters section
  if (TimerPPG.attachInterruptInterval(SEN_PERIOD, PPGHandler))
  {
    sprint("Starting PPG Timer OK, millis() = ");
    sprintln(String(millis()));
    sprint("SEN timer frequency: ");
    sprintln(String(SAMPLING_FREQUENCY));
    sprint("SEN timer period: ");
    sprintln(String(SEN_PERIOD));
  }
  else
    sprintln("Can't set PPG Timer. Select another freq. or timer");*/

  // Setting up PWM
  // BPM Pump
  PWM_Instance[0] = new RP2040_PWM(PIN_BPM_PUMP, PWM_FREQUENCY, 0.00f);
  PWM_Instance[0]->setPWM();
  // Buzzer
  PWM_Instance[1] = new RP2040_PWM(PIN_BUZZ, PWM_FREQUENCY, 0.00f);
  PWM_Instance[1]->setPWM();

  // Configuring the LEDs
  FastLED.addLeds<WS2813, PIN_NEO_LED, RGB>(leds, NUM_LEDS);
  // Turn OFF all of the LEDs in the start
  LED_OFF();

  sprintln("Configuration done, starting the system...");
}

void loop() {
  // TODO - Move this to a timer
  if (flag_pin_cng == true)
  {
    sprintln("INFO - Pin change true");
    flag_pin_cng = false;
    DigitalPinUpdate();
  }
  
  // Leads Detection for the ECG
  if (flag_en_ecg == true)
  {
    // Check the state for the LOD- by switching the MUX
    digitalWrite(PIN_MUX_A, HIGH);
    digitalWrite(PIN_MUX_B, LOW);
    digitalWrite(PIN_MUX_C, HIGH);
    int new_ln = digitalRead(PIN_AUX_ANALOG);
    // Configure the MUX for the aux analog reading
    digitalWrite(PIN_MUX_A, HIGH);
    digitalWrite(PIN_MUX_B, LOW);
    digitalWrite(PIN_MUX_C, LOW);
    if (ecg_ln != new_ln)
    {
      ecg_ln = new_ln;
      // Depending on their state, update the LEDs to be either Red or Green
      // RED    - Leads not connected
      // GREEN  - Leads connected properly
      if (ecg_ln == 1)
      {
        LED_control(3, 0, 10, 0);  
      }
      else
      {
        LED_control(3, 10, 0, 0);
      }
    }
    // Check the state for the LOD+ by switching the MUX
    digitalWrite(PIN_MUX_A, LOW);
    digitalWrite(PIN_MUX_B, LOW);
    digitalWrite(PIN_MUX_C, HIGH);
    int new_lp = digitalRead(PIN_AUX_ANALOG);
    // Configure the MUX for the aux analog reading
    digitalWrite(PIN_MUX_A, HIGH);
    digitalWrite(PIN_MUX_B, LOW);
    digitalWrite(PIN_MUX_C, LOW);
    if (ecg_lp != new_lp)
    {
      ecg_lp = new_lp;
      // Depending on their state, update the LEDs to be either Red or Green
      // RED    - Leads not connected
      // GREEN  - Leads connected properly
      if (ecg_lp == 1)
      {
        LED_control(4, 0, 10, 0);  
      }
      else
      {
        LED_control(4, 10, 0, 0);
      }
    }
    FastLED.show();
  }
  else
  {
    LED_control(3, 0, 0, 0);
    LED_control(4, 0, 0, 0);
    FastLED.show();
  }
  
  if (ppg_in_loop == true)
  {
    // PPG
    // We read the values only if the PPG is enabled
    if (spo2_active == true)
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
  }
}

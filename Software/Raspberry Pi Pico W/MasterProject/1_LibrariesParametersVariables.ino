/*
 *  LIBRARIES
 */
#include <Wire.h>
#include "RPi_Pico_TimerInterrupt.h"
#include "RP2040_PWM.h"
#include <DFRobot_MAX30102.h>
#include <FastLED.h>

/*
 *  PINS
 */
#define PIN_PWR_BTN     2
#define PIN_PWR_LATCH   3
#define PIN_SIG_CHARGE  4
#define PIN_MCP_CHARGE  5
#define PIN_BPM_PWR     6
#define PIN_BPM_BTN     7
#define PIN_BPM_PUMP    8
#define PIN_BPM_VALVE   9
#define PIN_MUX_A       10
#define PIN_MUX_B       11
#define PIN_MUX_C       12
#define PIN_ECG_EN      13
#define PIN_NEO_LED     14
#define PIN_BUZZ        15
#define PIN_ENC_A       16
#define PIN_ENC_B       17
#define PIN_I2C1_SDA    18
#define PIN_I2C1_SCL    19
#define PIN_I2C0_SDA    20
#define PIN_I2C0_SCL    21
#define PIN_ENC_BTN     22
#define PIN_BPM_ANALOG  26
#define PIN_ECG_ANALOG  27
#define PIN_AUX_ANALOG  28


/*
 *  PARAMETERS
 */

// GENERAL PARAMETERS
#define SAMPLING_FREQUENCY    1000      // [Hz]           Sampling frequency for the Pico ADC
#define COMM_FREQUENCY        500       // [Hz]           Communication frequnecy with the PC
#define ADC_RES               12        // [bit]          ADC resolution set in bits 10/12
#define SERIAL_BAUDRATE       115200    // [#]            Serial communication baudrate 9600/115200
#define PWM_FREQUENCY         1000      // [Hz]           PWM signal frequency     
#define SERIAL_DEBUG          true      // [true/false]   Flag that enables/disables serial debugging
#define LED_FREQUENCY         100       // [Hz]           LED timer 0 frequency
#define CON_FREQUENCY         1000      // [Hz]           Control timer 2 frequency
#define LED_TICKS             100       // [#]            Number of timer ticks before changing the LED state in normal state
#define LED_TICKS_ERROR       10        // [#]            Number of timer ticks before changing the LED state in error state
#define UNIFIED_MESSAGE       true      // [true/false]   Flag for sending a unified message over the serial port
#define PWR_OFF_HOLD          5000      // [ms]           Number of miliseconds that the blue buttons needs to be held for to turn off the device
#define NUM_LEDS              9         // [#]            Number of LEDs on the front panel

// BPM PARAMETERS
#define BPM_MAX_PUMP_DUTY     100       // [%]            Max duty cycle of the PWM signal that is controlling the pump for the BPM
#define BPM_MIN_PUMP_DUTY     0         // [%]            Min duty cycle of the PWM signal that is controlling the pump for the BPM

// AUX PARAMETERS
#define AUX_MAX_BUZZ_DUTY     100       // [%]            Max duty cycle of the PWM signal that is controlling the Buzzer
#define AUX_MIN_BUZZ_DUTY     0         // [%]            Min duty cycle of the PWM signal that is controlling the Buzzer
#define AUX_BUZZ_BEEP_DUTY    10        // [%]            Duty cycle used for the regular beeping when for example when it's indicating the pulse
#define AUX_BUZZ_BEEP_MAX     2000      // [ms]           Length of the longest allowed beep for the buzzer
#define AUX_BUZZ_BEEP_MIN     10        // [ms]           Length of the shortest allowed beep for the buzzer

// PPG PARAMETERS
#define PPG_SPO2_FREQUENCY    1         // [Hz]           Reading frequency for the SpO2 
#define PPG_IR_FREQUENCY      20        // [Hz]           Reading frequency for the PPG sensor

// CALCULATED PARAMETERS
#define COMM_PERIOD           1000000 / COMM_FREQUENCY                  // [us]   Number of us needed to achieve the desired frequency
#define LED_PERIOD            1000000 / LED_FREQUENCY                   // [us]   Number of us needed to achieve the desired frequency
#define SEN_PERIOD            1000000 / SAMPLING_FREQUENCY              // [us]   Number of us needed to achieve the desired frequency
#define CON_PERIOD            1000000 / CON_FREQUENCY                   // [us]   Number of us needed to achieve the desired frequency
#define PPG_SPO2_COUNT        SAMPLING_FREQUENCY / PPG_SPO2_FREQUENCY   // [#]    Max count value for the PPG SPO2 reading
#define PPG_IR_COUNT          SAMPLING_FREQUENCY / PPG_IR_FREQUENCY     // [#]    Max count value for the PPG IR reading

/*
 * VARIABLES
 */

// Flags
bool          flag_en_6V      =       true;     // [true/false]   Flag for turning the boost converter ON/OFF
bool          flag_pin_cng    =       false;    // [true/false]   Flag for indicating if a digital pin state change is needed
bool          error_state     =       false;    // [true/false]   Flag that indicates whether we are in an error state or not
bool          flag_pwr_latch  =       true;     // [true/false]   Flag that indicates whether we should keep the Pico W turned ON or not
bool          led_disable     =       false;    // [true/false]   Flag that indicates whether LEDs are disabled or not

// Communication
bool          flag_new_msg    =       false;    // [true/false]   Flag for showing if there is a new message on the Serial port
String        serial_msg      =       "";       // [String]       Variable for storing the message from the Serial port (Commands are received through this message)       
bool          data_stream     =       false;    // [true/false]   Flag for showing if the data stream to the PC is turned ON or OFF
volatile int  message_id      =       0;        // [#]            In the data stream, this will be the parameters used to make sure there aren't any skipped messages
String        stream_msg      =       "";       // [String]       Variable for storing the message for the DataStream
volatile bool flag_adc_msg    =       false;    // [true/false]   Flag for showing whether a new ADC message is scheduled
volatile bool flag_ppg_msg_ir =       false;    // [true/false]   Flag for showing whether a new PPG IR message is scheduled
volatile bool flag_ppg_msg_o2 =       false;    // [true/false]   Flag for showing whether a new PPG SpO2 message is scheduled       
volatile int  message1_id     =       0;        // [#]            Counter for message with ID = 1
volatile int  message2_id     =       0;        // [#]            Counter for message with ID = 2
volatile int  message3_id     =       0;        // [#]            Counter for message with ID = 3

// Blood Pressure Monitor
int           bpm_pump_duty   =       0;        // [%]            Duty cycle that is being sent to the pin connected to the BPM pump
int           bpm_valve       =       0;        // [0/1]          Variable for storing whether the valve is ON or OFF
int           bpm_opto        =       0;        // [0/1]          Variable for storing whether the optocoupler is turned ON or OFF
volatile int  bpm_adc         =       0;        // [ADC]          BPM ADC reading
volatile int  bpm_mmhg        =       0;        // [mmHg]         BPM reading converted to mmHg
bool          bpm_enable      =       false;    // [true/false]   Flag for inticating whether the BPM readings are enabled or not

// ECG
bool          flag_en_ecg     =       false;    // [true/false]   Flag for turning the ECG chip ON/OFF 
volatile int  ecg_adc         =       0;        // [ADC]          Variable for storing the latest ecg value read by the ADC
int           ecg_lp          =       -1;       // [0/1]          ECG LP signal
int           ecg_ln          =       -1;       // [0/1]          ECG LN signal
volatile int  ecg_msg_time    =       0;        // [ms]           ECG signal read time

// AUX
volatile int  aux_adc         =       0;        // [ADC]          ADC reading for the AUX channel
bool          aux_enable      =       false;    // [true/false]   Flag for indicating whether the AUX readings are enabled or disabled

// SpO2
bool          spo2_active     =       false;    // [true/false]   Flag that indicated whether our sensor is active or not
volatile int  spo2_ir         =       0;        // [#]            Variable for storing the IR value read by the MAX30102 sensor
volatile int  spo2_r          =       0;        // [#]            Variable for storing the R value read by the MAX30102 sensor
int32_t       spo2_o2         =       0;        // [#]            Variable for storing the O2 value read by the MAX30102 sensor
int8_t        spo2_o2_valid   =       0;        // [0/1]          Flag that indicates whether the O2 saturation reading is valid 
int32_t       spo2_hr         =       0;        // [#]            Variable for storing the heart rate value calculated by the MAX30102 sensor
int8_t        spo2_hr_valid   =       0;        // [0/1]          Flag that indicates whether the HR calculation is valid
volatile int  spo2_count      =       0;        // [#]            Counter for lowering the read frequency for SpO2 and HR for the MAX30102 sensor
volatile int  spo2_ir_count   =       0;        // [#]            Counter for lowering the read frequenct for IR readings for the MAX30102 sensor         
volatile int  spo2_ir_time    =       0;        // [ms]           Time of reading the IR signal from the MAX30102
volatile int  spo2_o2_time    =       0;        // [ms]           Time of reading the SpO2 values from the MAX30102
volatile int  ppg_msg_ind     =       0;        // [0/1]          Indicator for a new PPG message
bool          ppg_in_loop     =       true;     // [true/false]   Flag for determening whether PPG is handled in a loop or a timer

// Interface
int           buzz_duty       =       0;        // [%]            Duty cycle for controlling the volume of the buzzer
int           beep_start      =       0;        // [ms]           Start of the beep in ms
int           beep_length     =       0;        // [ms]           Length of the beep in ms
bool          beep_flag       =       false;    // [true/false]   Flag indicating whether we have a new beep or not
int           blue_btn_start  =       0;        // [ms]           Start time for when the blue button has been pressed
bool          blue_btn_state  =       false;    // [true/false]   Flag for indicating whether the blue button is pressed or not

// General
volatile int  led_counter     =       0;        // [#]            Used as a counter to keep track of progress with the LED timer
int           pico_led        =       0;        // [0/1]          Variable which shows whether the Pico LED is ON or OFF
float         battery_voltage =       0.00;     // [V]            Variable used for storing the measured votlage of the LION cell

// Testing
bool          plotter         =       false;    // [true/false]   Flag which indicates if the plotter is active for testing purposes

/*
 *      SPO2 SENSOR
 */
DFRobot_MAX30102            spo2_sensor;        // SpO2 Sensor MAX30102

/*
 *      TIMERS 
 */
RPI_PICO_Timer              TimerLED(0);        // Timer for the heartbeat LED                          - Frequency set in setup() - Default 10 Hz
RPI_PICO_Timer              TimerCOM(1);        // Timer for setting the communication rate             - Frequency set in setup() - Default 0.5 kHz
RPI_PICO_Timer              TimerPPG(2);        // Timer for PPG measurements                           - Frequency set in setup() - Default 2 kHz
RPI_PICO_Timer              TimerSEN(3);        // Timer for sensor data acqusition                     - Frequency set in setup() - Default 2 kHz

/*
 *      PWM
 */
RP2040_PWM*                 PWM_Instance[2];    // PWM for the Pico

/*
 *      LED-s
 */
CRGB                        leds[NUM_LEDS];     // LEDs in the front
 

//*******************************************************
// Copyright (c) MLRS project
// GPL3
// https://www.gnu.org/licenses/gpl-3.0.de.html
// OlliW @ www.olliw.eu
//*******************************************************
// hal
//********************************************************

//#define MLRS_FEATURE_DIVERSITY
//#define MLRS_FEATURE_NO_DIVERSITY

//-------------------------------------------------------
// TX DIY DUAL-E22 v010 STM32G431CBT
//-------------------------------------------------------

#define MLRS_FEATURE_NO_DIVERSITY
#define DEVICE_HAS_JRPIN5
#define DEVICE_HAS_COM_ON_USB


#ifdef MLRS_FEATURE_DIVERSITY
  #define DEVICE_HAS_DIVERSITY
#endif
#ifdef MLRS_FEATURE_NO_DIVERSITY
  #undef DEVICE_HAS_DIVERSITY
#endif

#ifdef DEBUG_ENABLED
#undef DEBUG_ENABLED
#endif

//-- Timers, Timing, EEPROM, and such stuff

#define DELAY_USE_DWT

#define SYSTICK_TIMESTEP          1000
#define SYSTICK_DELAY_MS(x)       (uint16_t)(((uint32_t)(x)*(uint32_t)1000)/SYSTICK_TIMESTEP)

#define EE_START_PAGE             60 // 128 kB flash, 2 kB page

#define MICROS_TIMx               TIM3


//-- UARTS
// UARTB = serial port
// UART = output port, SBus or whatever
// UARTC = debug port

#define UARTB_USE_UART3 // serial
#define UARTB_BAUD                RX_SERIAL_BAUDRATE
#define UARTB_USE_TX
#define UARTB_TXBUFSIZE           RX_SERIAL_TXBUFSIZE // 1024 // 512
#define UARTB_USE_TX_ISR
#define UARTB_USE_RX
#define UARTB_RXBUFSIZE           RX_SERIAL_RXBUFSIZE // 1024 // 512

#define UART_USE_UART2 // JR pin5, MBridge
#define UART_BAUD                 400000
#define UART_USE_TX
#define UART_TXBUFSIZE            512
#define UART_USE_TX_ISR
#define UART_USE_RX
#define UART_RXBUFSIZE            512

// used VCP
//#define UARTC_USE_UART1 // debug
//#define UARTC_BAUD                115200
//#define UARTC_USE_TX
//#define UARTC_TXBUFSIZE           512
//#define UARTC_USE_TX_ISR
//#define UARTC_USE_RX
//#define UARTC_RXBUFSIZE           512

//-- SX12xx & SPI

#define SPI_USE_SPI2              // PB13, PB14, PB15
#define SPI_CS_IO                 IO_PA8
#define SPI_USE_CLK_LOW_1EDGE     // datasheet says CPHA = 0  CPOL = 0
#define SPI_USE_CLOCKSPEED_9MHZ

#define SX_RESET                  IO_PB5
#define SX_DIO1                   IO_PB3
#define SX_BUSY                   IO_PB4
#define SX_RX_EN                  IO_PB9
#define SX_TX_EN                  IO_PC13

#define SX_DIO1_SYSCFG_EXTI_PORTx     LL_SYSCFG_EXTI_PORTB
#define SX_DIO1_SYSCFG_EXTI_LINEx     LL_SYSCFG_EXTI_LINE3
#define SX_DIO_EXTI_LINE_x            LL_EXTI_LINE_3
#define SX_DIO_EXTI_IRQn              EXTI3_IRQn
#define SX_DIO_EXTI_IRQHandler        EXTI3_IRQHandler
//#define SX_DIO_EXTI_IRQ_PRIORITY    11

void sx_init_gpio(void)
{
    gpio_init(SX_RESET, IO_MODE_OUTPUT_PP_HIGH, IO_SPEED_VERYFAST);
    gpio_init(SX_DIO1, IO_MODE_INPUT_PD, IO_SPEED_VERYFAST);
    gpio_init(SX_BUSY, IO_MODE_INPUT_PU, IO_SPEED_VERYFAST);
    gpio_init(SX_TX_EN, IO_MODE_OUTPUT_PP_LOW, IO_SPEED_VERYFAST);
    gpio_init(SX_RX_EN, IO_MODE_OUTPUT_PP_LOW, IO_SPEED_VERYFAST);
}

bool sx_busy_read(void)
{
    return (gpio_read_activehigh(SX_BUSY)) ? true : false;
}

void sx_amp_transmit(void)
{
    gpio_low(SX_RX_EN);
    gpio_high(SX_TX_EN);
}

void sx_amp_receive(void)
{
    gpio_low(SX_TX_EN);
    gpio_high(SX_RX_EN);
}

void sx_dio_init_exti_isroff(void)
{
    LL_SYSCFG_SetEXTISource(SX_DIO1_SYSCFG_EXTI_PORTx, SX_DIO1_SYSCFG_EXTI_LINEx);

    // let's not use LL_EXTI_Init(), but let's do it by hand, is easier to allow enabling isr later
    LL_EXTI_DisableEvent_0_31(SX_DIO_EXTI_LINE_x);
    LL_EXTI_DisableIT_0_31(SX_DIO_EXTI_LINE_x);
    LL_EXTI_DisableFallingTrig_0_31(SX_DIO_EXTI_LINE_x);
    LL_EXTI_EnableRisingTrig_0_31(SX_DIO_EXTI_LINE_x);

    NVIC_SetPriority(SX_DIO_EXTI_IRQn, SX_DIO_EXTI_IRQ_PRIORITY);
    NVIC_EnableIRQ(SX_DIO_EXTI_IRQn);
}

void sx_dio_enable_exti_isr(void)
{
    LL_EXTI_ClearFlag_0_31(SX_DIO_EXTI_LINE_x);
    LL_EXTI_EnableIT_0_31(SX_DIO_EXTI_LINE_x);
}

void sx_dio_exti_isr_clearflag(void)
{
    LL_EXTI_ClearFlag_0_31(SX_DIO_EXTI_LINE_x);
}


//-- Button

#define BUTTON                    IO_PA4

void button_init(void)
{
    gpio_init(BUTTON, IO_MODE_INPUT_PU, IO_SPEED_DEFAULT);
}

bool button_pressed(void)
{
    return gpio_read_activelow(BUTTON);
}


//-- LEDs

#define LED_GREEN               IO_PB0
#define LED_RED                 IO_PB12

void leds_init(void)
{
    gpio_init(LED_GREEN, IO_MODE_OUTPUT_PP_LOW, IO_SPEED_DEFAULT);
    gpio_init(LED_RED, IO_MODE_OUTPUT_PP_LOW, IO_SPEED_DEFAULT);
    gpio_low(LED_GREEN); // LED_GREEN_OFF
    gpio_low(LED_RED); // LED_RED_OFF
}

void led_green_off(void) { gpio_low(LED_GREEN); }
void led_green_on(void) { gpio_high(LED_GREEN); }
void led_green_toggle(void) { gpio_toggle(LED_GREEN); }

void led_red_off(void) { gpio_low(LED_RED); }
void led_red_on(void) { gpio_high(LED_RED); }
void led_red_toggle(void) { gpio_toggle(LED_RED); }


//-- POWER

#define POWER_GAIN_DBM            27 // gain of a PA stage if present
#define POWER_SX126X_MAX_DBM      0 // maximum allowed sx power
#define POWER_USE_DEFAULT_RFPOWER_CALC

#define RFPOWER_DEFAULT           0 // index into rfpower_list array

const rfpower_t rfpower_list[] = {
    { .dbm = POWER_MIN, .mW = INT8_MIN },
    { .dbm = POWER_10_DBM, .mW = 10 },
    { .dbm = POWER_20_DBM, .mW = 100 },
    { .dbm = POWER_24_DBM, .mW = 250 },
    { .dbm = POWER_27_DBM, .mW = 500 },
};


//-- TEST

uint32_t porta[] = {
    LL_GPIO_PIN_0, LL_GPIO_PIN_1, LL_GPIO_PIN_2, LL_GPIO_PIN_3, LL_GPIO_PIN_4, LL_GPIO_PIN_5, LL_GPIO_PIN_6, LL_GPIO_PIN_7,
    LL_GPIO_PIN_8, LL_GPIO_PIN_9, LL_GPIO_PIN_10, LL_GPIO_PIN_15,
};

uint32_t portb[] = {
    LL_GPIO_PIN_0, LL_GPIO_PIN_1, LL_GPIO_PIN_3, LL_GPIO_PIN_4, LL_GPIO_PIN_5, LL_GPIO_PIN_6, LL_GPIO_PIN_7,
    LL_GPIO_PIN_8, LL_GPIO_PIN_9, LL_GPIO_PIN_10, LL_GPIO_PIN_11,
    LL_GPIO_PIN_12, LL_GPIO_PIN_13, LL_GPIO_PIN_14, LL_GPIO_PIN_15,
};

uint32_t portc[] = {
    LL_GPIO_PIN_13, LL_GPIO_PIN_14, LL_GPIO_PIN_15,
};





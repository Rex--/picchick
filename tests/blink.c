#include <xc.h>

/* PIC18F25Q10
#define _XTAL_FREQ 1000000

#pragma config FEXTOSC = OFF, RSTOSC = HFINTOSC_1MHZ, FCMEN = OFF
#pragma config PWRTE = ON, LPBOREN = OFF, BOREN = OFF, ZCD = OFF, PPS1WAY = OFF, STVREN = OFF, XINST = OFF
#pragma config WDTE = OFF, WDTCWS = WDTCWS_7, WDTCCS = SC
#pragma config CLKOUTEN = ON

#define LED_PIN 0b11111111
#define LED_TRIS TRISB
#define LED_ANSEL ANSELB
#define LED_PORT PORTB
*/

/* PIC16F1454
#define _XTAL_FREQ 500000

#pragma config FOSC = INTOSC, WDTE = OFF, PWRTE = ON, MCLRE = ON, CP = OFF, BOREN = OFF, CLKOUTEN = ON, IESO = OFF, FCMEN = OFF
#pragma config WRT = OFF, CPUDIV = NOCLKDIV, USBLSCLK = 24MHz, PLLMULT = 4x, PLLEN = DISABLED, STVREN = OFF, BORV = HI, LPBOR = OFF, LVP = ON

#define LED_PIN 0b00100000
#define LED_TRIS TRISA
#define LED_ANSEL ANSELA
#define LED_PORT PORTA
*/

/* PIC16(L)F19197
#define _XTAL_FREQ 1000000

#pragma config FCMEN = OFF, CSWEN = OFF, LCDPEN = OFF, VBATEN = OFF, CLKOUTEN = ON, RSTOSC = HFINT1, FEXTOSC = OFF
#pragma config DEBUG = OFF, STVREN = OFF, PPS1WAY = OFF, ZCD = OFF, BORV = HI, BOREN = OFF, LPBOREN = OFF, PWRTS = PWRT_64, MCLRE = ON
#pragma config WDTCPS = WDTCPS_0, WDTE = OFF, WDTCWS = WDTCWS_0, WDTCCS = SC 
#pragma config BBSIZE = 512, BBEN = OFF, SAFEN = OFF, WRTAPP = OFF, WRTB = OFF, WRTC = OFF, WRTD = OFF, WRTSAF = OFF, LVP = ON
#pragma config CP = OFF

#define LED_PIN 0b10000000
#define LED_TRIS TRISG
#define LED_ANSEL ANSELG
#define LED_PORT PORTG
*/


void
main (void)
{
    // Set LED pin to digital output
    LED_ANSEL &= ~(LED_PIN);
    LED_TRIS &=  ~(LED_PIN);
    
    while (1)
    {
        // Turn LED on
        LED_PORT |= LED_PIN;

        // Wait for a bit
        __delay_ms(500);

        // Turn LED off
        LED_PORT &= ~(LED_PIN);

        // Wait for a bit
        __delay_ms(500);
    }
}

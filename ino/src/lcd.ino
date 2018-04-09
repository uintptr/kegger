#include <DHT.h>
#include <HX711.h>

#define DHT_PIN                 2
#define SCALE_DOUT              3
#define SCALE_CLOCK             4


#define LOOP_GRANULARITY_MS     1000
#define DHT_SAMPLE_MS           2000

#define SCALE_CALIBRATION       -12600.00

DHT     dht(DHT_PIN, DHT11);
HX711   scale(SCALE_DOUT, SCALE_CLOCK);

static int32_t  g_nDHTSample = 0;
static float    g_nTemp      = 0;
static float    g_nHumidity  = 0;

void setup()
{
    Serial.begin (9600);
    scale.set_scale();
    scale.tare();   //Reset the scale to 0
}

void loop()
{
    int     nTemperature    = 0;
    int     nHumidity       = 0;
    char    aLine [ 100 ]   = { 0 };

    scale.set_scale( SCALE_CALIBRATION );

    if ( g_nDHTSample <= 0 )
    {
        g_nTemp     = dht.readTemperature();
        g_nHumidity = dht.readHumidity();

        //
        // Skip a few cycles
        //
        g_nDHTSample = DHT_SAMPLE_MS;
    }

    //
    // CSV to make it easy to read off the serial line
    //
    // snprintf() doesn't seem to handle floating points very well
    //
    snprintf(   aLine,
                sizeof(aLine),
                "%d,%d",
                ( int ) g_nTemp,
                ( int ) g_nHumidity );

    Serial.println( aLine );

    Serial.print   ( "read: " );
    Serial.println ( scale.get_units(20) + 5 );

    scale.power_down();

    delay(LOOP_GRANULARITY_MS);

    scale.power_up();

    g_nDHTSample -= DHT_SAMPLE_MS;
}

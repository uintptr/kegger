#include <DHT.h>
#include <HX711.h>

#define DHT_PIN                 2
#define SCALE_DOUT              3
#define SCALE_CLOCK             4

#define LOOP_GRANULARITY_MS     1000
#define SCALE_SAMPLE_SIZE       20

static DHT      dht(DHT_PIN, DHT11);
static HX711    scale(SCALE_DOUT, SCALE_CLOCK);

static float    g_fTemperature;
static float    g_fHumidity;
static float    g_fWeight;

void setup()
{
    Serial.begin (9600);

    scale.set_scale();

    g_fTemperature  = 0;
    g_fHumidity     = 0;
    g_fWeight       = 0;
}

void loop()
{
    g_fTemperature  = dht.readTemperature();
    g_fHumidity     = dht.readHumidity();

    scale.power_up();

    g_fWeight = scale.read_average(SCALE_SAMPLE_SIZE);

    scale.power_down();

    //
    // Have to cast and compare against 0 because of NaN
    //
    if( 0 != ( int ) g_fTemperature      &&
        0 != ( int ) g_fHumidity  &&
        0 != ( int ) g_fWeight )
    {
        //
        // CSV to make it easy to read off the serial line
        //
        Serial.print(g_fTemperature);
        Serial.print(",");
        Serial.print(g_fHumidity);
        Serial.print(",");
        Serial.println(g_fWeight);
    }

    delay(LOOP_GRANULARITY_MS);
}

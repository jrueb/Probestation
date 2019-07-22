#include <Adafruit_BME680.h>

// ms to wait between reading from serial
#define WAITREAD 100

Adafruit_BME680 sensor76;
Adafruit_BME680 sensor77;

#define BUFLEN 64
int pos = 0;
char buf[BUFLEN];

bool setupBME680(const Adafruit_BME680& sensor, uint8_t address) {
	if (!sensor.begin(address)) {
		Serial.print("Error: Could not connect to BME680 at address 0x");
    Serial.print(address, HEX);
    Serial.println(". Check your I2C wiring");
		return false;
	}
  
  // Set up oversampling and filter initialization
  sensor.setTemperatureOversampling(BME680_OS_8X);
  sensor.setHumidityOversampling(BME680_OS_2X);
  sensor.setPressureOversampling(BME680_OS_4X);
  sensor.setIIRFilterSize(BME680_FILTER_SIZE_3);
  sensor.setGasHeater(320, 150); // 320*C for 150 ms
  
  return true;
}

void setup() {
  Serial.begin(19200);
  while (!Serial); // Wait for serial to be ready

  Wire.begin();
  
  if (!setupBME680(sensor76, 0x76))
    while(1);
  if (!setupBME680(sensor77, 0x77))
    while(1);
}

bool measure(const Adafruit_BME680& sensor) {
  if (!sensor.performReading())
    return false;
  
  Serial.print(sensor.temperature);
  Serial.print(" °C, ");
  Serial.print((long)sensor.pressure);
  Serial.print(" Pa, ");
  Serial.print(sensor.humidity);
  Serial.print(" %, ");
  Serial.print(sensor.gas_resistance / 1000);
  Serial.println(" kΩ");
  
  return true;
}

bool measureall(const Adafruit_BME680& sensor1, const Adafruit_BME680& sensor2) {
  if (!sensor1.performReading())
    return false;
  if (!sensor2.performReading())
    return false;
  
  Serial.print(sensor1.temperature);
  Serial.print(" °C, ");
  Serial.print((long)sensor1.pressure);
  Serial.print(" Pa, ");
  Serial.print(sensor1.humidity);
  Serial.print(" %, ");
  Serial.print(sensor1.gas_resistance / 1000);
  Serial.print(" kΩ, ");
  Serial.print(sensor2.temperature);
  Serial.print(" °C, ");
  Serial.print((long)sensor2.pressure);
  Serial.print(" Pa, ");
  Serial.print(sensor2.humidity);
  Serial.print(" %, ");
  Serial.print(sensor2.gas_resistance / 1000);
  Serial.println(" kΩ");
  
  return true;
}

void execute(const char* cmd) {
  char cmd_lower[BUFLEN];
  for (int i = 0; i < sizeof(cmd_lower); ++i)
    cmd_lower[i] = tolower(cmd[i]);
  
  if (strcmp("*idn?\n", cmd_lower) == 0
      || strcmp("*idn?\r\n", cmd_lower) == 0) {

    Serial.println("Arduino Probestation Environment Sensoring");
  } else if (strcmp("help\n", cmd_lower) == 0
      || strcmp("help\r\n", cmd_lower) == 0) {

    Serial.println("Available commands: *idn? help format measureall measure76 measure77");
  } else if (strcmp("format\n", cmd_lower) == 0
      || strcmp("format\r\n", cmd_lower) == 0) {

    Serial.println("Format is: Temperature, Pressure, Humidity, Gas resistance");
  } else if (strcmp("measure76\n", cmd_lower) == 0
      || strcmp("measure76\r\n", cmd_lower) == 0) {

      if (!measure(sensor76))
        Serial.println("Error: Failed to measure from sensor at 0x76.");
  } else if (strcmp("measure77\n", cmd_lower) == 0
      || strcmp("measure77\r\n", cmd_lower) == 0) {

      if (!measure(sensor77))
        Serial.println("Error: Failed to measure from sensor at 0x77.");
  } else if (strcmp("measureall\n", cmd_lower) == 0
      || strcmp("measureall\r\n", cmd_lower) == 0) {

      if (!measureall(sensor76, sensor77))
        Serial.println("Error: Failed to measure from sensors");
  }
}

void loop() {
  delay(WAITREAD);

  if (Serial.available() == 0)
    return;
  char c = Serial.read();
  buf[pos] = c;
  pos++;
  buf[pos] = 0;
  if (pos == sizeof(buf) - 1)
    pos = 0;
  if (c == '\n') {
    execute(buf);
    pos = 0;
  }
}

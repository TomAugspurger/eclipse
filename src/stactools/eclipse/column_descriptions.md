|              Field¹              |     Type      | Nullable | Description                   |
|----------------------------------|---------------|----------|-------------------------------|
| City                             | String        | N        | City where the Microsoft Eclipse device is deployed |
| DeviceId                         | Integer       | N        | Id for a given device |
| LocationName                     | String        | N        | Unique string describing the device location |
| Latitude                         | Double        | N        | Latitude of the device location|
| Longitude                        | Double        | N        | Longitude of the device location|
| ReadingDateTimeUTC               | DateTime      | N        | The UTC date time string (like 2022-03-04 20:27:25.000) when the reading from the Eclipse sensor was recorded |
| PM25                             | Double        | Y        | Uncalibrated Fine particulate matter (PM 2.5) in µg/m³ |
| CalibratedPM25                   | Double        | Y        | Calibrated PM 2.5 in µg/m³ |
| CalibratedO3                     | Double        | Y        | Calibrated Ozone in PPB |
| CalibratedNO2                    | Double        | Y        | Calibrated Nitrogen Dioxide in PPB |
| Temperature                      | Double        | Y        | Degree Celsius |
| Humidity                         | Double        | Y        | Relative humidity |
| CO                               | Double        | Y        | Uncalibrated Carbon monoxide (CO) in PPM |
| BatteryLevel                     | Double        | Y        | Device battery level in Volts|
| PercentBattery                   | Double        | Y        | Percent of device battery|
| CellSignal                       | Double        | Y        | Cellular signal strength in dB |
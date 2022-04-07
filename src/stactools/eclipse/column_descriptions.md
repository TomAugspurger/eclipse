
|              Field¹              |     Type      | Nullable | Description                   |
|----------------------------------|---------------|----------|-------------------------------|
| City                             | String        | N        | City where the Microsoft Eclipse device is deployed |
| DeviceId                         | Integer       | N        | Id for a given device |
| LocationName                     | String        | N        | Unique string describing the device location |
| Latitude                         | Double        | N        | Latitude of the device location|
| Longitude                        | Double        | N        | Longitude of the device location|
| ReadingDateTimeUTC               | DateTime      | N        | The UTC date time string (like 2022-03-04 20:27:25.000) when the reading from the Eclipse sensor was recorded |
| PM25                             | Double        | Y        | Fine particulate matter (PM 2.5) in µg/m³ |
| CalibratedPM25                   | Double        | Y        | Calibrated PM 2.5 in µg/m³ |
| O3                            | Double        | Y        | Ozone in µg/m³ |
| NO2                              | Double        | Y        | Nitrous Dioxide in µg/m³ |
| Humidity                         | Double        | Y        | Relative humidity |
| RawCO                            | Double        | Y        | Raw carbon monoxide (CO) in PPM |
| BatteryLevel                     | Double        | Y        | Device battery level in Volts|
| PercentBattery                   | Double        | Y        | Percent of device battery|
| CellSignal                       | Double        | Y        | Cellular signal strength in dB |

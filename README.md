# Module ultrasonic-dimled

Parking assistant with a basic LED and ultrasonic sensor

## Model joyce:ultrasonic-dimled:ultrasonic-dimLED

Connect a PWM-capable LED (with resistor) to an ultrasonic sensor to increase brightness as an object gets closer, and blink when it's within a specific range

### Configuration

The following attribute template can be used to configure this model:

```json
{
  "auto_start": <boolean>,
  "board": <string>,
  "sensor": <string>,
  "led_pin": <string>,
  "max_distance": <float>,
  "blinking_distance": <float>
}
```

#### Attributes

The following attributes are available for this model:

| Name                | Type    | Inclusion | Description                                                |
| ------------------- | ------- | --------- | ---------------------------------------------------------- |
| `auto_start`        | boolean | Required  | Starts the control loop                                    |
| `board`             | string  | Required  | Name of the Raspberry Pi board as found in the Viam app    |
| `sensor`            | string  | Required  | Name of the ultrasonic sensor as found in the Viam app     |
| `led_pin`           | string  | Required  | Number of the physical pin connected to the LED            |
| `max_distance`      | float   | Optional  | Max distance from sensor to detect objects (in meters)     |
| `blinking_distance` | float   | Optional  | Distance from snesor to begin blinking rapidly (in meters) |

#### Example Configuration

```json
{
  "auto_start": true,
  "board": "board-1",
  "sensor": "ultra-adafruit",
  "led_pin": "11",
  "max_distance": 1,
  "blinking_distance": 0.2
}
```

### DoCommand

You can start the control loop with `start` or `stop`, or test the LED by sending a flash command with `test`.

#### Example DoCommand

```json
{
  "start": true
}

{
  "stop": true
}

{
  "test": true
}
```

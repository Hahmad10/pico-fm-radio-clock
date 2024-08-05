# FM Radio-Clock on a Raspberry Pi Pico

A clock radio built on a custom 2-layer PCB around a Raspberry Pi Pico (RP2040), from summer 2024.

The board combines an RDA5807M FM tuner, two LM386 audio amplifiers (one for the radio, one for the alarm), an SSD1306 OLED over SPI, a PEC11R rotary encoder with a push switch, and four tactile buttons. The MicroPython firmware shows the time in 12- or 24-hour format along with the temperature, sets and snoozes an alarm, and tunes and mutes the radio, all through on-screen menus.

## Table of Contents

- [File Structure](#file-structure)
- [Hardware](#hardware)
- [Firmware](#firmware)
- [Running It](#running-it)
- [Third-Party Code](#third-party-code)

## File Structure

```
pico-fm-radio-clock/
├── README.md
├── src/                          # Final firmware (copy all of it to the Pico)
│   ├── main.py                   # UI: display, buttons, encoder, menus, main loop
│   ├── PicoClock_API.py          # Clock class on the RP2040's RTC, 12/24 h formatting
│   ├── PicoAlarm_API.py          # Alarm class: PWM buzzer, snooze/stop interrupt, mutes radio
│   ├── PicoRadio_API.py          # Radio class: RDA5807M over I2C (frequency, volume, mute)
│   └── PicoTemp_API.py           # Temperature from the RP2040's on-chip sensor
├── prototypes/                   # Subsystem tests written before the integrated build
│   ├── radio_display.py          # Radio driver + OLED readout
│   ├── radio_button_volume.py    # Button interrupt adjusting radio volume
│   ├── radio_menu.py             # First menu for driving the radio from the OLED
│   ├── display_radio_info.py     # Radio info on the OLED, updated on a button press
│   ├── display_button_debounced.py
│   ├── clock.py                  # First clock test
│   ├── clock_button_v1.py        # Clock with a display-mode button
│   ├── clock_button_v2.py
│   ├── clock_button_v3.py
│   └── clock_radio_time_set.py   # Clock + radio + encoder time setting, before the alarm
└── hardware/
    ├── schematic.jpg             # Full KiCad schematic
    ├── pcb-layout.jpg            # KiCad 2-layer layout
    ├── pcb-front.jpg             # Fabricated board, front
    ├── pcb-back.jpg              # Fabricated board, back
    ├── enclosure-3d.jpg          # SOLIDWORKS enclosure model
    └── enclosure-traces.jpg      # Laser-cut panel outlines
```

### src/
`main.py` is the integrated program: display, buttons, encoder, menus and the main loop. Its git history shows it growing from the first integrated build to the final version (edit modes, channel tuning, snooze-duration editing, station names). The four `*_API.py` files are the classes it imports.

### prototypes/
Each subsystem (radio, display, buttons, clock, encoder) was brought up on its own before being merged into `main.py`. They're kept here as a record of how the firmware grew.

### hardware/
The schematic, layout and enclosure were drawn in KiCad 8 and SOLIDWORKS. The board was fabricated by PCBWay: 112 × 80.2 mm, 2 layers, 1.6 mm FR-4, lead-free HASL.

## Hardware

| Block | Part | Interface | Pico pins |
|---|---|---|---|
| FM tuner | RDA5807M module | I2C1 @ 200 kHz, address 0x10 | GP26 SDA, GP27 SCL |
| Display | 128×64 SSD1306 OLED | SPI0 | GP18 SCK, GP19 MOSI, GP17 CS, GP20 DC, GP21 RES |
| Encoder | Bourns PEC11R + switch | GPIO with pull-ups | GP6 DT, GP7 CLK, GP8 SW |
| Buttons | 4× TL1105 | GPIO interrupts with pull-downs | GP0 set, GP1 edit, GP2 12/24 h, GP3 snooze |
| Alarm | LM386 + speaker | PWM | GP15 |
| Radio audio | LM386 + speaker, volume pot | analog from the tuner | — |
| Temperature | RP2040 internal sensor | ADC4 | — |

The parts cost about $28 in total, before the PCB.

## Firmware

- **Clock:** uses the RP2040's built-in RTC. The colon blinks every 500 ms, and a button toggles 12/24-hour mode. The encoder sets hours and minutes.
- **Alarm:** set from the menu. When it fires, the radio mutes and a 1.5 kHz PWM tone pulses on GP15. The first snooze press snoozes, the second stops it, and the radio resumes if it was playing. A 500 ms window debounces the snooze button.
- **Radio:** tunes 88–108 MHz in 0.1 MHz steps with volume 0–15 and mute. The 8-byte RDA5807M register block is rebuilt on every change and written over I2C.
- **UI:** button handlers are interrupt-driven and debounced in software. The OLED shows the time, temperature and the radio station as a scrolling status line, with short confirmation messages when a setting changes.

## Running It

1. Flash MicroPython onto the Pico.
2. Copy `ssd1306.py` from [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/micropython/drivers/display/ssd1306) to the Pico. It's the standard driver and isn't vendored here.
3. Copy everything in `src/` to the Pico, for example with Thonny or `mpremote cp src/*.py :`.
4. Reset the board, and `main.py` starts on boot.

## Third-Party Code

The `Radio` class in `PicoRadio_API.py` is adapted from an existing RDA5807M MicroPython driver, and the OLED uses the standard `ssd1306` driver from micropython-lib.

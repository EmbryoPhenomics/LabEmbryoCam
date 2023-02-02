/**
 * MK4duo Firmware for 3D Printer, Laser and CNC
 *
 * Based on Marlin, Sprinter and grbl
 * Copyright (C) 2011 Camiel Gubbels / Erik van der Zalm
 * Copyright (C) 2013 Alberto Cotronei @MagoKimbra
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 */

#ifndef _LASER_H_
#define _LASER_H_

#if ENABLED(LASER)

  #include <inttypes.h>

  #if ENABLED(HIGH_TO_FIRE) // Some cutters fire on high, some on low.
    #define LASER_ARM   HIGH
    #define LASER_UNARM LOW
  #else
    #define LASER_ARM   LOW
    #define LASER_UNARM HIGH
  #endif

  // Laser constants
  #define LASER_OFF   0
  #define LASER_ON    1

  #define CONTINUOUS  0
  #define PULSED      1
  #define RASTER      2

  class Laser {

    public: /** Public Parameters */

      static float    ppm;          // pulses per millimeter, for pulsed firing mode

      static uint8_t  intensity,    // Laser firing instensity 0 - 255
                      mode;         // CONTINUOUS, PULSED, RASTER

      static uint32_t duration,     // laser firing duration in microseconds, for pulsed firing mode
                      dur;          // instantaneous duration

      static bool     status,       // LASER_ON / LASER_OFF - buffered
                      firing,       // LASER_ON / LASER_OFF - instantaneous
                      diagnostics;  // Verbose debugging output over serial

      static millis_t last_firing;  // microseconds since last laser firing

      static uint16_t time,         // temporary counter to limit eeprom writes
                      lifetime;     // laser lifetime firing counter in minutes

      #if ENABLED(LASER_RASTER)

        static unsigned char  raster_data[LASER_MAX_RASTER_LINE],
                              rasterlaserpower;

        static float          raster_aspect_ratio,
                              raster_mm_per_pulse;

        static int            raster_raw_length,
                              raster_num_pixels;

        static uint8_t        raster_direction;

      #endif

    public: /** Public Function */

      static void init();
      static void fire(uint8_t intensity=255);
      static void extinguish();
      static void set_mode(uint8_t mode);

      #if ENABLED(LASER_PERIPHERALS)
        static bool peripherals_ok();
        static void peripherals_on();
        static void peripherals_off();
        static void wait_for_peripherals();
      #endif // LASER_PERIPHERALS

  };

  extern Laser laser;

#endif // ENABLED(LASER)

#endif /* _LASER_H_ */

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

#include "../../../MK4duo.h"

#if ENABLED(__AVR__)

  Watchdog watchdog;

  // Initialize watchdog with a 4 sec interrupt time
  void Watchdog::init(void) {
    #if ENABLED(USE_WATCHDOG)
      #if ENABLED(WATCHDOG_RESET_MANUAL)
        // We enable the watchdog timer, but only for the interrupt.
        // Take care, as this requires the correct order of operation, with interrupts disabled. See the datasheet of any AVR chip for details.
        wdt_reset();
        cli();
        _WD_CONTROL_REG = _BV(_WD_CHANGE_BIT) | _BV(WDE);
        _WD_CONTROL_REG = _BV(WDIE) | WDTO_4S;

        sei();
        wdt_reset();
      #else
        wdt_enable(WDTO_4S);
      #endif
    #endif // USE_WATCHDOG
  }

  void Watchdog::reset(void) {
    #if ENABLED(USE_WATCHDOG)
      wdt_reset();
    #endif
  }

  //===========================================================================
  //=================================== ISR ===================================
  //===========================================================================

  // Watchdog timer interrupt, called if main program blocks >4sec and manual reset is enabled.
  #if ENABLED(USE_WATCHDOG) && ENABLED(WATCHDOG_RESET_MANUAL)
    ISR(WDT_vect) {
      sei();  // With the interrupt driven serial we need to allow interrupts.
      SERIAL_LM(ER, "Watchdog timeout. Reset required.");
      printer.minikill();
    }
  #endif // WATCHDOG_RESET_MANUAL

#endif

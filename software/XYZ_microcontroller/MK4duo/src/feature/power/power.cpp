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

#if HAS_POWER_SWITCH || HAS_POWER_CONSUMPTION_SENSOR || HAS_POWER_CHECK

  Power powerManager;

  // Public Parameters
  #if HAS_POWER_CONSUMPTION_SENSOR
    int16_t   Power::current_raw_powconsumption = 0;    // Holds measured power consumption
    float     Power::consumption_meas           = 0.0;
    uint32_t  Power::consumption_hour           = 0,
              Power::startpower                 = 0;
  #endif

  // Private Parameters
  flagbyte_t  Power::flag;

  #if HAS_POWER_SWITCH
    bool      Power::powersupply_on = false;
    #if (POWER_TIMEOUT > 0)
      watch_t Power::watch_lastPowerOn(POWER_TIMEOUT * 1000UL);
    #endif
  #endif

  // Public Function
  #if HAS_POWER_SWITCH || HAS_POWER_CHECK

    // Public Function
    void Power::init() {
      #if HAS_POWER_SWITCH
        SET_OUTPUT(PS_ON_PIN);
      #endif
      #if HAS_POWER_CHECK
        SET_INPUT(POWER_CHECK_PIN);
      #endif
    }

    #if HAS_POWER_CHECK

      void Power::factory_parameters() {
        setLogic(POWER_CHECK_LOGIC);
        setPullup(PULLUP_POWER_CHECK);
      }

      void Power::setup_pullup() {
        HAL::setInputPullup(POWER_CHECK_PIN, isPullup());
      }

      void Endstops::report() {
        SERIAL_LOGIC("POWER CHECK Logic", isLogic());
        SERIAL_LOGIC(" Pullup", isPullup());
      }

    #endif 

    void Power::spin() {
      if (is_power_needed())
        power_on();
      #if (POWER_TIMEOUT > 0)
        else if (watch_lastPowerOn.elapsed())
          power_off();
      #endif
    }

    void Power::power_on() {
      #if (POWER_TIMEOUT > 0)
        watch_lastPowerOn.start();
      #endif
      if (!powersupply_on) {
        WRITE(PS_ON_PIN, PS_ON_AWAKE);
        #if HAS_TRINAMIC
          HAL::delayMilliseconds(100); // Wait for power to settle
          tmc.restore();
        #endif
        HAL::delayMilliseconds((DELAY_AFTER_POWER_ON) * 1000UL);
        powersupply_on = true;
      }
    }

    void Power::power_off() {
      if (powersupply_on) {
        WRITE(PS_ON_PIN, PS_ON_ASLEEP);
        powersupply_on = false;
        #if (POWER_TIMEOUT > 0)
          watch_lastPowerOn.stop();
        #endif
      }
    }

    bool Power::is_power_needed() {

      #if HEATER_COUNT > 0
        if (thermalManager.heaters_isActive()) return true;
      #endif

      #if FAN_COUNT > 0
        LOOP_FAN() if (fans[f].Speed > 0) return true;
      #endif

      if (X_ENABLE_READ == X_ENABLE_ON || Y_ENABLE_READ == Y_ENABLE_ON || Z_ENABLE_READ == Z_ENABLE_ON
          || E0_ENABLE_READ == E_ENABLE_ON // If any of the drivers are enabled...
          #if DRIVER_EXTRUDERS > 1
            || E1_ENABLE_READ == E_ENABLE_ON
            #if HAS_X2_ENABLE
              || X2_ENABLE_READ == X_ENABLE_ON
            #endif
            #if DRIVER_EXTRUDERS > 2
              || E2_ENABLE_READ == E_ENABLE_ON
              #if DRIVER_EXTRUDERS > 3
                || E3_ENABLE_READ == E_ENABLE_ON
                #if DRIVER_EXTRUDERS > 4
                  || E4_ENABLE_READ == E_ENABLE_ON
                  #if DRIVER_EXTRUDERS > 5
                    || E5_ENABLE_READ == E_ENABLE_ON
                  #endif
                #endif
              #endif
            #endif
          #endif
      ) return true;

      return false;
    }

  #endif // HAS_POWER_SWITCH

  #if HAS_POWER_CONSUMPTION_SENSOR

    // Convert raw Power Consumption to watt
    float Power::raw_analog2voltage() {
      return ((HAL_VOLTAGE_PIN) * current_raw_powconsumption) / (AD_RANGE);
    }

    float Power::analog2voltage() {
      float power_zero_raw = (POWER_ZERO * AD_RANGE) / (HAL_VOLTAGE_PIN);
      float rel_raw_power = (current_raw_powconsumption < power_zero_raw) ? (2 * power_zero_raw - current_raw_powconsumption) : current_raw_powconsumption;
      return ((HAL_VOLTAGE_PIN) * rel_raw_power) / (AD_RANGE - POWER_ZERO);
    }

    float Power::analog2current() {
      float temp = analog2voltage() / POWER_SENSITIVITY;
      temp = (((100 - POWER_ERROR) / 100) * temp) - (POWER_OFFSET);
      return temp > 0 ? temp : 0;
    }

    float Power::analog2power() {
      return (analog2current() * POWER_VOLTAGE * 100) / (POWER_EFFICIENCY);
    }

    float Power::analog2error(float current) {
      float temp1 = (analog2voltage() / POWER_SENSITIVITY - POWER_OFFSET) * (POWER_VOLTAGE);
      if (temp1 <= 0) return 0.0;
      float temp2 = current * (POWER_VOLTAGE);
      if (temp2 <= 0) return 0.0;
      return ((temp2 / temp1) - 1) * 100;
    }

    float Power::analog2efficiency(float watt) {
      return (analog2current() * (POWER_VOLTAGE) * 100) / watt;
    }

  #endif // HAS_POWER_CONSUMPTION_SENSOR

#endif // HAS_POWER_SWITCH || HAS_POWER_CONSUMPTION_SENSOR

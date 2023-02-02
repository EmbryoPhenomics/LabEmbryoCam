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

/**
 * mcode
 *
 * Copyright (C) 2017 Alberto Cotronei @MagoKimbra
 */

#if ENABLED(AUTO_BED_LEVELING_BILINEAR)

  #define CODE_M421

  /**
   * M421: Set a single Mesh Bed Leveling Z coordinate
   *
   * Usage:
   *   M421 I<xindex> J<yindex> Z<linear>
   *   M421 I<xindex> J<yindex> Q<offset>
   */
  inline void gcode_M421(void) {
    int8_t ix = parser.intval('I', -1), iy = parser.intval('J', -1);
    const bool  hasI = ix >= 0,
                hasJ = iy >= 0,
                hasZ = parser.seen('Z'),
                hasQ = !hasZ && parser.seen('Q');

    if (!hasI || !hasJ || !(hasZ || hasQ)) {
      SERIAL_LM(ER, MSG_ERR_M421_PARAMETERS);
    }
      else if (!WITHIN(ix, 0, GRID_MAX_POINTS_X - 1) || !WITHIN(iy, 0, GRID_MAX_POINTS_Y - 1)) {
      SERIAL_LM(ER, MSG_ERR_MESH_XY);
    }

    if (hasI && hasJ && !(hasZ || hasQ)) {
      SERIAL_MV("Level value in ix", ix);
      SERIAL_MV(" iy", iy);
      SERIAL_EMV(" Z", abl.z_values[ix][iy]);
      return;
    }
    else {
      abl.z_values[ix][iy] = parser.value_linear_units() + (hasQ ? abl.z_values[ix][iy] : 0);
      #if ENABLED(ABL_BILINEAR_SUBDIVISION)
        abl.virt_interpolate();
      #endif
    }
  }

#endif // ENABLED(AUTO_BED_LEVELING_BILINEAR)

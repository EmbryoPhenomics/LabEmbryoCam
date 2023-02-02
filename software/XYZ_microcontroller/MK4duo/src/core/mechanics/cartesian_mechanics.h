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
 * cartesian_mechanics.h
 *
 * Copyright (C) 2016 Alberto Cotronei @MagoKimbra
 */

#pragma once

// Struct Cartesian Settings
typedef struct : public generic_data_t {} mechanics_data_t;

class Cartesian_Mechanics : public Mechanics {

  public: /** Constructor */

    Cartesian_Mechanics() {}

  public: /** Public Parameters */

    static mechanics_data_t data;

    static const float  base_max_pos[XYZ],
                        base_min_pos[XYZ],
                        base_home_pos[XYZ],
                        max_length[XYZ];

    #if ENABLED(DUAL_X_CARRIAGE)
      static DualXMode  dual_x_carriage_mode;
      static float      inactive_extruder_x_pos,        // used in mode 0 & 1
                        raised_parked_position[XYZE],   // used in mode 1
                        duplicate_extruder_x_offset;    // used in mode 2 & 3
      static int16_t    duplicate_extruder_temp_offset; // used in mode 2 & 3
      static millis_t   delayed_move_time;              // used in mode 1
      static bool       active_extruder_parked,         // used in mode 1, 2 & 3
                        extruder_duplication_enabled,   // used in mode 2
                        scaled_duplication_mode;        // used in mode 3
    #endif

  public: /** Public Function */

    /**
     * Initialize Factory parameters
     */
    static void factory_parameters();

    /**
     * Get the stepper positions in the cartesian_position[] array.
     *
     * The result is in the current coordinate space with
     * leveling applied. The coordinates need to be run through
     * unapply_leveling to obtain the "ideal" coordinates
     * suitable for current_position, etc.
     */
    static void get_cartesian_from_steppers();

    /**
     *  Plan a move to (X, Y, Z) and set the current_position
     *  The final current_position may not be the one that was requested
     */
    static void do_blocking_move_to(const float rx, const float ry, const float rz, const float &fr_mm_s=0.0);
    static void do_blocking_move_to_x(const float &rx, const float &fr_mm_s=0.0);
    static void do_blocking_move_to_z(const float &rz, const float &fr_mm_s=0.0);
    static void do_blocking_move_to_xy(const float &rx, const float &ry, const float &fr_mm_s=0.0);

    /**
     * Home all axes according to settings
     */
    static void home(const bool homeX=false, const bool homeY=false, const bool homeZ=false);

    /**
     * Home an individual linear axis
     */
    static void do_homing_move(const AxisEnum axis, const float distance, const float fr_mm_s=0.0);

    /**
     * Prepare a linear move in a Cartesian setup.
     *
     * When a mesh-based leveling system is active, moves are segmented
     * according to the configuration of the leveling system.
     *
     * Returns true if current_position[] was set to destination[]
     */
    static bool prepare_move_to_destination_mech_specific();

    /**
     * Set an axis' current position to its home position (after homing).
     *
     * For Cartesian robots this applies one-to-one when an
     * individual axis has been homed.
     *
     * Callers must sync the planner position after calling this!
     */
    static void set_axis_is_at_home(const AxisEnum axis);

    static bool position_is_reachable(const float &rx, const float &ry);
    static bool position_is_reachable_by_probe(const float &rx, const float &ry);

    /**
     * Report current position to host
     */
    static void report_current_position_detail();

    /**
     * Plan an arc in 2 dimensions
     *
     * The arc is approximated by generating many small linear segments.
     * The length of each segment is configured in MM_PER_ARC_SEGMENT (Default 1mm)
     * Arcs should only be made relatively large (over 5mm), as larger arcs with
     * larger segments will tend to be more efficient. Your slicer should have
     * options for G2/G3 arc generation. In future these options may be GCode tunable.
     */
    #if ENABLED(ARC_SUPPORT)
      static void plan_arc(const float (&cart)[XYZE], const float (&offset)[2], const uint8_t clockwise);
    #endif

    /**
     * Prepare a linear move in a dual X axis setup
     */
    #if ENABLED(DUAL_X_CARRIAGE)
      FORCE_INLINE static bool dxc_is_duplicating() { return dual_x_carriage_mode >= DXC_DUPLICATION_MODE; }
      static float  x_home_pos(const int extruder);
      static bool   dual_x_carriage_unpark();
      FORCE_INLINE static int x_home_dir(const uint8_t extruder) { return extruder ? X2_HOME_DIR : X_HOME_DIR; }
    #endif

    /**
     * Print mechanics parameters in memory
     */
    #if DISABLED(DISABLE_M503)
      static void print_parameters();
    #endif

    #if ENABLED(NEXTION) && ENABLED(NEXTION_GFX)
      static void Nextion_gfx_clear();
    #endif

  private: /** Private Function */

    /**
     *  Home axis
     */
    static void homeaxis(const AxisEnum axis);

    #if ENABLED(QUICK_HOME)
      static void quick_home_xy();
    #endif

    #if ENABLED(Z_SAFE_HOMING)
      static void home_z_safely();
    #endif

    #if ENABLED(DOUBLE_Z_HOMING)
      static void double_home_z();
    #endif

};

extern Cartesian_Mechanics mechanics;

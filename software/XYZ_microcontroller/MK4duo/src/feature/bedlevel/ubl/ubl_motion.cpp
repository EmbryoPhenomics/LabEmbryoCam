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

#include "../../../../MK4duo.h"

#if ENABLED(AUTO_BED_LEVELING_UBL)

#include "ubl.h"
#include <math.h>

#if UBL_DELTA

  #define DELTA_SEGMENT_MIN_LENGTH 0.10 // mm (still subject to DELTA_SEGMENTS_PER_SECOND)

  /**
   * Prepare a segmented linear move for DELTA/SCARA/CARTESIAN with UBL and FADE semantics.
   * This calls planner.buffer_segment multiple times for small incremental moves.
   * Returns true if did NOT move, false if moved (requires mechanics.current_position update).
   */

  bool _O2 unified_bed_leveling::prepare_segmented_line_to(const float (&rtarget)[XYZE], const float &feedrate) {

    if (!mechanics.position_is_reachable(rtarget[X_AXIS], rtarget[Y_AXIS]))  // fail if moving outside reachable boundary
      return true; // did not move, so mechanics.current_position still accurate

    const float total[XYZE] = {
      rtarget[X_AXIS] - mechanics.current_position[X_AXIS],
      rtarget[Y_AXIS] - mechanics.current_position[Y_AXIS],
      rtarget[Z_AXIS] - mechanics.current_position[Z_AXIS],
      rtarget[E_AXIS] - mechanics.current_position[E_AXIS]
    };

    const float cartesian_xy_mm = HYPOT(total[X_AXIS], total[Y_AXIS]),                    // total horizontal xy distance
                seconds = cartesian_xy_mm / feedrate;                                     // seconds to move xy distance at requested rate
    uint16_t    segments = LROUND(mechanics.data.segments_per_second * seconds),         // preferred number of segments for distance @ feedrate
                seglimit = LROUND(cartesian_xy_mm * (1.0f / (DELTA_SEGMENT_MIN_LENGTH))); // number of segments at minimum segment length

    NOMORE(segments, seglimit); // limit to minimum segment length (fewer segments)
    NOLESS(segments, 1U);       // must have at least one segment

    const float inv_segments = 1.0f / segments;  // divide once, multiply thereafter

    const float segment_xyz_mm = HYPOT(cartesian_xy_mm, total[Z_AXIS]) * inv_segments;    // length of each segment

    const float diff[XYZE] = {
      total[X_AXIS] * inv_segments,
      total[Y_AXIS] * inv_segments,
      total[Z_AXIS] * inv_segments,
      total[E_AXIS] * inv_segments
    };

    // Note that E segment distance could vary slightly as z mesh height
    // changes for each segment, but small enough to ignore.

    float raw[XYZE] = {
      mechanics.current_position[X_AXIS],
      mechanics.current_position[Y_AXIS],
      mechanics.current_position[Z_AXIS],
      mechanics.current_position[E_AXIS]
    };

    // Only compute leveling per segment if ubl active and target below z_fade_height.
    if (!bedlevel.leveling_active || !bedlevel.leveling_active_at_z(rtarget[Z_AXIS])) {   // no mesh leveling
      while (--segments) {
        LOOP_XYZE(i) raw[i] += diff[i];
        planner.buffer_line(raw, feedrate, active_extruder, segment_xyz_mm);
      }
      planner.buffer_line(rtarget, feedrate, active_extruder, segment_xyz_mm);
      return false; // moved but did not set_current_from_destination();
    }

    // Otherwise perform per-segment leveling

    #if ENABLED(ENABLE_LEVELING_FADE_HEIGHT)
      const float fade_scaling_factor = bedlevel.fade_scaling_factor_for_z(rtarget[Z_AXIS]);
    #endif

    // increment to first segment destination
    LOOP_XYZE(i) raw[i] += diff[i];

    for(;;) {  // for each mesh cell encountered during the move

      // Compute mesh cell invariants that remain constant for all segments within cell.
      // Note for cell index, if point is outside the mesh grid (in MESH_INSET perimeter)
      // the bilinear interpolation from the adjacent cell within the mesh will still work.
      // Inner loop will exit each time (because out of cell bounds) but will come back
      // in top of loop and again re-find same adjacent cell and use it, just less efficient
      // for mesh inset area.

      int8_t cell_xi = (raw[X_AXIS] - (UBL_MESH_MIN_X)) * (1.0 / (MESH_X_DIST)),
             cell_yi = (raw[Y_AXIS] - (UBL_MESH_MIN_Y)) * (1.0 / (MESH_Y_DIST));

      cell_xi = constrain(cell_xi, 0, (GRID_MAX_POINTS_X) - 1);
      cell_yi = constrain(cell_yi, 0, (GRID_MAX_POINTS_Y) - 1);

      const float x0 = mesh_index_to_xpos(cell_xi),   // 64 byte table lookup avoids mul+add
                  y0 = mesh_index_to_ypos(cell_yi);

      float z_x0y0 = z_values[cell_xi  ][cell_yi  ],  // z at lower left corner
            z_x1y0 = z_values[cell_xi+1][cell_yi  ],  // z at upper left corner
            z_x0y1 = z_values[cell_xi  ][cell_yi+1],  // z at lower right corner
            z_x1y1 = z_values[cell_xi+1][cell_yi+1];  // z at upper right corner

      if (isnan(z_x0y0)) z_x0y0 = 0;              // ideally activating bedlevel.active (G29 A)
      if (isnan(z_x1y0)) z_x1y0 = 0;              //   should refuse if any invalid mesh points
      if (isnan(z_x0y1)) z_x0y1 = 0;              //   in order to avoid isnan tests per cell,
      if (isnan(z_x1y1)) z_x1y1 = 0;              //   thus guessing zero for undefined points

      float cx = raw[X_AXIS] - x0,   // cell-relative x and y
            cy = raw[Y_AXIS] - y0;

      const float z_xmy0 = (z_x1y0 - z_x0y0) * (1.0 / (MESH_X_DIST)),   // z slope per x along y0 (lower left to lower right)
                  z_xmy1 = (z_x1y1 - z_x0y1) * (1.0 / (MESH_X_DIST));   // z slope per x along y1 (upper left to upper right)

            float z_cxy0 = z_x0y0 + z_xmy0 * cx;            // z height along y0 at cx (changes for each cx in cell)

      const float z_cxy1 = z_x0y1 + z_xmy1 * cx,            // z height along y1 at cx
                  z_cxyd = z_cxy1 - z_cxy0;                 // z height difference along cx from y0 to y1

            float z_cxym = z_cxyd * (1.0 / (MESH_Y_DIST));  // z slope per y along cx from y0 to y1 (changes for each cx in cell)

      //    float z_cxcy = z_cxy0 + z_cxym * cy;            // interpolated mesh z height along cx at cy (do inside the segment loop)

      // As subsequent segments step through this cell, the z_cxy0 intercept will change
      // and the z_cxym slope will change, both as a function of cx within the cell, and
      // each change by a constant for fixed segment lengths.

      const float z_sxy0 = z_xmy0 * diff[X_AXIS],                                     // per-segment adjustment to z_cxy0
                  z_sxym = (z_xmy1 - z_xmy0) * (1.0 / (MESH_Y_DIST)) * diff[X_AXIS];  // per-segment adjustment to z_cxym

      for(;;) {  // for all segments within this mesh cell

        if (--segments == 0)                      // if this is last segment, use rtarget for exact
          COPY_ARRAY(raw, rtarget);

        const float z_cxcy = (z_cxy0 + z_cxym * cy) // interpolated mesh z height along cx at cy
          #if ENABLED(ENABLE_LEVELING_FADE_HEIGHT)
            * fade_scaling_factor                   // apply fade factor to interpolated mesh height
          #endif
        ;

        const float z = raw[Z_AXIS];
        raw[Z_AXIS] += z_cxcy;
        planner.buffer_line(raw, feedrate, active_extruder, segment_xyz_mm);
        raw[Z_AXIS] = z;

        if (segments == 0)                        // done with last segment
          return false;                           // did not set_current_from_destination()

        LOOP_XYZE(i) raw[i] += diff[i];

        cx += diff[X_AXIS];
        cy += diff[Y_AXIS];

        if (!WITHIN(cx, 0, MESH_X_DIST) || !WITHIN(cy, 0, MESH_Y_DIST)) // done within this cell, break to next
          break;

        // Next segment still within same mesh cell, adjust the per-segment
        // slope and intercept to compute next z height.

        z_cxy0 += z_sxy0;   // adjust z_cxy0 by per-segment z_sxy0
        z_cxym += z_sxym;   // adjust z_cxym by per-segment z_sxym

      } // segment loop
    } // cell loop

    return false; // caller will update current_position
  }

#else

  void unified_bed_leveling::line_to_destination_cartesian(const float &feed_rate, uint8_t extruder) {
    /**
     * Much of the nozzle movement will be within the same cell. So we will do as little computation
     * as possible to determine if this is the case. If this move is within the same cell, we will
     * just do the required Z-Height correction, call the Planner's buffer_line() routine, and leave
     */
    #if HAS_POSITION_MODIFIERS
      float start[XYZE] = { mechanics.current_position[X_AXIS], mechanics.current_position[Y_AXIS], mechanics.current_position[Z_AXIS], mechanics.current_position[E_AXIS] },
              end[XYZE] = { mechanics.destination[X_AXIS], mechanics.destination[Y_AXIS], mechanics.destination[Z_AXIS], mechanics.destination[E_AXIS] };
      planner.apply_modifiers(start);
      planner.apply_modifiers(end);
    #else
      const float (&start)[XYZE] = mechanics.current_position,
                    (&end)[XYZE] = mechanics.destination;
    #endif

    const int cell_start_xi = get_cell_index_x(start[X_AXIS]),
              cell_start_yi = get_cell_index_y(start[Y_AXIS]),
              cell_dest_xi  = get_cell_index_x(end[X_AXIS]),
              cell_dest_yi  = get_cell_index_y(end[Y_AXIS]);

    if (bedlevel.g26_debug_flag) {
      SERIAL_MV(" ubl.line_to_destination(xe=", end[X_AXIS]);
      SERIAL_MV(", ye=", end[Y_AXIS]);
      SERIAL_MV(", ze=", end[Z_AXIS]);
      SERIAL_MV(", ee=", end[E_AXIS]);
      SERIAL_CHR(')');
      SERIAL_EOL();
      debug_current_and_destination(PSTR("Start of ubl.line_to_destination_cartesian()"));
    }

    // A move within the same cell needs no splitting
    if (cell_start_xi == cell_dest_xi && cell_start_yi == cell_dest_yi) {

      // For a move off the bed, use a constant Z raise
      if (!WITHIN(cell_dest_xi, 0, GRID_MAX_POINTS_X - 1) || !WITHIN(cell_dest_yi, 0, GRID_MAX_POINTS_Y - 1)) {

        // Note: There is no Z Correction in this case. We are off the grid and don't know what
        // a reasonable correction would be.  If the user has specified a UBL_Z_RAISE_WHEN_OFF_MESH
        // value, that will be used instead of a calculated (Bi-Linear interpolation) correction.

        const float z_raise = 0.0
          #if ENABLED(UBL_Z_RAISE_WHEN_OFF_MESH)
            + UBL_Z_RAISE_WHEN_OFF_MESH
          #endif
        ;
        planner.buffer_segment(end[X_AXIS], end[Y_AXIS], end[Z_AXIS] + z_raise, end[E_AXIS], feed_rate, extruder);
        mechanics.set_current_to_destination();

        if (bedlevel.g26_debug_flag)
          debug_current_and_destination(PSTR("out of bounds in ubl.line_to_destination_cartesian()"));

        return;
      }

      FINAL_MOVE:

      // The distance is always MESH_X_DIST so multiply by the constant reciprocal.
      const float xratio = (end[X_AXIS] - mesh_index_to_xpos(cell_dest_xi)) * (1.0 / (MESH_X_DIST));

      float z1 = z_values[cell_dest_xi    ][cell_dest_yi    ] + xratio *
                (z_values[cell_dest_xi + 1][cell_dest_yi    ] - z_values[cell_dest_xi][cell_dest_yi    ]),
            z2 = z_values[cell_dest_xi    ][cell_dest_yi + 1] + xratio *
                (z_values[cell_dest_xi + 1][cell_dest_yi + 1] - z_values[cell_dest_xi][cell_dest_yi + 1]);

      if (cell_dest_xi >= GRID_MAX_POINTS_X - 1) z1 = z2 = 0.0;

      // X cell-fraction done. Interpolate the two Z offsets with the Y fraction for the final Z offset.
      const float yratio = (end[Y_AXIS] - mesh_index_to_ypos(cell_dest_yi)) * (1.0f / (MESH_Y_DIST)),
                  z0 = cell_dest_yi < GRID_MAX_POINTS_Y - 1 ? (z1 + (z2 - z1) * yratio) * bedlevel.fade_scaling_factor_for_z(end[Z_AXIS]) : 0.0;

      // Undefined parts of the Mesh in z_values[][] are NAN.
      // Replace NAN corrections with 0.0 to prevent NAN propagation.
      planner.buffer_segment(end[X_AXIS], end[Y_AXIS], end[Z_AXIS] + (isnan(z0) ? 0.0 : z0), end[E_AXIS], feed_rate, extruder);

      if (bedlevel.g26_debug_flag)
        debug_current_and_destination(PSTR("FINAL_MOVE in ubl.line_to_destination_cartesian()"));

      mechanics.set_current_to_destination();
      return;
    }

    /**
     * Past this point the move is known to cross one or more mesh lines. Check for the most common
     * case - crossing only one X or Y line - after details are worked out to reduce computation.
     */

    const float dx = end[X_AXIS] - start[X_AXIS],
                dy = end[Y_AXIS] - start[Y_AXIS];

    const int left_flag = dx < 0.0 ? 1 : 0,
              down_flag = dy < 0.0 ? 1 : 0;

    const float adx = left_flag ? -dx : dx,
                ady = down_flag ? -dy : dy;

    const int dxi = cell_start_xi == cell_dest_xi ? 0 : left_flag ? -1 : 1,
              dyi = cell_start_yi == cell_dest_yi ? 0 : down_flag ? -1 : 1;

    /**
     * Compute the scaling factor for the extruder for each partial move.
     * We need to watch out for zero length moves because it will cause us to
     * have an infinate scaling factor. We are stuck doing a floating point
     * divide to get our scaling factor, but after that, we just multiply by this
     * number. We also pick our scaling factor based on whether the X or Y
     * component is larger. We use the biggest of the two to preserve precision.
     */

    const bool use_x_dist = adx > ady;

    float on_axis_distance = use_x_dist ? dx : dy,
          e_position = end[E_AXIS] - start[E_AXIS],
          z_position = end[Z_AXIS] - start[Z_AXIS];

    const float e_normalized_dist = e_position / on_axis_distance,
                z_normalized_dist = z_position / on_axis_distance;

    int current_xi = cell_start_xi,
        current_yi = cell_start_yi;

    const float m = dy / dx,
                c = start[Y_AXIS] - m * start[X_AXIS];

    const bool inf_normalized_flag = (isinf(e_normalized_dist) != 0),
               inf_m_flag = (isinf(m) != 0);

    /**
     * Handle vertical lines that stay within one column.
     * These need not be perfectly vertical.
     */
    if (dxi == 0) {       // Check for a vertical line
      current_yi += down_flag;  // Line is heading down, we just want to go to the bottom
      while (current_yi != cell_dest_yi + down_flag) {
        current_yi += dyi;
        const float next_mesh_line_y = mesh_index_to_ypos(current_yi);

        /**
         * Skip the calculations for an infinite slope.
         * For others the next X is the same so this can continue.
         * Calculate X at the next Y mesh line.
         */
        const float rx = inf_m_flag ? start[X_AXIS] : (next_mesh_line_y - c) / m;

        float z0 = z_correction_for_x_on_horizontal_mesh_line(rx, current_xi, current_yi) * bedlevel.fade_scaling_factor_for_z(end[Z_AXIS]);

        // Undefined parts of the Mesh in z_values[][] are NAN.
        // Replace NAN corrections with 0.0 to prevent NAN propagation.
        if (isnan(z0)) z0 = 0.0;

        const float ry = mesh_index_to_ypos(current_yi);

        /**
         * Without this check, it's possible to generate a zero length move, as in the case where
         * the line is heading down, starting exactly on a mesh line boundary. Since this is rare
         * it might be fine to remove this check and let planner.buffer_segment() filter it out.
         */
        if (ry != start[Y_AXIS]) {
          if (!inf_normalized_flag) {
            on_axis_distance = use_x_dist ? rx - start[X_AXIS] : ry - start[Y_AXIS];
            e_position = start[E_AXIS] + on_axis_distance * e_normalized_dist;
            z_position = start[Z_AXIS] + on_axis_distance * z_normalized_dist;
          }
          else {
            e_position = end[E_AXIS];
            z_position = end[Z_AXIS];
          }

          planner.buffer_segment(rx, ry, z_position + z0, e_position, feed_rate, extruder);
        } //else printf("FIRST MOVE PRUNED  ");
      }

      if (bedlevel.g26_debug_flag)
        debug_current_and_destination(PSTR("vertical move done in ubl.line_to_destination_cartesian()"));

      // At the final destination? Usually not, but when on a Y Mesh Line it's completed.
      if (mechanics.current_position[X_AXIS] != end[X_AXIS] || mechanics.current_position[Y_AXIS] != end[Y_AXIS])
        goto FINAL_MOVE;

      mechanics.set_current_to_destination();
      return;
    }

    /**
     * Handle horizontal lines that stay within one row.
     * These need not be perfectly horizontal.
     */
    if (dyi == 0) {
      current_xi += left_flag;
      while (current_xi != cell_dest_xi + left_flag) {
        current_xi += dxi;
        const float next_mesh_line_x = mesh_index_to_xpos(current_xi),
                    ry = m * next_mesh_line_x + c;   // Calculate Y at the next X mesh line

        float z0 = z_correction_for_y_on_vertical_mesh_line(ry, current_xi, current_yi) * bedlevel.fade_scaling_factor_for_z(end[Z_AXIS]);

        // Undefined parts of the Mesh in z_values[][] are NAN.
        // Replace NAN corrections with 0.0 to prevent NAN propagation.
        if (isnan(z0)) z0 = 0.0;

        const float rx = mesh_index_to_xpos(current_xi);

        /**
         * Without this check, it's possible to generate a zero length move, as in the case where
         * the line is heading left, starting exactly on a mesh line boundary. Since this is rare
         * it might be fine to remove this check and let planner.buffer_segment() filter it out.
         */
        if (rx != start[X_AXIS]) {
          if (!inf_normalized_flag) {
            on_axis_distance = use_x_dist ? rx - start[X_AXIS] : ry - start[Y_AXIS];
            e_position = start[E_AXIS] + on_axis_distance * e_normalized_dist;  // is based on X or Y because this is a horizontal move
            z_position = start[Z_AXIS] + on_axis_distance * z_normalized_dist;
          }
          else {
            e_position = end[E_AXIS];
            z_position = end[Z_AXIS];
          }

          if (!planner.buffer_segment(rx, ry, z_position + z0, e_position, feed_rate, extruder))
            break;
        } //else printf("FIRST MOVE PRUNED  ");
      }

      if (mechanics.current_position[X_AXIS] != end[X_AXIS] || mechanics.current_position[Y_AXIS] != end[Y_AXIS])
        goto FINAL_MOVE;

      mechanics.set_current_to_destination();
      return;
    }

    /**
     *
     * Handle the generic case of a line crossing both X and Y Mesh lines.
     *
     */

    int xi_cnt = cell_start_xi - cell_dest_xi,
        yi_cnt = cell_start_yi - cell_dest_yi;

    if (xi_cnt < 0) xi_cnt = -xi_cnt;
    if (yi_cnt < 0) yi_cnt = -yi_cnt;

    current_xi += left_flag;
    current_yi += down_flag;

    while (xi_cnt > 0 || yi_cnt > 0) {

      const float next_mesh_line_x = mesh_index_to_xpos(current_xi + dxi),
                  next_mesh_line_y = mesh_index_to_ypos(current_yi + dyi),
                  ry = m * next_mesh_line_x + c,    // Calculate Y at the next X mesh line
                  rx = (next_mesh_line_y - c) / m;  // Calculate X at the next Y mesh line
                                                    // (No need to worry about m being zero.
                                                    //  If that was the case, it was already detected
                                                    //  as a vertical line move above.)

      if (left_flag == (rx > next_mesh_line_x)) {   // Check if we hit the Y line first
        // Yes!  Crossing a Y Mesh Line next
        float z0 = z_correction_for_x_on_horizontal_mesh_line(rx, current_xi - left_flag, current_yi + dyi)
                   * bedlevel.fade_scaling_factor_for_z(end[Z_AXIS]);

        // Undefined parts of the Mesh in z_values[][] are NAN.
        // Replace NAN corrections with 0.0 to prevent NAN propagation.
        if (isnan(z0)) z0 = 0.0;

        if (!inf_normalized_flag) {
          on_axis_distance = use_x_dist ? rx - start[X_AXIS] : next_mesh_line_y - start[Y_AXIS];
          e_position = start[E_AXIS] + on_axis_distance * e_normalized_dist;
          z_position = start[Z_AXIS] + on_axis_distance * z_normalized_dist;
        }
        else {
          e_position = end[E_AXIS];
          z_position = end[Z_AXIS];
        }
        if (!planner.buffer_segment(rx, next_mesh_line_y, z_position + z0, e_position, feed_rate, extruder))
          break;
        current_yi += dyi;
        yi_cnt--;
      }
      else {
        // Yes!  Crossing a X Mesh Line next
        float z0 = z_correction_for_y_on_vertical_mesh_line(ry, current_xi + dxi, current_yi - down_flag)
                   * bedlevel.fade_scaling_factor_for_z(end[Z_AXIS]);

        // Undefined parts of the Mesh in z_values[][] are NAN.
        // Replace NAN corrections with 0.0 to prevent NAN propagation.
        if (isnan(z0)) z0 = 0.0;

        if (!inf_normalized_flag) {
          on_axis_distance = use_x_dist ? next_mesh_line_x - start[X_AXIS] : ry - start[Y_AXIS];
          e_position = start[E_AXIS] + on_axis_distance * e_normalized_dist;
          z_position = start[Z_AXIS] + on_axis_distance * z_normalized_dist;
        }
        else {
          e_position = end[E_AXIS];
          z_position = end[Z_AXIS];
        }

        if (!planner.buffer_segment(next_mesh_line_x, ry, z_position + z0, e_position, feed_rate, extruder))
          break;
        current_xi += dxi;
        xi_cnt--;
      }

      if (xi_cnt < 0 || yi_cnt < 0) break; // Too far! Exit the loop and go to FINAL_MOVE
    }

    if (bedlevel.g26_debug_flag)
      debug_current_and_destination(PSTR("generic move done in ubl.line_to_destination_cartesian()"));

    if (mechanics.current_position[X_AXIS] != end[X_AXIS] || mechanics.current_position[Y_AXIS] != end[Y_AXIS])
      goto FINAL_MOVE;

    mechanics.set_current_to_destination();
  }

#endif // UBL_DELTA

#endif // AUTO_BED_LEVELING_UBL

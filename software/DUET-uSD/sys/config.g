; Configuration file for Duet WiFi (firmware version 3.3)
; executed by the firmware on start-up
;
; generated by RepRapFirmware Configuration Tool v3.3.15 on Tue Mar 14 2023 14:12:21 GMT+0000 (GMT)

; General preferences
G90                                     ; send absolute coordinates...
M83                                     ; ...but relative extruder moves
M550 P"LabEmbryoCam"                    ; set printer name
M669 K1                                 ; select CoreXY mode

; Network
M551 P"radix"                           ; set password
M552 P0.0.0.0 S1                        ; enable network and acquire dynamic address via DHCP
M586 P0 S1                              ; enable HTTP
M586 P1 S0                              ; disable FTP
M586 P2 S0                              ; disable Telnet

; Drives
M569 P0 S1                              ; physical drive 0 goes forwards
M569 P1 S1                              ; physical drive 1 goes forwards
M569 P2 S1                              ; physical drive 2 goes forwards
M569 P3 S1                              ; physical drive 3 goes forwards
M584 X0 Y1 Z2 E3                        ; set drive mapping
M350 X16 Y16 Z8 E16 I1                 ; configure microstepping with interpolation
M92 X100.00 Y100.00 Z400.00 E420.00       ; set steps per mm
M566 X900.00 Y900.00 Z60.00 E120.00     ; set maximum instantaneous speed changes (mm/min)
M203 X6000.00 Y6000.00 Z180.00 E1200.00 ; set maximum speeds (mm/min)
M201 X500.00 Y500.00 Z20.00 E250.00     ; set accelerations (mm/s^2)
M906 X800 Y800 Z500 E800 I60            ; set motor currents (mA) and motor idle factor in per cent
M84 S1                                ; Set idle timeout

; Axis Limits
M208 X0 Y0 Z0 S1                        ; set axis minima
M208 X210 Y100 Z100 S0                   ; set axis maxima

; Endstops
M574 X2 S1 P"xstop"                     ; configure switch-type (e.g. microswitch) endstop for high end on X via pin xstop
M574 Y1 S1 P"ystop"                     ; configure switch-type (e.g. microswitch) endstop for low end on Y via pin ystop
M574 Z1 S1 P"zstop"                     ; configure switch-type (e.g. microswitch) endstop for low end on Z via pin zstop

; Z-Probe
M558 P0 H5 F120 T6000                   ; disable Z probe but set dive height, probe speed and travel speed
M557 X15:210 Y15:80 S20                 ; define mesh grid

; Heaters
M140 H-1                                ; disable heated bed (overrides default heater mapping)

; Fans
M950 F0 C"fan0" Q500                    ; create fan 0 on pin fan0 and set its frequency
M106 P0 S0 H-1                          ; set fan 0 value. Thermostatic control is turned off
M950 F1 C"fan1" Q500                    ; create fan 1 on pin fan1 and set its frequency
M106 P1 S1 H-1                          ; set fan 1 value. Thermostatic control is turned off

; Tools

; Custom settings are not defined


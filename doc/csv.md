# CSV for OT-2
## Column Definition
0. Step
1. Step Type
2. Comment (Step comment at the top row of each step)
3. Source Labware / Command target labware
4. Source Slot / Command target slot
5. Source Well/ Command target well (optional)
6. Source Volume (µL)
7. Source Name (the last word can be hex color code starting from #)
8. Dest Labware / User Friendly Description of command
9. Dest Slot / Command option integral
10. Dest Well / Command option string
11. Dest Volume (µL) / Command option float
12. Dest Name (the last word can be hex color code starting from #)
13. Handling Volume (µL)
14. Change Tip ([blank]/always/per source/per destination/once/never)
15. Aspirate Rate (1-6)
16. Prewet Cycle
17. Source Delay (sec)
18. Source Touch Tip (speed 0.25-1)
19. Source Air Gap (µL)
20. Dispense Rate (1-6)
21. Pipetting Cycle
22. Dest Delay (sec)
23. Dest Touch Tip (speed 0.25-1)
24. Dest Air Gap (uL)
25. Reverse Mode ([blank]/Bin/Source)
26. Distribute (No/Allow/Force [Bin/Source])
27. Pipette

## Mix
- (hidden option, deleted before export) before source
- (hidden option, deleted before export) before step
- mixing cycle and target are indicated by prewet cycle (source) or pipetting cycle (dest) and handling volume specify mixing volume.
- All pipetting options apart from prewet and pipetting follows parent transfer.

## Miscellanoeous Command
- Temperature Module Control
- Magnetic Module Control
- Thermocycler Module Control
- Heater-Shaker Module Control
- Pause
### Temperature Module Control
#### Dest Well
- deactivate
- start
#### Dest Volume
- Target temperature (4-95)
#### Comment (Description)
- Temperature Module (Slot [Destination Slot]): Set temperature at [Source Volume] degree Celsius
- Temperature Module (Slot [Destination Slot]): Start setting temperature at [Source Volume] degree Celsius
- Temperature Module (Slot [Destination Slot]): Deactivate
### Magnetic Module Control
#### Dest Well 
- disengage
- engage
#### Dest Volume
- height from bottom
#### Comment (Description)
- Magnetic Module (Slot [Destination Slot]): Disengage
- Magnetic Module (Slot [Destination Slot]): Engage labware default
- Magnetic Module (Slot [Destination Slot]): Engage at [Source Volume] mm from base
### Pause
#### Dest Slot
- Waiting time in seconds (blank or 0 stands for resume manually)
#### Dest Well (multiple options allowed separated by space)
- beep
- temperature
- (hidden option, deleted before export) before source
- (hidden option, deleted before export) before step 
#### Dest Volume
- Target temperature
#### Comment (Description)
- Pause: Resume manually from Opentrons app.
- Pause: Pause for hh hr mm min ss sec. 
- Pause: Pause for hh:mm:ss. Beep On.
- Pause: Pause until Temperature module in slot [Destination Slot] reaches [Source Volume] degree Celsius
- Pause: Pause until Heater-Shaker module in slot [Destination Slot] reaches [Source Volume] degree Celsius 
### Heater-Shaker Module Control
#### Dest Slot
- Target speed (200-3000)
#### Dest Well (multiple options allowed)
- deactivate_heater
- deactivate_shaker
- start_heater (set temeprature and not wait until temmpareture reaches)
- lock
- unlock
#### Dest Volume
- Target temperature (37-95)
#### Comment (Description)
- Heater-Shaker Module (Slot [Destination Slot]): Set temperature at [Source Volume] degree Celsius
- Heater-Shaker Module (Slot [Destination Slot]): Start setting temperature at [Source Volume] degree Celsius
- Heater-Shaker Module (Slot [Destination Slot]): Deactivate Heater
- Heater-Shaker Module (Slot [Destination Slot]): Set shaking speed at [Source Slot] rpm
- Heater-Shaker Module (Slot [Destination Slot]): Set shaking speed at [Source Slot] rpm and set temperature at [Source Volume] degree Celsius
- Heater-Shaker Module (Slot [Destination Slot]): Set shaking speed at [Source Slot] rpm and start setting temperature at [Source Volume] degree Celsius
- Heater-Shaker Module (Slot [Destination Slot]): Open Latch
- Heater-Shaker Module (Slot [Destination Slot]): Close Latch
### Thermocycler Module Control
Specifically this module is controled by multiple steps. Lid and block temperature should be specified by separated command step.
Thermocycler module and the labware in the thermocycler is always in slot 7.
#### Dest Slot
- Hold time in sec
- Block max volume 
#### Dest Well (multiple options allowed)
- deactivate_block
- deactivate_lid
- block (can not be used with lid)
- lid (can not be used with block)
- open_lid
- close_lid
- execute_profile (profile can not be used with other options. Specify profile filename in the second argument)
#### Dest Volume
- Target temperature (Block:4-99; Lid: 37-110)
- Repetition of profile (converted to integral in the Python script)
#### Comment (Description)
- Thermocycler Module (Vol: [Source Slot]): Deactivate block
- Thermocycler Module (Vol: [Source Slot]): Deactivate lid
- Thermocycler Module: Set [lid/block] temperature at [Source Volume] degree Celsius
- Thermocycler Module: Set [lid/block] temperature at [Source Volume] degree Celsius and hold hh hr mm min ss sec (if hold option applied)
- Thermocycler Module (Vol: [Source Slot]): Set [block] temperature at [Source Volume] degree Celsius
- Thermocycler Module (Vol: [Source Slot]): Open lid
- Thermocycler Module (Vol: [Source Slot]): Close lid
- Thermocycler Module (Vol: [Source Slot]): Execute profile ([Source Well]) for [Source Volume] time(s)

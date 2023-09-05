# How Pipette Works in Transfer/Distribute/Consolidate/Mix methods
## Sequence
0. Volume/Offset is inspected
    1. Carryover cycle is calculated and if necessary the transfer volume is split
    2. If the cycle exceeds max_carryover, the program should raise error.
    3. At this step, float volume for many-to-many transfer is converted to list of float.
    4. If source/destination volume is given, aspirate/dispense offset is calculated.
        1. Offset is automatically calculated from source well volume, on converted script using .depth/.lendth/.width/.diameter property
        2. PCR plate: assuming the well shape as a corn sliced at its 2/5 height, bearing 3/5 times diameter of bottom compared to top. offset_from_bottom = ( (2 * depth / diameter) ** (2/3) * (27 / 4 * depth * diameter ** 2 + 150 * volume / pi()) ** 3 - 3 * depth) / 2
        3. Other case: Assuming flat bottom well, offset_from_bottom = volume / (area) ; area = pi() * diameter ** 2 / 4 or area = width * length
        4. For a safe margin, ( depth of labware / 5 ) or 10 mm lower than calculation will be used, with minimum limit of 0.5 mm
    5. If no volume given, mm from bottom offset should be given instead.
    6. If aspirate/dispense flow rate is specified, applied here
1. Replace tips (apart from new_tip='never')
    1. remove existing tip if the pipette has
        1. If the other pipette also has tip, remove it too (use protocol.loaded_instruments property)
    2. pick up new tip
    3. Options:
        1. always: Replace new tip before every apsirate
        2. never: Never drop tip. It can be used for dry run.
        3. once: Replace tip at the beginning of the step.
        4. onSource: Replace tip when next source is differnt (no tip replace during carryover)
        5. onDest: Replace tip when next destination is different (no tip replace during carryover)
        6. Blank (auto): Similar to on source but if the dest is not empty well before transfer, replace tip. If no volume given, behave as always to take safer side
2. Optional: Prewet the tip
    1. As same as official, 2/3 of max volume of pipette tip is aspirate/dispensed at source
    2. For safety margin, if source volume is given, source * 0.8 is upper limit and appropriate offset for the mixing substep is applied
    3. If no source volume is given, transfer volume (before carryover split, volume[i]) is the maximum limit of prewet.
    4. Note that this option is to make tip wet in advance. For mixing, use before mix option.
3. Optional: Mix specified volume before aspirate, for specified times
    1. Aspirate offset is applied
    2. Aspirate delay is applied
    3. In reverse mode, disposal volume is aspirated in advance to avoid bubble
    4. For safety margin, if source volume is given, source * 0.8 is upper limit and appropriate offset for the mixing substep is applied
    5. Skipped in consolidate mode
4.1. Aspirate specified volume
    1. Aspirate rate is specified. Default=Max
    2. In case reverse mode, specified volume as disposal volume is further aspirated.
4.2. Optional Delay for specified seconds, parking at the specified position.
    1. Default = 1 mm from bottom, if volume is given, calculated value.
5.1 Optional: Touch tip at specified offset
    1. Same offset from bottom is applied over step
    2. If offset is not given, -1 mm from top is applied
    3. Before touch tip aspirate delay is applied if specified, but at top of well 
5.2. Optional: Air Gap with specified volume, to prevent drop falling on deck
    1. As same as official, consolidate causes air gap as separater (air gap at every source)
    2. Before movement, delay is applied if specified
    3. During consolidate, air gap option works as putting spacer between different source liquid.
6.1. Dispense specified volume
    1. Release air gap at the top of dest well before dispense
    2. At this point, if volume is given, assess if dest is empty or not
    3. During distribute, no air gap is applied
6.2. Optional Delay for specified seconds, parking at the specified position.
    1. Default = 0.5 mm from bottom, if volume is given, calculated value.
7. Optional: Mix specified volume after dispense, for specified times
    1. Dispense offset is applied
    2. For safety margin, if source volume is given, source * 0.8 is upper limit and appropriate offset for the mixing substep is applied
    3. Dispense delay is applied if specified
    4. Skipped in distribute mode
8.1. Optional: Touch tip at specified offset
    1. Same offset from bottom is applied over step
    2. If offset is not given, -1 mm from top is applied
8.2. Optional: Air Gap with specified volume, to prevent drop falling on deck
    1. accompanied with drop tip
    2. during distribute mode, no air gap is applied between dest to dest transfer
16. Optional: blowout to specified location, one of trash, source well, destination well
    1. Default=Trash
    2. In distribute mode or reverse mode, blow out to dest well is not allowed and forced to trash.
17. Drop tip to trash, according to next condition and option
    1. always: remove tip when current pipette is not used in next step (to refrain from floating dirty tip above deck). e.g. Next is module step, next pipette is different type...
    2. never: Never drop tip. Unlike official, no tip robot movement is allowed for dry run.
        1. remove tip when another pipette is used (to refrain from floating dirty tip above deck).
    3. once: The tip will be replaced once a step. If next step is never, do not drop tip. Otherwise, drop tip.
    4. onSource: Drop tip when next source is differnt (no tip replace during carryover).
        1. remove tip when current pipette is not used in next step (to refrain from floating dirty tip above deck). e.g. Next is module step, next pipette is different type...
    5. onDest: Drop tip when next destination is different (no tip replace during carryover). 
        1. remove tip when current pipette is not used in next step (to refrain from floating dirty tip above deck). e.g. Next is module step, next pipette is different type...
    6. Blank (auto): Similar to on source but if the current dest is not empty well before transfer, drop tip (tip will be replaced if condition met during carryover)
        1. remove tip when current pipette is not used in next step (to refrain from floating dirty tip above deck). e.g. Next is module step, next pipette is different type...
        2. if source is identical and pipette is unchanged, keep the tip over step to step.
18. Aspirate/dispense rate is resumed to default
## List structure of parameters
### Liquidhandling volumes
#### volume (transfer/distribute/consolidate)
- float, or list of float to specify liquid hanlding order and handling volumes
- no carryover assessed
#### handling_volumes
- list (i th transfer path) of list (j th carryover/mix cycle)
#### cont_volumes
- list (k th continuous transfer path) of list (l th item of continous transfer path) of list (j th carryover cycle) 
### Source/Destination/Mix volumes
#### source_volumes
#### dest_volumes
#### mix_volumes
#### aspirate_offsets
#### dispense_offsets
## Requisites of parameters
### Pipette:
- Object
### Labware: 
- Labware object
- Each step has only one aspirate/dispense/mix labware (aspirating from/dispensing to varied labwares requires to split steps)
### Wells
- List of str (e.g. ['A1', 'B2']), in handling order. The wells are sorted before converted to Python protocol
- Length of the list is
  - Transfer: same length
  - Distribute: aspirate wells = 1, dispense wells > 1
  - Consolidate: aspirate wells > 1, dispense wells = 1
  - Mix: same length
### Volume
- Float, list of float, or taple of float
  - Float for identical value over the step
  - List of float specifies each volume for each liquid hanlding
  - Tapple of two float specifies the range of volume for every liquid hanlding. By default the volume is linear gradient between two values keeping float order
    - You can specify the curve by adding optional parameter gradient: lambda.
### Offset
- float or None

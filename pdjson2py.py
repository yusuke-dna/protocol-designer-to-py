try:
    import json, datetime, argparse, math, time
except ImportError as e:
    missing_module = str(e).split(" ")[-1].replace("'", "")
    print(f"It appears that the module {missing_module} is not installed.")
    print("Please run the following command to install the required dependencies:")
    print(f"pip install {missing_module}")
    exit()

parser = argparse.ArgumentParser()
parser.add_argument('arg1', type=str, help='The JSON file exported from Protocol Designer.')
parser.add_argument('arg2', type=str, nargs='?', default=None, help='Specify "auto" for automatic tiprack assignment. For used tiprack reuse, input "C1" (if single pipette is installed) or "A1/E10" ([for left pipette]/[for right pipette], no blank allowed if both installed) to specify starting (filled) well of the used tiprack. Input "None" to keep Protocol Designer tip assignment.')
parser.add_argument('arg3', type=str, nargs='?', default=None, help='Slack Webhook URL here like "https://hooks.slack.com/services/[YOUR]/[WEBHOOK]/[URL]" for notification via Slack.')
parser.add_argument('arg4', type=str, nargs='?', default=None, help='Command mode for debug. Command hash is used to generate python script.')
args = parser.parse_args()

def bottom2top(json_dict: dict, labware_name_full: str, well_name: str, v_mm:float) -> float:
    # indeed, top2bottom too. Only used in byCommand mode.
    well_depth = json_dict['labwareDefinitions'][labware_name_full]['wells'][well_name]['depth']
    return v_mm - well_depth

def used_tiprack_parse_command(tiprack_assign=None) -> list:        
    starting_tip_well = tiprack_assign.split('/')
    for i in range(len(starting_tip_well)):
        well_name = starting_tip_well[i].upper()
        alphabetic_part = ''.join(filter(str.isalpha, well_name))
        numeric_part = ''.join(filter(str.isdigit, well_name))
        numeric_part = str(int(numeric_part))
        if alphabetic_part == '':
            row = (int(numeric_part) - 1) % 8
            col = (int(numeric_part) - 1) // 8 + 1
            alphabetic_part = chr(row + ord('A'))
            numeric_part = str(col)
        starting_tip_well[i] = alphabetic_part + numeric_part 
    return starting_tip_well

# Receive e.g. A1/E10 or C1 and returns {'left': 'A1', 'right': 'E10'} or {'left': 'C1', 'right': 'C1'}
# This function should be updated to receive left="A1", right="E10" instead and return {'left': 'A1', 'right': 'E10'}
def used_tiprack_parse(tiprack_assign=None) -> dict:        
    starting_tip_well = {}
    starting_tip_well['left'] = tiprack_assign.split('/')[0]
    if len(tiprack_assign.split('/')) == 1:
        starting_tip_well['right'] = tiprack_assign.split('/')[0]
    else:  
        starting_tip_well['right'] = tiprack_assign.split('/')[1]
    for key in starting_tip_well.keys():
        well_name = starting_tip_well[key].upper()
        alphabetic_part = ''.join(filter(str.isalpha, well_name))
        numeric_part = ''.join(filter(str.isdigit, well_name))
        numeric_part = str(int(numeric_part))
        if alphabetic_part == '':
            row = (int(numeric_part) - 1) % 8
            col = (int(numeric_part) - 1) // 8 + 1
            alphabetic_part = chr(row + ord('A'))
            numeric_part = str(col)
        starting_tip_well[key] = alphabetic_part + numeric_part 
    return starting_tip_well

# CSV parser have to convert 6 level flow rate to flow rate µL/sec 

def nested_method_output(f, pdjson):
    f.write(f'''
    def liquid_handling(mode, pipette, volume, aspirate_labware=None, aspirate_wells=None, 
                    dispense_labware=None, dispense_wells=None, 
                    repetitions=None, mix_labware=None, mix_wells=None, new_tip='always', 
                    aspirate_offset={pdjson['designerApplication']['data']['defaultValues']['aspirate_mmFromBottom']}, dispense_offset={pdjson['designerApplication']['data']['defaultValues']['dispense_mmFromBottom']}, mix_offset={pdjson['designerApplication']['data']['defaultValues']['dispense_mmFromBottom']},
                    source_volumes=None, dest_volumes=None, mix_volumes=None,
                    aspirate_flow_rate=None, dispense_flow_rate=None, mix_before=None, mix_after=None, 
                    aspirate_touch_tip=False, aspirate_touch_tip_offset=None,
                    dispense_touch_tip=False, dispense_touch_tip_offset=None, 
                    mix_touch_tip=False, mix_touch_tip_offset=None, pre_wet_tip=False,
                    aspirate_air_gap=0.0, dispense_air_gap=0.0, mix_air_gap=0.0, aspirate_delay=None, aspirate_delay_bottom=1.0, dispense_delay=None, dispense_delay_bottom=0.5,
                    blow_out=False, blowout_location='trash', disposal_volume=None):
        try:
            nonlocal protocol, step
            if step == 0:
                raise ValueError('Step number must be 1 or more.')
            default_touchtip_offset_from_top = {pdjson['designerApplication']['data']['defaultValues']['touchTip_mmFromTop']}
            default_blowout_offset_from_top = {pdjson['designerApplication']['data']['defaultValues']['blowout_mmFromTop']}
            min_volume = pipette.min_volume
            max_volume = pipette.max_volume
            max_carryover = {pdjson['metadata'].get('max_carryover', 10)}
            if aspirate_labware != None:
                aspirate_labware_name = aspirate_labware.load_name
                if len(aspirate_wells) == 1:
                    aspirate_wells = [aspirate_wells[0]] * len(dispense_wells)
            if dispense_labware != None:
                dispense_labware_name = dispense_labware.load_name
                if len(dispense_wells) == 1:
                    dispense_wells = [dispense_wells[0]] * len(aspirate_wells)
            if mix_labware != None:
                mix_labware_name = mix_labware.load_name
            if disposal_volume == None and mode == 'distribute': # disposal volume is always applied in distribute mode.
                disposal_volume = min_volume
            elif disposal_volume == None or mode == 'consolidate':
                disposal_volume = 0.0
            elif disposal_volume > 0.0 and disposal_volume < min_volume:
                disposal_volume = min_volume
            if aspirate_air_gap > 0.0 and aspirate_air_gap < min_volume:
                aspirate_air_gap = min_volume
            if dispense_air_gap > 0.0 and dispense_air_gap < min_volume:
                dispense_air_gap = min_volume
            if new_tip == '' or new_tip == None:
                if dest_volumes != None:
                    new_tip = 'auto'
                else:
                    new_tip = 'always'
            if aspirate_touch_tip == True:
                aspirate_touch_tip = 1
            if dispense_touch_tip == True:
                dispense_touch_tip = 1
            if mix_touch_tip == True:
                mix_touch_tip = 1
            if mode == 'distribute' or mode == 'consolidate':   # mix before/mix after is not supported in distribute/consolidate mode
                mix_before = None
                mix_after = None
            if mode == 'mix':
                aspirate_wells = mix_wells
                dispense_wells = mix_wells
                dispense_air_gap = mix_air_gap
                dispense_touch_tip = mix_touch_tip
        
            # 0.1 Volume/repetitions inspection and handling volume is converted to list (each well-to-well path/mixing well) of list (carryover/mixing cycle including carryover).
  
            if type(volume) == int or type(volume) == float or (type(volume) == str and volume.isnumeric()):
                volume = float(volume)
                if mode != 'mix':
                    volumes = [volume] * len(aspirate_wells)
                else:
                    volumes = [volume] * len(mix_wells)
            elif type(volume) == list:
                for i in range (len(volume)):
                    if type(volume[i]) == int or type(volume[i]) == float or (type(volume[i]) == str and volume[i].isnumeric()):
                        volumes.append(float(volume[i]))
                    else:
                        raise TypeError(f'volume must be float or list of float, not {{type(volume[i])}}')
            else:
                raise TypeError(f'volume must be float or list of float, not {{type(volume)}}')

            if mode == 'mix':
                if type(repetitions) == int or type(repetitions) == float or (type(repetitions) == str and repetitions.isnumeric()):
                    repetitions = int(repetitions)
                    repetitions = [repetitions] * len(mix_wells)
                elif type(repetitions) == list:
                    for i in range (len(repetitions)):
                        if type(repetitions[i]) == int or type(repetitions[i]) == float or (type(repetitions[i]) == str and repetitions[i].isnumeric()):
                            repetitions.append(float(repetitions[i]))
                        else:
                            raise TypeError(f'repetitions must be float or list of float, not {{type(repetitions[i])}}')
                else:
                    raise TypeError(f'repetitions must be float or list of float, not {{type(repetitions)}}')

            handling_volumes = [[] for _ in range(len(volumes))]  # volumes list is converted to handling_volumes list
            for i in range(len(volumes)):
                if mode != 'mix':
                    if volumes[i] > max_volume - aspirate_air_gap - disposal_volume:       # disposal volume for mix stands for mixing with at least specified volume aspirated to avoid bubbles. The disposal volume will be blow out to trash.
                        left_volume = volumes[i]
                        carryover_cycle = math.ceil(left_volume / (max_volume - aspirate_air_gap - disposal_volume))
                        if carryover_cycle > max_carryover:
                            raise ValueError(f'Volume {{volumes[i]}} exceeds maximum carryover for pipette {{pipette.instrument_name}}.')
                        aliquot_volume = math.ceil( left_volume / carryover_cycle )
                        while left_volume > 0:
                            handling_volumes[i].append(min(aliquot_volume, left_volume))
                            left_volume -= min(aliquot_volume, left_volume)
                    else:
                        handling_volumes[i] = [volumes[i]]
                else:
                    if volumes[i] > max_volume - disposal_volume:       # disposal volume for mix stands for mixing with at least specified volume aspirated to avoid bubbles. The disposal volume will be blow out to trash.
                        mix_cycle = math.ceil(repetitions[i] * volumes[i] / (max_volume - disposal_volume))
                        if mix_cycle / repetitions[i] > max_carryover:
                            raise ValueError(f'Volume {{volumes[i]}} for mix exceeds maximum carryover for pipette {{pipette.instrument_name}}.')
                        handling_volumes[i] = [(ceil(repetitions[i] * volumes[i] / mix_cycle))] * mix_cycle  # the length of handling_volume[i] specifies mixing cycle repetition.
                    else:
                        handling_volumes[i] = [volumes[i]] * repetitions[i]

            # 0.2 Aspirate/Dipense/mix offset is calculated. List (each transfer pass) of list (carryover).
            if source_volumes != None and mode != 'mix':
                aspirate_offsets = []
                for i in range(len(source_volumes)):
                    aspirate_offsets.append([])
                    for j in range(len(handling_volumes[i])):
                        diameter = aspirate_labware[aspirate_wells[i]].diameter
                        width = aspirate_labware[aspirate_wells[i]].width
                        length = aspirate_labware[aspirate_wells[i]].length
                        depth = aspirate_labware[aspirate_wells[i]].depth
                        # source_left_volume is source_volume - all transfer volume until j - all disposal volume until j.
                        source_left_volume = source_volumes[i] - sum(handling_volumes[i][:(j+1)]) - disposal_volume * (j + 1)
                        if 'PCR' in aspirate_labware_name:
                            aspirate_offsets[i].append(max(0.5, ( (2 * depth / diameter) ** (2/3) * (27 / 4 * depth * diameter ** 2 + 150 * source_left_volume / math.pi) ** 3 - 3 * depth) / 2 - min (depth / 5 , 10)))
                        elif aspirate_labware[aspirate_wells[i]].diameter == None:
                            aspirate_offsets[i].append(max(0.5, source_left_volume / (width * length) - min (depth / 5 , 10)))
                        else:
                            aspirate_offsets[i].append(max(0.5, source_left_volume * 4 / (math.pi * diameter ** 2) - min (depth / 5 , 10)))
            elif mode != 'mix':
                aspirate_offsets = [aspirate_offset] * len(aspirate_wells)
                for i in range(len(aspirate_offsets)):
                    aspirate_offsets[i] = [aspirate_offsets[i]]
                    if len(handling_volumes[i]) > 1:
                        aspirate_offsets[i] = aspirate_offsets[i] * len(handling_volumes[i])
            if dest_volumes != None and mode != 'mix':
                dispense_offsets = []
                for i in range(len(dest_volumes)):
                    dispense_offsets.append([])
                    for j in range(len(handling_volumes[i])):
                        diameter = dispense_labware[dispense_wells[i]].diameter
                        width = dispense_labware[dispense_wells[i]].width
                        length = dispense_labware[dispense_wells[i]].length
                        depth = dispense_labware[dispense_wells[i]].depth
                        # dest_left_volume is dest_volume + all transfer volume until j.
                        dest_left_volume = dest_volumes[i] + sum(handling_volumes[i][:j])
                        if 'PCR' in dispense_labware_name:
                            dispense_offsets[i].append(max(0.5, ( (2 * depth / diameter) ** (2/3) * (27 / 4 * depth * diameter ** 2 + 150 * dest_left_volume / math.pi) ** 3 - 3 * depth) / 2 - min (depth / 5 , 10)))
                        elif dispense_labware[dispense_wells[i]].diameter == None:
                            dispense_offsets[i].append(max(0.5, dest_left_volume / (width * length) - min (depth / 5 , 10)))
                        else:
                            dispense_offsets[i].append(max(0.5, dest_left_volume * 4 / (math.pi * diameter ** 2) - min (depth / 5 , 10)))
            elif mode != 'mix':
                dispense_offsets = [dispense_offset] * len(dispense_wells)
                for i in range(len(dispense_offsets)):
                    dispense_offsets[i] = [dispense_offsets[i]]
                    if len(handling_volumes[i]) > 1:
                        dispense_offsets[i] = dispense_offsets[i] * len(handling_volumes[i])
            if mix_volumes != None and mode == 'mix':
                mix_offsets = []
                for i in range(len(mix_volumes)):
                    mix_offsets.append([])
                    for j in range(len(handling_volumes[i])):   # mix offset is identical over i, but stored as list for consistency to aspirate/dispense offset.
                        diameter = mix_labware[mix_wells[i]].diameter
                        width = mix_labware[mix_wells[i]].width
                        length = mix_labware[mix_wells[i]].length
                        depth = mix_labware[mix_wells[i]].depth
                        mix_left_volume = mix_volumes[i] - handling_volumes[i][j] - disposal_volume
                        if 'PCR' in mix_labware_name:
                            mix_offsets[i].append(max(0.5, ( (2 * depth / diameter) ** (2/3) * (27 / 4 * depth * diameter ** 2 + 150 * mix_left_volume / math.pi) ** 3 - 3 * depth) / 2 - min (depth / 5 , 10)))
                        elif mix_labware[mix_wells[i]].diameter == None:
                            mix_offsets[i].append(max(0.5, mix_left_volume / (width * length) - min (depth / 5 , 10)))
                        else:
                            mix_offsets[i].append(max(0.5, mix_left_volume * 4 / (math.pi * diameter ** 2) - min (depth / 5 , 10)))
                aspirate_offsets = mix_offsets  # to reuse following script without modification
                dispense_offsets = mix_offsets
            elif mode == 'mix':
                mix_offsets = [mix_offset] * len(mix_wells)
                for i in range(len(mix_offsets)):
                    mix_offsets[i] = [mix_offsets[i]]
                    if len(handling_volumes[i]) > 1:
                        mix_offsets[i] = mix_offsets[i] * len(handling_volumes[i])
                aspirate_offsets = mix_offsets  # to reuse following script without modification
                dispense_offsets = mix_offsets

            # 0.3 Distribute/Consolidate pass is arranged based on volume. List (each distribute) of List (each well-to-well path) of list (carryover).
            cont_volumes = []
            cont_aspirate_offsets = []
            cont_dispense_offsets = []
            cont_start_flag = []
            for i in range(len(handling_volumes)):
                if len(handling_volumes[i]) > 1:    # in case of carry over, one distribute/consolidate cycle assigned
                    cont_volumes.append([handling_volumes[i]])           # [..,[[carry,over,volumes]]]
                    cont_aspirate_offsets.append(aspirate_offsets[i])
                    cont_dispense_offsets.append(dispense_offsets[i])
                    cont_start_flag.append(True)
                elif len(cont_volumes) == 0:  # fist path to be distributed 
                    cont_volumes.append([handling_volumes[i]])  # [[[transfer_volume: float]]]
                    cont_aspirate_offsets.append(aspirate_offsets[i])
                    cont_dispense_offsets.append(dispense_offsets[i])
                    cont_start_flag.append(True)
                elif mode == 'distribute' and sum(item for sublist in cont_volumes[-1] for item in sublist) + handling_volumes[i][0] + disposal_volume + aspirate_air_gap <= max_volume: # if next path does not exeed max volume, distribute cycle is kept same
                    cont_volumes[-1].append(handling_volumes[i])    # [..,[..,[former_volume],[transfered_volume]]]
                    cont_aspirate_offsets[-1][0] = min(cont_aspirate_offsets[-1][0], aspirate_offsets[i][0])
                    cont_dispense_offsets[-1][0] = min(cont_dispense_offsets[-1][0], dispense_offsets[i][0])
                    cont_start_flag.append(False)
                elif mode == 'consolidate' and sum(item for sublist in cont_volumes[-1] for item in sublist) + len(cont_volumes[-1]) * dispense_air_gap + handling_volumes[i][0] + disposal_volume + dispense_air_gap <= max_volume: # if next path does not exeed max volume, distribute cycle is kept same
                    cont_volumes[-1].append(handling_volumes[i])    # [..,[..,[former_volume],[transfered_volume]]]
                    cont_aspirate_offsets[-1][0] = min(cont_aspirate_offsets[-1][0], aspirate_offsets[i][0])
                    cont_dispense_offsets[-1][0] = min(cont_dispense_offsets[-1][0], dispense_offsets[i][0])
                    cont_start_flag.append(False)
                else:   # new distribute cycle when it exceeds max volume
                    cont_volumes.append([handling_volumes[i]])
                    cont_aspirate_offsets.append(aspirate_offsets[i])
                    cont_dispense_offsets.append(dispense_offsets[i])
                    cont_start_flag.append(True)

            # 0.4 Pipette offset at prewet and mix_before/after is calculated. For mix, these are ignored.
            if mode != 'mix':
                if pre_wet_tip and source_volumes != None:
                    pre_wet_tip_offsets = []
                    pre_wet_volumes = []
                    for i in range(len(aspirate_wells)):
                        diameter = aspirate_labware[aspirate_wells[i]].diameter
                        width = aspirate_labware[aspirate_wells[i]].width
                        length = aspirate_labware[aspirate_wells[i]].length
                        depth = aspirate_labware[aspirate_wells[i]].depth
                        pre_wet_volumes.append(min (max_volume * 2/3, source_volumes[i] * 0.8))
                        pre_wet_left_volume = source_volumes[i] - pre_wet_volumes[i]
                        if 'PCR' in aspirate_labware_name:
                            pre_wet_tip_offsets.append(max(0.5, ( (2 * depth / diameter) ** (2/3) * (27 / 4 * depth * diameter ** 2 + 150 * pre_wet_left_volume / math.pi) ** 3 - 3 * depth) / 2 - min (depth / 5 , 10)))
                        elif aspirate_labware[aspirate_wells[i]].diameter == None:
                            pre_wet_tip_offsets.append(max(0.5, pre_wet_left_volume / (width * length) - min (depth / 5 , 10)))
                        else:
                            pre_wet_tip_offsets.append(max(0.5, pre_wet_left_volume * 4 / (math.pi * diameter ** 2) - min (depth / 5 , 10)))
                elif pre_wet_tip:
                    pre_wet_tip_offsets = [aspirate_offset] * len(aspirate_wells)
                    if mode == 'distribute':
                        pre_wet_volumes = [min(max_volume * 2/3, sum(item for sublist in handling_volumes for item in sublist))] * len(aspirate_wells)
                    else:
                        pre_wet_volumes = [min(max_volume * 2/3, sum(item for item in handling_volumes[i]))] * len(aspirate_wells)
                if mix_before:
                    if mix_before[0] == None and mix_before[1] == None:
                        mix_before[0] = 3
                        mix_before[1] = max_volume - disposal_volume
                    elif mix_before[0] == None:
                        mix_before[0] = ceil( mix_before[1] / (max_volume - disposal_volume) )
                        if mix_before[0] > max_carryover:
                            raise ValueError(f'Volume {{mix_before[1]}} exceeds maximum carryover for pipette {{pipette.instrument_name}}.')
                        mix_before[1] = max_volume - disposal_volume
                    elif mix_before[1] > max_volume - disposal_volume:
                        mix_before_loop = mix_before[1] / (max_volume - disposal_volume)
                        if mix_before_loop > max_carryover:
                            raise ValueError(f'Volume {{mix_before[1]}} exceeds maximum carryover for pipette {{pipette.instrument_name}}.')
                        mix_before[0] = math.ceil(mix_before[0] * mix_before_loop)
                        mix_before[1] = max_volume - disposal_volume
                    if source_volumes != None:
                        mix_before_offsets = []
                        mix_before_cycles = []
                        mix_before_volumes = []
                        for i in range(len(aspirate_wells)):
                            diameter = aspirate_labware[aspirate_wells[i]].diameter
                            width = aspirate_labware[aspirate_wells[i]].width
                            length = aspirate_labware[aspirate_wells[i]].length
                            depth = aspirate_labware[aspirate_wells[i]].depth
                            if mix_before[1] > source_volumes[i] * 0.8: # if mix_before specified more than source volume or close, limit mixing volume and multiply cycle.
                                mix_before_volume.append(source_volumes[i] * 0.8 - disposal_volume)
                                mix_before_loop = ( mix_before[1] / (source_volumes[i] * 0.8 - disposal_volume) )
                                if mix_before_loop > max_carryover:
                                    raise ValueError(f'Mixing volume {{mix_before[1]}} for Source volume {{source_volumes[i]}} exceeds maximum carryover for pipette {{pipette.instrument_name}}.')
                                mix_before_cycles.append(ceil(mix_before[0] * mix_before_loop))
                            else:
                                mix_before_cycles.append(mix_before[0])
                                mix_before_volumes.append(mix_before[1])
                            mix_before_left_volume = source_volumes[i] - mix_before_volumes[i]
                            if 'PCR' in aspirate_labware_name:
                                mix_before_offsets.append(max(0.5, ( (2 * depth / diameter) ** (2/3) * (27 / 4 * depth * diameter ** 2 + 150 * mix_before_left_volume / math.pi) ** 3 - 3 * depth) / 2 - min (depth / 5 , 10)))
                            elif aspirate_labware[aspirate_wells[i]].diameter == None:
                                mix_before_offsets.append(max(0.5, mix_before_left_volume / (width * length) - min (depth / 5 , 10)))
                            else:
                                mix_before_offsets.append(max(0.5, mix_before_left_volume * 4 / (math.pi * diameter ** 2) - min (depth / 5 , 10)))
                    elif mix_before:
                        mix_before_offsets = [aspirate_offset] * len(aspirate_wells)
                        mix_before_cycles = [mix_before[0]] * len(aspirate_wells)
                        mix_before_volumes = [mix_before[1]] * len(aspirate_wells)
                if mix_after:
                    if mix_after[0] == None and mix_after[1] == None:
                        mix_after[0] = 3
                        mix_after[1] = max_volume
                    elif mix_after[0] == None:
                        mix_after[0] = ceil( mix_after[1] / (max_volume) )
                        if mix_after[0] > max_carryover:
                            raise ValueError(f'Volume {{mix_after[1]}} exceeds maximum carryover for pipette {{pipette.instrument_name}}.')
                        mix_after[1] = max_volume
                    elif mix_after[1] > max_volume:
                        mix_after_loop = mix_after[1] / (max_volume)
                        if mix_after_loop > max_carryover:
                            raise ValueError(f'Volume {{mix_after[1]}} exceeds maximum carryover for pipette {{pipette.instrument_name}}.')
                        mix_after[0] = math.ceil(mix_after[0] * mix_after_loop)
                        mix_after[1] = max_volume
                    if dest_volumes != None:
                        mix_after_offsets = []
                        mix_after_cycles = []
                        mix_after_volumes = []
                        for i in range(len(dispense_wells)):
                            diameter = dispense_labware[dispense_wells[i]].diameter
                            width = dispense_labware[dispense_wells[i]].width
                            length = dispense_labware[dispense_wells[i]].length
                            depth = dispense_labware[dispense_wells[i]].depth
                            mix_after_left_volume = dest_volumes[i] + sum(handling_volumes[i])
                            if mix_after[1] > mix_after_left_volume * 0.8: # if mix_after specified more than dest volume after transfer or close, limit mixing volume and multiply cycle.
                                mix_after_volumes.append(mix_after_left_volume * 0.8)
                                mix_after_loop = ( mix_after[1] / (mix_after_left_volume * 0.8) )
                                if mix_after_loop > max_carryover:
                                    raise ValueError(f'Mixing volume {{mix_after[1]}} for Destination volume {{mix_after_left_volume}} exceeds maximum carryover for pipette {{pipette.instrument_name}}.')
                                mix_after_cycles.append(ceil(mix_after[0] * mix_after_loop))
                            else:
                                mix_after_cycles.append(mix_after[0])
                                mix_after_volumes.append(mix_after[1])
                            if 'PCR' in dispense_labware_name:
                                mix_after_offsets.append(max(0.5, ( (2 * depth / diameter) ** (2/3) * (27 / 4 * depth * diameter ** 2 + 150 * mix_after_left_volume / math.pi) ** 3 - 3 * depth) / 2 - min (depth / 5 , 10)))
                            elif dispense_labware[dispense_wells[i]].diameter == None:
                                mix_after_offsets.append(max(0.5, mix_after_left_volume / (width * length) - min (depth / 5 , 10)))
                            else:
                                mix_after_offsets.append(max(0.5, mix_after_left_volume * 4 / (math.pi * diameter ** 2) - min (depth / 5 , 10)))
                    elif mix_after:
                        mix_after_offsets = [dispense_offset] * len(dispense_wells)
                        mix_after_cycles = [mix_after[0]] * len(dispense_wells)
                        mix_after_volumes = [mix_after[1]] * len(dispense_wells)

            # 0.5 Flow rate is calculated and applied.
            default_aspirate_flow_rate = pipette.flow_rate.aspirate # default flow rate depends on API version. in API ver ≥ 2.6, twice higher than Protocol Designer default.
            default_dispense_flow_rate = pipette.flow_rate.dispense # default flow rate depends on API version. in API ver ≥ 2.6, twice higher than Protocol Designer default.
            if aspirate_flow_rate != None:
                pipette.flow_rate.aspirate = aspirate_flow_rate
            default_dispense_flow_rate = pipette.flow_rate.dispense
            if dispense_flow_rate != None:
                pipette.flow_rate.dispense = dispense_flow_rate        

            # 1. Tip is replaced according to new_tip option. Dispense air gap is applied before dropping tip if specified.
            if new_tip != 'never':   # Replace tip for all options apart from 'never' at the beginning of the step
                for key in protocol.loaded_instruments:
                    if protocol.loaded_instruments[key].has_tip:
                        protocol.loaded_instruments[key].drop_tip()
                pipette.pick_up_tip()

            if not pipette.has_tip:     # for debug, 'never' option also pick up tip
                protocol.comment(f"new_tip='never' is ignored for debug.")
                pipette.pick_up_tip()

            k = -1   # k th distribute/consolidate cycle

            for i in range(len(handling_volumes)):
                if cont_start_flag[i]:
                    k += 1
                    l = 0   # counter for consolidate/distribute cycle
                else:
                    l += 1
                cont_end_flag = cont_start_flag[i+1] if len(cont_start_flag) > i+1 else True

                # Official protocol designer does not allow change perSource or perDest when consolidate/ditribute is selected. This script supports them for consistency and for no-tip-replacement during carryover (hight risk of cross contamination).
                if i > 0 and ((new_tip == 'perSource' and aspirate_wells[i-1] != aspirate_wells[i]) or (new_tip == 'perDest' and dispense_wells[i-1] != dispense_wells[i]) or (new_tip == 'auto' and (aspirate_wells[i-1] != aspirate_wells[i] or dest_volumes[i-1] > 0))):  # Replace tip per source/destination
                    if pipette.has_tip:
                        if dispense_air_gap:
                            pipette.air_gap(dispense_air_gap)
                            if dispense_delay:
                                protocol.delay(seconds=dispense_delay)
                        pipette.drop_tip()
                    pipette.pick_up_tip()
                    
                for j in range(len(handling_volumes[i])):               # each carryover/mixing cycle
                    if debug == True:
                        protocol.comment(f"i={{i}}, j={{j}}, k={{k}}, l={{l}}")
                    if mode == 'distribute' and not cont_start_flag[i]: # skipped during path between dest to dest in distribute mode
                        pass
                    elif mode == 'mix':                                   # no tip replacement during mixing the same well (over same i)
                        pass 
                    elif not (i == 0 and j == 0) and (new_tip == 'always' or (new_tip == 'auto' and dest_volumes[i] > 0 )):  # Replace tip per each transfer, 'auto' replace tip when dest is filled (tip is contaminated)
                        if pipette.has_tip:
                            if dispense_air_gap:
                                if protocol.is_simulating == True:
                                    protocol.comment("Additional air gap during carry over.")
                                pipette.air_gap(dispense_air_gap)
                                if dispense_delay:
                                    protocol.delay(seconds=dispense_delay)
                            pipette.drop_tip()
                        pipette.pick_up_tip()

            # 2. Pre-wetting tip
                    if mode == 'distribute' and not cont_start_flag[i]: # skipped during path between dest to dest in distribute mode. Prewet seems igonred in Protocol Designer ver 6.2.2. but kept active for consistency.
                        pass
                    elif mode == 'mix':                                   # skipped in mix mode
                        pass
                    elif (pre_wet_tip and j == 0 and l == 0) or (mode == 'consolidate' and cont_start_flag[i]):  # prewet will be done only at the first cycle of carry over, assuming carry over makes the tip wet, or the first source of consolidate
                        if mode == 'distribute' and debug == True:
                            protocol.comment("Additional pre-wetting.")
                        elif debug == True:
                            protocol.comment("Pre-wet")
                        pipette.aspirate(pre_wet_volumes[i], aspirate_labware[aspirate_wells[i]].bottom(pre_wet_tip_offsets[i]))
                        if aspirate_delay:  # no height adjustemnt for pre-wetting
                            protocol.delay(seconds=aspirate_delay)
                        pipette.dispense(pre_wet_volumes[i], aspirate_labware[aspirate_wells[i]].bottom(pre_wet_tip_offsets[i]))
                        if aspirate_delay:  # assuming delay is determined by source solution property, aspirate delay is applied.
                            protocol.delay(seconds=dispense_delay)

            # 3. Mix before aspirating
                    if mode == 'consolidate' or mode == 'mix': # skipped in consolidate mode and mix mode
                        pass
                    elif mix_before and j == 0 and ((mode == 'transfer' or mode == 'reverse') or (mode == 'distribute' and l == 0)):    # first cycle of either carryover of transfer/reverse or distribute                   # mix_before only at the first cycle of carryover 
                        if debug == True:
                            protocol.comment("mix before")
                        for _ in range(mix_before_cycles[i]):
                            pipette.aspirate(mix_before_volumes[i], aspirate_labware[aspirate_wells[i]].bottom(mix_before_offsets[i]))
                            if aspirate_delay:
                                if source_volumes == None:
                                    pipette.move_to(aspirate_labware[aspirate_wells[i]].bottom(aspirate_delay_bottom),speed=20, publish=False) # slowed the speed to reduce vibration
                                protocol.delay(seconds=aspirate_delay)
                            pipette.dispense(mix_before_volumes[i], aspirate_labware[aspirate_wells[i]].bottom(mix_before_offsets[i]))
                            if aspirate_delay:  # assuming delay is determined by source solution property, aspirate delay is applied.
                                if source_volumes == None:
                                    pipette.move_to(aspirate_labware[aspirate_wells[i]].bottom(dispense_delay_bottom),speed=20, publish=False) # slowed the speed to reduce vibration
                                protocol.delay(seconds=dispense_delay)

            # 4. Release air gap during carryover
                    if mode == 'distribute' and not cont_end_flag: # skipped during path between dest to dest in distribute mode, for accuracy of dispense volume
                        pass
                    elif mode == 'consolidate' and not cont_end_flag: # skipped during path between source to source in consolidate mode
                        pass
                    elif mode == 'mix': # skipped in mix mode
                        pass
                    elif blow_out:  # dispense air gap is applied in case blowout is specified
                        pass
                    elif len(handling_volumes[i]) > 1 and j > 0 and aspirate_air_gap:    # air gap for aspirate during return trip of carryover is released here
                        pipette.dispense(aspirate_air_gap, aspirate_labware[aspirate_wells[i]].top())
                        if dispense_delay:
                            protocol.delay(seconds=dispense_delay)                

            # 5. Aspirate and delay
                    if mode == 'mix':
                        if disposal_volume and j == 0: # disposal volume is aspirated only at the first cycle of mix
                            handling_volume = handling_volumes[i][j] + disposal_volume
                        else:
                            handling_volume = handling_volumes[i][j]    
                        if debug == True:
                            protocol.comment("aspirate-mix")
                        pipette.aspirate(handling_volume, mix_labware[mix_wells[i]].bottom(mix_offsets[i][j]))
                        if aspirate_delay:
                            protocol.delay(seconds=aspirate_delay)

                    elif mode == 'transfer' or mode == 'consolidate':
                        aspirate_volume = handling_volumes[i][j] + disposal_volume
                        if debug == True:
                            protocol.comment("aspirate-transfer/consoludate")
                        pipette.aspirate(aspirate_volume, aspirate_labware[aspirate_wells[i]].bottom(aspirate_offsets[i][j]))
                        if aspirate_delay:
                            if source_volumes == None:
                                pipette.move_to(aspirate_labware[aspirate_wells[i]].bottom(aspirate_delay_bottom),speed=20) # slowed the speed to reduce vibration
                            protocol.delay(seconds=aspirate_delay)

                    elif mode == 'distribute' and cont_start_flag[i]:
                        if debug == True:
                            protocol.comment("aspirate-distribute")
                        if len(cont_volumes[k][0]) == 1:    # in case no carryover
                            aspirate_volume = sum(item[0] for item in cont_volumes[k]) + disposal_volume
                        elif len(cont_volumes[k][0]) > 1:   # in case carryover
                            aspirate_volume = cont_volumes[k][0][j]  # Disposal volume is ignored during carryover. Contrary to transfer, where disposal volume is always counted for reverse mode
                        pipette.aspirate(aspirate_volume, aspirate_labware[aspirate_wells[i]].bottom(cont_aspirate_offsets[k][j]))
                        if aspirate_delay:
                            if source_volumes == None:
                                pipette.move_to(aspirate_labware[aspirate_wells[i]].bottom(aspirate_delay_bottom),speed=20) # slowed the speed to reduce vibration
                            protocol.delay(seconds=aspirate_delay)
                            
            # 6. Touch tip
                    if mode == 'distribute' and not cont_start_flag[i]: # skipped during path between dest to dest in distribute mode
                        pass
                    elif mode == 'mix':
                        pass
                    elif aspirate_touch_tip:
                        if aspirate_touch_tip_offset == None:
                            pipette.touch_tip(v_offset=default_touchtip_offset_from_top, speed=aspirate_touch_tip)
                        else:
                            offset = aspirate_touch_tip_offset - aspirate_labware[aspirate_wells[i]].depth
                            pipette.touch_tip(v_offset=offset, speed=aspirate_touch_tip)

            # 7 Air gap and delay
                    if mode == 'distribute' and not cont_start_flag[i]: # skipped during path between dest to dest in distribute mode
                        pass
                    elif mode == 'mix': # skipped in mix mode
                        pass
                    elif aspirate_air_gap:
                        pipette.air_gap(aspirate_air_gap)
                        if aspirate_delay:
                            protocol.delay(seconds=aspirate_delay)

            # 8. Release air gap and delay, 
                    if mode == 'distribute' and not cont_start_flag[i]: # skipped during path between dest to dest in distribute mode
                        pass
                    elif mode == 'mix': # skipped in mix mode
                        pass
                    elif mode == 'consolidate' and not cont_end_flag:
                        pass
                    elif aspirate_air_gap:
                        pipette.dispense(aspirate_air_gap, dispense_labware[dispense_wells[i]].top())
                        if dispense_delay:
                            protocol.delay(seconds=dispense_delay)

            # 9. dispense/mix and delay
                    if mode == 'mix':
                        if debug == True:
                            protocol.comment("dispense-mix")
                        pipette.dispense(handling_volumes[i][j], mix_labware[mix_wells[i]].bottom(mix_offsets[i][j]))
                        if dispense_delay:
                            protocol.delay(seconds=dispense_delay)

                    elif mode == 'transfer' or mode == 'reverse' or mode == 'distribute':
                        if debug == True:
                            protocol.comment("dispense-transfer/reverses/distribute")
                        pipette.dispense(handling_volumes[i][j], dispense_labware[dispense_wells[i]].bottom(dispense_offsets[i][j]))
                        if dispense_delay:
                            if dest_volumes == None:
                                pipette.move_to(dispense_labware[dispense_wells[i]].bottom(dispense_delay_bottom),speed=20) # slowed the speed to reduce vibration
                            protocol.delay(seconds=dispense_delay)

                    elif mode == 'consolidate' and cont_end_flag:
                        if debug == True:
                            protocol.comment("dispense-consolidate")
                        if aspirate_air_gap:    # liquid is dispensed one by one to avoid bubble if air gap is specified
                            if debug == True:
                                protocol.comment("dispense-consolidate, dispense step by step")
                            for m in range(len(cont_volumes[k])):
                                pipette.dispense(cont_volumes[k][m][j], dispense_labware[dispense_wells[i]].bottom(cont_dispense_offsets[k][j]))      
                                if pipette.current_volume > 0:
                                    pipette.dispense(aspirate_air_gap, dispense_labware[dispense_wells[i]].top()) 
                            if dispense_delay:
                                if dest_volumes == None:
                                    pipette.move_to(dispense_labware[dispense_wells[i]].bottom(dispense_delay_bottom),speed=20) # slowed the speed to reduce vibration
                                protocol.delay(seconds=dispense_delay)
                        else:
                            if debug == True:
                                protocol.comment("dispense-consolidate")
                            pipette.dispense(pipette.current_volume, dispense_labware[dispense_wells[i]].bottom(cont_dispense_offsets[k][j])) # dispense all the volume in the pipette if no air gap
                            if dispense_delay:
                                if dest_volumes == None:
                                    pipette.move_to(dispense_labware[dispense_wells[i]].bottom(dispense_delay_bottom),speed=20) # slowed the speed to reduce vibration
                                protocol.delay(seconds=dispense_delay)
                                        
            # 10. Mix after dispensing
                    if mode == 'consolidate' or mode == 'mix': # skipped in distribute/mix mode
                        pass
                    elif mix_after and j == len(handling_volumes[i]) - 1 and ((mode == 'transfer' or mode == 'reverse') or (mode == 'consolidate' and l == len(cont_volumes[k]) - 1)):    # last cycle of either carryover of transfer/reverse or consolidate
                        if debug == True:
                            protocol.comment("mix after")
                        for _ in range(mix_after_cycles[i]):
                            pipette.aspirate(mix_after_volumes[i], dispense_labware[dispense_wells[i]].bottom(mix_after_offsets[i]))
                            if dispense_delay:  # assuming delay is determined by dest solution property, dispense delay is applied.
                                if dest_volumes == None:
                                    pipette.move_to(dispense_labware[dispense_wells[i]].bottom(dispense_delay_bottom),speed=20) # slowed the speed to reduce vibration
                                protocol.delay(seconds=dispense_delay)
                            pipette.dispense(mix_after_volumes[i], dispense_labware[dispense_wells[i]].bottom(mix_after_offsets[i]))
                            if dispense_delay:
                                if dest_volumes == None:
                                    pipette.move_to(dispense_labware[dispense_wells[i]].bottom(dispense_delay_bottom),speed=20) # slowed the speed to reduce vibration
                                protocol.delay(seconds=dispense_delay)

            # 11. Blow out at dest (applied every carryover cycle)
                    if blow_out:
                        if mode == 'distribute' or mode == 'reverse': # dest blow out is not allowed to distribute or reverse mode
                            pass
                        elif mode == 'consolidate' and not cont_end_flag: # skipped during path between source to source in consolidate mode
                            pass
                        elif mode == 'mix' and j < len(handling_volumes[i]) - 1: # skipped in mix mode apart from the last cycle
                            pass
                        elif blowout_location == 'destination well' and disposal_volume == 0:   # blow out to destination well is not allowed in distribute mode
                            if debug == True:
                                protocol.comment("browout-dest")
                            pipette.blow_out(dispense_labware[dispense_wells[i]].top(default_blowout_offset_from_top))

            # 12. Touch tip
                    if mode == 'consolidate' and not cont_end_flag: # skipped during path between source to source in consolidate mode
                        pass
                    elif mode == 'mix' and j < len(handling_volumes[i]) - 1: # skipped in mix mode apart from the last cycle
                        pass
                    elif dispense_touch_tip:
                        if dispense_touch_tip_offset == None:
                            offset = default_touchtip_offset_from_top
                        else:
                            offset = dispense_touch_tip_offset - dispense_labware[dispense_wells[i]].depth
                        pipette.touch_tip(v_offset=offset, speed=aspirate_touch_tip)

            # 13. Air gap and delay for carryover                           
                    if mode == 'distribute' and not cont_end_flag: # skipped during path between dest to dest in distribute mode, for accuracy of dispense volume
                        pass
                    elif mode == 'consolidate' and not cont_end_flag: # skipped during path between source to source in consolidate mode
                        pass
                    elif mode == 'mix' and j < len(handling_volumes[i]) - 1: # skipped in mix mode apart from the last cycle
                        pass
                    elif blow_out or disposal_volume > 0:  # dispense air gap is applied in case blowout is specified
                        if dispense_air_gap:
                            if debug == True:
                                protocol.comment("additional dispense air gap")
                            pipette.air_gap(dispense_air_gap)
                            if dispense_delay:
                                protocol.delay(seconds=dispense_delay)
                    elif len(handling_volumes[i]) > 1 and j < len(handling_volumes[i]) - 1 and aspirate_air_gap:    # air gap for aspirate is applied for return trip of carryover
                        if debug == True:
                            protocol.comment("additional aspirate air gap")
                        pipette.air_gap(aspirate_air_gap)
                        if dispense_delay:
                            protocol.delay(seconds=dispense_delay)
                                    
            # 14. Blow out at source or trash (applied every carryover cycle)
                    if blow_out or disposal_volume:
                        if mode == 'distribute' and not cont_end_flag: # skipped during path between dest to dest in distribute mode
                            pass
                        elif mode == 'consolidate' and not cont_end_flag: # skipped during path between source to source in consolidate mode
                            pass
                        elif mode == 'mix' and j < len(handling_volumes[i]) - 1: # skipped in mix mode apart from the last cycle
                            pass
                        elif blowout_location == 'source well':
                            if debug == True:
                                protocol.comment("browout-source")
                            pipette.blow_out(aspirate_labware[aspirate_wells[i]].top(default_blowout_offset_from_top))                            
                        elif blowout_location == 'destination well' and disposal_volume == 0:   # blow out to destination well is not allowed in distribute mode
                            pass
                        else:
                            if debug == True:
                                protocol.comment("browout-trash")
                            pipette.blow_out(protocol.fixed_trash['A1'])

            # 15. Drop tip when air gap specified, for consistensy of Protocol designer
            if dispense_air_gap:
                pipette.air_gap(dispense_air_gap)
                if dispense_delay:
                    protocol.delay(seconds=dispense_delay)
                pipette.drop_tip()
               
            # 16. Resume flow rate
            pipette.flow_rate.aspirate = default_aspirate_flow_rate
            pipette.flow_rate.dispense = default_dispense_flow_rate
        except Exception as e:
            raise Exception(f"{{str(sys.exc_info()[0]).split('.')[-1][:-2]}} in Step {{step}}. transfer-{{mode}}: {{e}}, line {{sys.exc_info()[2].tb_lineno}}")
''')

def sort_wells(wells, first_sort, second_sort) -> list:
    # reorder list based on first_sort and second_sort.
    if first_sort == None and second_sort == None:
        return wells
    elif first_sort == 't2b':
        if second_sort == 'l2r':  # default
            return wells
        elif second_sort == 'r2l':
            wells = sorted(wells, key=lambda x: (-int(x[1:]), x[0]))
            return wells
    elif first_sort == 'b2t':
        if second_sort == 'l2r':
            wells = sorted(wells, key=lambda x: (int(x[1:]), -ord(x[0])))
            return wells
        elif second_sort == 'r2l':  # inverted order of the wells
            return wells[::-1]
    elif first_sort == 'l2r':
        if second_sort == 't2b':
            wells = sorted(wells, key=lambda x: (x[0], int(x[1:]))) # sort by row first, then column
            return wells
        elif second_sort == 'b2t':
            wells = sorted(wells, key=lambda x: (-ord(x[0]), int(x[1:]))) # sort by column first, then row in reverse order
            return wells
    elif first_sort == 'r2l':
        if second_sort == 't2b':
            wells = sorted(wells, key=lambda x: (x[0], -int(x[1:]))) # sort by column first, then row in reverse order
            return wells
        elif second_sort == 'b2t':
            wells = sorted(wells, key=lambda x: (-ord(x[0]), -int(x[1:]))) # sort by row first in reverse order, then column in reverse order
            return wells

def otjson2py_command(filename: str, tiprack_assign=None, webhook_url=None) -> str:

    # Specifying starting well of the used tiprack.
    if tiprack_assign == None or tiprack_assign == 'auto':
        used_tiprack = False
    else:
        used_tiprack = True
        starting_tip_well = used_tiprack_parse(tiprack_assign)
        
    try:
        with open(filename, 'r') as f:
            pdjson = json.load(f)
    except FileNotFoundError:
        return 'Error: File not found.'

    # to parse pipettes, labwares and modules from JSON file to variables
    metadata = pdjson['metadata']
    metadata['created'] = datetime.datetime.fromtimestamp(float(metadata['created'])/1000).strftime('%Y-%m-%d %H:%M:%S.%f')
    metadata['lastModified'] = datetime.datetime.fromtimestamp(float(metadata['lastModified'])/1000).strftime('%Y-%m-%d %H:%M:%S.%f')
    for key, value in metadata.items(): 
        if value is None:
            metadata[key] = "n/a"
    metadata['tags'] = str(metadata['tags'])
    if used_tiprack == True:
        metadata['apiLevel'] = '2.13'   # mitigate the bug of OT2 API 2.14
    else:
        metadata['apiLevel'] = '2.14'
    module_dict = {
        'temperatureModuleV2':'temperature module gen2',
        'magneticModuleV2':'magnetic module gen2',
        'thermocyclerModuleV2':'thermocycler module gen2',
        'heaterShakerModuleV1':'heaterShakerModuleV1',
        'magneticModuleV1':'magnetic module',
        'temperatureModuleV1':'temperature module',
        'thermocyclerModuleV1':'thermocycler module'
    }
  
    pipettes_name = {}
    pipettes = {}
    for key, value in pdjson['pipettes'].items():
        pipettes_name[key] = value['name']
        pipettes[key] = ""

    labwares_name = {}
    labwares = {}
    for key, value in pdjson['labware'].items():
        labwares_name[key] = value['definitionId'].split('/')[1]
        labwares[key] = ""
    labwares['fixedTrash'] = 'protocol.fixed_trash'

    modules_name = {}
    modules = {}
    for key, value in pdjson['modules'].items():
        modules_name[key] = module_dict[str(value['model'])]
        modules[key] = ""

    with open('output.py', 'w') as f:

# Print header
        f.write('from opentrons import protocol_api\nimport json, urllib.request, math\n\n')
        f.write(f'metadata = {metadata}\n\n')
        if webhook_url != None:
            f.write(f'webhook_url = "{webhook_url}"\n\n')
            f.write("def send_to_slack(webhook_url, message):\n    data = {\n        'text': message,\n        'username': 'MyBot',\n        'icon_emoji': ':robot_face:'\n    }\n    data = json.dumps(data).encode('utf-8')\n\n    headers = {'Content-Type': 'application/json'}\n\n    req = urllib.request.Request(webhook_url, data, headers)\n    with urllib.request.urlopen(req) as res:\n        if res.getcode() != 200:\n            raise ValueError(\n                'Request to slack returned an error %s, the response is:\\n%s'\n                % (res.getcode(), res.read().decode('utf-8'))\n            )\n\n")
        f.write('def run(protocol: protocol_api.ProtocolContext):\n')

# For every command...
        for i in range(len(pdjson['commands'])):
            command_step = pdjson['commands'][i]

# Serial numbering for debug
            if i%20 == 0 and i > 19:
                f.write(f'\n# command no. {i}\n')

# load pipettes
            if command_step['commandType'] == 'loadPipette':
                mount = command_step['params']['mount']
                if tiprack_assign == 'auto' or used_tiprack == True:   # comparison "tiprack_assign == auto" is for backword compatibility and could be removed in future.
                    tiprack_name = pdjson['designerApplication']['data']['pipetteTiprackAssignments'][command_step['params']['pipetteId']]
                    tipracks = []
                    for key, value in pdjson['designerApplication']['data']['savedStepForms']['__INITIAL_DECK_SETUP_STEP__']['labwareLocationUpdate'].items() :
                        if key.split(':')[len(key.split(':'))-1] == tiprack_name :
                            tipracks.append(labwares[key])
                            tipracks_str = '[' + ']['.join(tipracks) + ']'
                    ini_tiprack = tipracks[0]
                    f.write(f"    pipette{i} = protocol.load_instrument(instrument_name='{pipettes_name[command_step['params']['pipetteId']]}', mount='{mount}',tip_racks={tipracks_str})\n")
                    if used_tiprack == True:
                        f.write(f"    pipette{i}.starting_tip = {ini_tiprack}.well('{starting_tip_well[mount]}')\n")
                else:
                    f.write(f"    pipette{i} = protocol.load_instrument(instrument_name='{pipettes_name[command_step['params']['pipetteId']]}', mount='{mount}')\n")
                pipettes[command_step['params']['pipetteId']] = f"{mount}_pipette"

# load labwares and modules
            if command_step['commandType'] == 'loadLabware':
                if list(command_step['params']['location'].keys())[0] == 'slotName':
                    f.write(f"    labware{i} = protocol.load_labware(load_name='{labwares_name[command_step['params']['labwareId']]}', "
                            f"location='{command_step['params']['location']['slotName']}')\n")
                    labwares[command_step['params']['labwareId']] = f"labware{i}"
                else:
                    f.write(f"    labware{i} = {modules[command_step['params']['location']['moduleId']]}"
                            f".load_labware('{labwares_name[command_step['params']['labwareId']]}')\n")
                    labwares[command_step['params']['labwareId']] = f"labware{i}"
            elif command_step['commandType'] == 'loadModule':
                f.write(f"    module{i} = protocol.load_module(module_name='{modules_name[command_step['params']['moduleId']]}',"
                        f"location='{command_step['params']['location']['slotName']}')\n")
                modules[command_step['params']['moduleId']] = f"module{i}"

# liquid handling
            if command_step['commandType'] == 'pickUpTip' and (tiprack_assign == 'auto' or used_tiprack == True):
                f.write(f"    {pipettes[command_step['params']['pipetteId']]}.pick_up_tip()\n")
            elif command_step['commandType'] == 'pickUpTip':
                f.write(f"    {pipettes[command_step['params']['pipetteId']]}"
                        f".pick_up_tip(location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'])\n")
            elif command_step['commandType'] == 'aspirate':
                if command_step.get('meta') != None:
                    if command_step['meta'].get('isAirGap') == True:
                        f.write(f"    protocol.comment('Air gap')\n")
                f.write(f"    {pipettes[command_step['params']['pipetteId']]}.flow_rate.aspirate = {command_step['params']['flowRate']}\n")
                f.write(f"    {pipettes[command_step['params']['pipetteId']]}"
                        f".aspirate(volume={command_step['params']['volume']}, "
                        f"location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'].bottom(z={command_step['params']['wellLocation']['offset']['z']}))\n")
            elif command_step['commandType'] == 'dispense':
                f.write(f"    {pipettes[command_step['params']['pipetteId']]}.flow_rate.dispense = {command_step['params']['flowRate']}\n")
                f.write(f"    {pipettes[command_step['params']['pipetteId']]}"
                        f".dispense(volume={command_step['params']['volume']}, "
                        f"location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'].bottom(z={command_step['params']['wellLocation']['offset']['z']}))\n")
            elif command_step['commandType'] == 'blowout':
                f.write(f"    {pipettes[command_step['params']['pipetteId']]}"
                        f".blow_out(location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'].bottom(z={command_step['params']['wellLocation']['offset']['z']}))\n")
            elif command_step['commandType'] == 'dropTip':
                f.write(f"    {pipettes[command_step['params']['pipetteId']]}.drop_tip()\n")
            elif command_step['commandType'] == 'touchTip':
                f.write(f"    {pipettes[command_step['params']['pipetteId']]}"
                        f".touch_tip(location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'], "
                        f"v_offset={bottom2top(pdjson, str(command_step['params']['labwareId'].split(':')[1]), command_step['params']['wellName'], command_step['params']['wellLocation']['offset']['z'])})\n")
            elif command_step['commandType'] == 'moveToWell':   # used in delay
                f.write(f"    {pipettes[command_step['params']['pipetteId']]}." 
                        f"move_to(location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'].bottom(z={command_step['params']['wellLocation']['offset']['z']}))\n")

# heater-shaker module control
            elif command_step['commandType'] == 'heaterShaker/closeLabwareLatch':
                f.write(f"    {modules[command_step['params']['moduleId']]}." 
                        f"close_labware_latch()\n")
            elif command_step['commandType'] == 'heaterShaker/setTargetTemperature':
                f.write(f"    {modules[command_step['params']['moduleId']]}." 
                        f"set_target_temperature({command_step['params']['celsius']})\n")
            elif command_step['commandType'] == 'heaterShaker/setAndWaitForTemperature':
                f.write(f"    {modules[command_step['params']['moduleId']]}." 
                        f"set_and_wait_for_temperature({command_step['params']['celsius']})\n")
            elif command_step['commandType'] == 'heaterShaker/setAndWaitForShakeSpeed':
                f.write(f"    {modules[command_step['params']['moduleId']]}." 
                        f"set_and_wait_for_shake_speed({command_step['params']['rpm']})\n")
            elif command_step['commandType'] == 'heaterShaker/deactivateShaker':
                f.write(f"    {modules[command_step['params']['moduleId']]}." 
                        f"deactivate_shaker()\n")
            elif command_step['commandType'] == 'heaterShaker/deactivateHeater':
                f.write(f"    {modules[command_step['params']['moduleId']]}." 
                        f"deactivate_heater()\n")
            elif command_step['commandType'] == 'heaterShaker/waitForTemperature':
                f.write(f"    {modules[command_step['params']['moduleId']]}." 
                        f"wait_for_temperature()\n")

# magnetic module control
            elif command_step['commandType'] == 'magneticModule/engage':
                f.write(f"    {modules[command_step['params']['moduleId']]}.engage(height_from_base={command_step['params']['height']})\n")
            elif command_step['commandType'] == 'magneticModule/disengage':
                f.write(f"    {modules[command_step['params']['moduleId']]}.disengage()\n")

# temperature module control
            elif command_step['commandType'] == 'temperatureModule/setTargetTemperature':
                if pdjson['commands'][i+1].get('commandType') == 'temperatureModule/waitForTemperature':
                    f.write(f"    {modules[command_step['params']['moduleId']]}.set_temperature(celsius={command_step['params']['celsius']})\n")
                else:
                    f.write(f"    {modules[command_step['params']['moduleId']]}.start_set_temperature(celsius={command_step['params']['celsius']}) # Hidden API returns immediately. Wait temperture step will follow always.\n")
            elif command_step['commandType'] == 'temperatureModule/waitForTemperature':
                f.write(f"    while ({modules[command_step['params']['moduleId']]}.temperature != {command_step['params']['celsius']} and not protocol.is_simulating()):\n        protocol.delay(seconds=1)\n")
            elif command_step['commandType'] == 'temperatureModule/deactivate':
                f.write(f"    {modules[command_step['params']['moduleId']]}.deactivate()\n")
            
# thermocycler module control
            elif command_step['commandType'] == 'thermocycler/openLid':
                f.write(f"    {modules[command_step['params']['moduleId']]}.open_lid()\n")
            elif command_step['commandType'] == 'thermocycler/closeLid':
                f.write(f"    {modules[command_step['params']['moduleId']]}.close_lid()\n")
            elif command_step['commandType'] == 'thermocycler/deactivateBlock':
                f.write(f"    {modules[command_step['params']['moduleId']]}.deactivate_block()\n")
            elif command_step['commandType'] == 'thermocycler/deactivateLid':
                f.write(f"    {modules[command_step['params']['moduleId']]}.deactivate_lid()\n")
            elif command_step['commandType'] == 'thermocycler/setTargetBlockTemperature':
                f.write(f"    {modules[command_step['params']['moduleId']]}.set_block_temperature(temperature={command_step['params']['celsius']})\n")
            elif command_step['commandType'] == 'thermocycler/setTargetLidTemperature':
                f.write(f"    {modules[command_step['params']['moduleId']]}.set_lid_temperature(temperature={command_step['params']['celsius']})\n")
            elif command_step['commandType'] == 'thermocycler/waitForLidTemperature' or command_step['commandType'] == 'thermocycler/waitForBlockTemperature':
                None # set_*_temperature pauses protocol untill the temperature reaches
            elif command_step['commandType'] == 'thermocycler/deactivateLid':
                f.write(f"    {modules[command_step['params']['moduleId']]}.deactivate_lid()\n")
            elif command_step['commandType'] == 'thermocycler/deactivateBlock':
                f.write(f"    {modules[command_step['params']['moduleId']]}.deactivate_block()\n")
            elif command_step['commandType'] == 'thermocycler/runProfile':
                steps = []
                for item in command_step['params']['profile']:
                    step = {}
                    step['temperature'],step['hold_time_seconds'] = item['celsius'],item['holdSeconds']
                    steps.append(step)
                steps = str(steps)
                f.write(f"    {modules[command_step['params']['moduleId']]}.execute_profile(steps={steps},repetitions=1,block_max_volume={command_step['params']['blockMaxVolumeUl']})\n")
# other control      
            elif command_step['commandType'] == 'delay' and command_step['params'].get('seconds') == None :
                message = str(command_step['params'].get('message'))
                if webhook_url != None:
                    f.write(f'    send_to_slack(webhook_url,"Your OT-2 has said: {message}")\n')
                f.write(f"    protocol.pause(msg='{message}')\n")
            elif command_step['commandType'] == 'delay' :
                message = str(command_step['params'].get('message'))
                f.write(f"    protocol.delay(seconds={command_step['params'].get('seconds')}")
                if message == 'None':
                    f.write(')\n')
                else:
                    f.write(f", msg='{message}')\n")
            elif command_step['commandType'] == 'loadLiquid' or command_step['commandType'] == 'loadPipette' or command_step['commandType'] == 'loadLabware' or command_step['commandType'] == 'loadModule':
                # loading liquid, begins from API 2.14 is not supported.
                None
            else:
                f.write(f"not parsed: {command_step['commandType']}, {i}\n")

        if webhook_url != None:
            f.write(f'    send_to_slack(webhook_url,"Your OT-2 protocol has just completed!")\n')

# pdjson is a dictionary format data from Protocol Designer, apart from a special transfer-path option: 'reverse', a listed form of volume, aspirate_mmFromBottom and dispense_mmFromBottom, as well as wellOrder_first and wellOrder_second can be None. Mix has mix_airGap_checkbox and mix_airGap_volume. Thermocycler has extra thermocyclerFormType: 'thermocyclerHold' to enable incubation. 'sourceVolumes', 'destVolumes', and 'mixVolumes' are added to calculate offset.
# otjson2py will be changed to csv2py in future.
def otjson2py(filename: str, tiprack_assign=None, webhook_url=None, debug=False) -> str:
    # Specifying starting well of the used tiprack.
    if tiprack_assign == None or tiprack_assign == 'auto' or tiprack_assign == 'A1/A1' or tiprack_assign == 'A1':
        used_tiprack = False
    else:
        used_tiprack = True
        starting_tip_well = used_tiprack_parse(tiprack_assign)
    
    # to parse pipettes, labwares and modules from JSON file to variables
    try:
        with open(filename, 'r') as f:
            pdjson = json.load(f)   
    except FileNotFoundError:
        return 'Error: File not found.'
        
    metadata = pdjson['metadata']
    metadata['created'] = datetime.datetime.fromtimestamp(float(metadata['created'])/1000).strftime('%Y-%m-%d %H:%M:%S.%f')
    metadata['lastModified'] = datetime.datetime.fromtimestamp(float(metadata['lastModified'])/1000).strftime('%Y-%m-%d %H:%M:%S.%f')
    for key, value in metadata.items(): 
        if value is None:
            metadata[key] = "n/a"
    metadata['tags'] = str(metadata['tags'])
    if used_tiprack == True:
        metadata['apiLevel'] = '2.13'   # mitigate the bug of OT2 API 2.14
    else:
        metadata['apiLevel'] = '2.14'
    module_dict = {
        'temperatureModuleV2':'temperature module gen2',
        'magneticModuleV2':'magnetic module gen2',
        'thermocyclerModuleV2':'thermocycler module gen2',
        'heaterShakerModuleV1':'heaterShakerModuleV1',
        'magneticModuleV1':'magnetic module',
        'temperatureModuleV1':'temperature module',
        'thermocyclerModuleV1':'thermocycler module'
    }
  
    # pipettes_name is a dictionary with key of pipette ID and value of pipette name (e.g. p20_single_gen2).
    # pipettes is a dictionary with key of pipette ID and value of pipette object (e.g. left_pipette).
    pipettes_name = {}
    pipettes = {}
    for key, value in pdjson['pipettes'].items():
        pipettes_name[key] = value['name']
        pipettes[key] = ""

    # labwares_name is a dictionary with key of labware ID and value of labware name (e.g. opentrons_96_tiprack_20ul).
    # labwares is a dictionary with key of labware ID and value of labware object (e.g. tiprack1).
    labwares_name = {}
    labwares = {}
    for key, value in pdjson['labware'].items():
        labwares_name[key] = value['definitionId'].split('/')[1]
        labwares[key] = ""
    labwares['fixedTrash'] = 'protocol.fixed_trash'

    # modules_name is a dictionary with key of module ID and value of module name (e.g. temperature module gen2).
    # modules is a dictionary with key of module ID and value of module object (e.g. tempermod_7).
    modules_name = {}
    modules = {}
    for key, value in pdjson['modules'].items():
        modules_name[key] = module_dict[str(value['model'])]
        modules[key] = ""

    # liquids is a dictionary with key of liquid ID (serial integral from 0 in str) and value of liquid object (e.g. liq_water).
    liquids = {}

    # Other parameters assigend to variables
    if metadata.get('max_carryover') == None:
        max_carryover = 10
    else:  
        max_carryover = metadata['max_carryover']

# header
    with open('output.py', 'w') as f:
        f.write('from opentrons import protocol_api\nimport json\nimport time\nimport math\nimport sys\n\n')
        f.write(f'metadata = {metadata}\n\n')
        if webhook_url is not None:
            f.write(f'webhook_url = "{webhook_url}"\n\n')
            f.write("import urllib.request\n\n")
            f.write("def send_to_slack(webhook_url, message):\n")
            f.write("    data = {\n")
            f.write("        'text': message,\n")
            f.write("        'username': 'MyBot',\n")
            f.write("        'icon_emoji': ':robot_face:'\n")
            f.write("    }\n")
            f.write("    data = json.dumps(data).encode('utf-8')\n\n")
            f.write("    headers = {'Content-Type': 'application/json'}\n\n")
            f.write("    req = urllib.request.Request(webhook_url, data, headers)\n")
            f.write("    with urllib.request.urlopen(req) as res:\n")
            f.write("        if res.getcode() != 200:\n")
            f.write("            raise ValueError(\n")
            f.write("                'Request to slack returned an error %s, the response is:\\n%s'\n")
            f.write("                % (res.getcode(), res.read().decode('utf-8')))\n\n")

        f.write('def run(protocol: protocol_api.ProtocolContext):\n\n')
        nested_method_output(f, pdjson)

# load modules
        f.write(f'\n    debug = {debug}  # debug mode shows more comments\n\n')
        f.write(f"# load modules\n")
        for key in modules.keys():
            if pdjson['designerApplication']['data']['savedStepForms']['__INITIAL_DECK_SETUP_STEP__']['moduleLocationUpdate'][key] == 'span7_8_10_11':
                slot = '7'
            else:
                slot = pdjson['designerApplication']['data']['savedStepForms']['__INITIAL_DECK_SETUP_STEP__']['moduleLocationUpdate'][key]
            f.write(f"    mod_{modules_name[key][0:6].lower()}_{slot} = protocol.load_module(module_name='{modules_name[key]}',"
                        f"location='{slot}')\n")
            # modules are stored in dictionary with key of module ID
            modules[key] = f"mod_{modules_name[key][0:6].lower()}_{slot}"
            
# load labwares
        f.write(f"\n# load labwares\n")
        for key in labwares.keys():
            slot = pdjson['designerApplication']['data']['savedStepForms']['__INITIAL_DECK_SETUP_STEP__']['labwareLocationUpdate'][key]
            if slot in modules :
                f.write(f"    {pdjson['labwareDefinitions'][key.split(':')[1]]['metadata']['displayCategory'].lower()}_{modules[slot]} = {modules[slot]}.load_labware('{labwares_name[key]}')\n")
                labwares[key] = f"{pdjson['labwareDefinitions'][key.split(':')[1]]['metadata']['displayCategory'].lower()}_{modules[slot]}"
            elif key != 'fixedTrash':
                f.write(f"    {pdjson['labwareDefinitions'][key.split(':')[1]]['metadata']['displayCategory'].lower()}_{slot} = protocol.load_labware(load_name='{labwares_name[key]}', "
                            f"location='{slot}')\n")
                labwares[key] = f"{pdjson['labwareDefinitions'][key.split(':')[1]]['metadata']['displayCategory'].lower()}_{slot}"
        # labwares are stored in dictionary with key of labware ID

# load pipettes
        f.write(f"\n# load pipettes\n")
        for pipId in pipettes.keys():
            mount = pdjson['designerApplication']['data']['savedStepForms']['__INITIAL_DECK_SETUP_STEP__']['pipetteLocationUpdate'][pipId]
            if tiprack_assign == 'auto' or used_tiprack == True:
                tiprack_name = pdjson['designerApplication']['data']['pipetteTiprackAssignments'][pipId]
                tipracks = []
                for key, value in pdjson['designerApplication']['data']['savedStepForms']['__INITIAL_DECK_SETUP_STEP__']['labwareLocationUpdate'].items() :
                    if key.split(':')[len(key.split(':'))-1] == tiprack_name :
                        tipracks.append(labwares[key])
                        tipracks_str = '[' + ']['.join(tipracks) + ']'
                ini_tiprack = tipracks[0]
                f.write(f"    {mount}_pipette = protocol.load_instrument(instrument_name='{pipettes_name[pipId]}', mount='{mount}',tip_racks={tipracks_str})\n")
                if used_tiprack == True:
                    f.write(f"    {mount}_pipette.starting_tip = {ini_tiprack}.well('{starting_tip_well[mount]}')\n")
            else:
                f.write(f"    {mount}_pipette = protocol.load_instrument(instrument_name='{pipettes_name[pipId]}', mount='{mount}')\n")
            # pipettes are stored in dictionary with key of pipette ID
            pipettes[pipId] = f"{mount}_pipette"

# define liquids
        if used_tiprack == False:
            f.write(f"\n# define liquids\n")
            for key in pdjson['designerApplication']['data']['ingredients'].keys():
                f.write(f"    liq_{pdjson['designerApplication']['data']['ingredients'][key]['name'].lower()} = protocol.define_liquid(name='{pdjson['designerApplication']['data']['ingredients'][key]['name'].lower()}',description='{pdjson['designerApplication']['data']['ingredients'][key]['description']}',display_color='{pdjson['designerApplication']['data']['ingredients'][key]['displayColor']}')\n")
                # liquids are stored in list with key of liquid serial (incremental number in string starting from 0)
                liquids[key] = f"liq_{pdjson['designerApplication']['data']['ingredients'][key]['name'].lower()}"

# load liquids to labwares 
            f.write(f"\n# load liquids to labwares\n")
            for labwareId, wellName_dict in pdjson['designerApplication']['data']['ingredLocations'].items():
                for wellName, liquidId_dict in wellName_dict.items():
                    for liquidId, volume_dict in liquidId_dict.items():
                        f.write(f"    {labwares[labwareId]}['{wellName}'].load_liquid({liquids[liquidId]},volume={volume_dict['volume']})\n")

# steps in order
        f.write(f"\n# Protocol sections")
        for i in range(len(pdjson['designerApplication']['data']['orderedStepIds'])):
            ordered_step = pdjson['designerApplication']['data']['savedStepForms'][pdjson['designerApplication']['data']['orderedStepIds'][i]]
            step = i + 1
            f.write(f"\n    step = {step} # {ordered_step['stepName']}")
            if ordered_step['stepDetails'] != "":
                f.write(f" Notes: {ordered_step['stepDetails']}\n")
                f.write(f"    protocol.comment(f'Step {{step}}. {ordered_step['stepDetails']}')\n")
            else:
                f.write(f"\n    protocol.comment(f'Step {{step}}.')\n")  
                      

# liquid hanlding 
    # moving liquid
    # the source liquid and destination liquid should be in each single labware.
            if ordered_step['stepType'] == 'moveLiquid':
                sorted_aspirate_wells = sort_wells(ordered_step['aspirate_wells'], ordered_step['aspirate_wellOrder_first'], ordered_step['aspirate_wellOrder_second'])
                sorted_dispense_wells = sort_wells(ordered_step['dispense_wells'], ordered_step['dispense_wellOrder_first'], ordered_step['dispense_wellOrder_second'])
                if ordered_step['path'] == 'single' or ordered_step['path'] == 'reverse':   # reverse mode is original mode allowing disposal volume parameter
                    f.write(f"    liquid_handling(mode='transfer', ")
                elif ordered_step['path'] == 'multiAspirate':
                    f.write(f"    liquid_handling(mode='consolidate', ")
                elif ordered_step['path'] == 'multiDispense':
                    f.write(f"    liquid_handling(mode='distribute', ")
                f.write(f"pipette={pipettes[ordered_step['pipette']]}, volume={ordered_step['volume']},\n             "   # Volume can be one of float or list of float, as same as official instrument.transfer() attribute. Tuple is no longer supported.
                            f"aspirate_labware={labwares[ordered_step['aspirate_labware']]}, aspirate_wells={sorted_aspirate_wells},\n             "
                            f"dispense_labware={labwares[ordered_step['dispense_labware']]}, dispense_wells={sorted_dispense_wells},\n             ")
                if ordered_step['aspirate_mmFromBottom'] != None:
                    f.write(f"aspirate_offset={ordered_step['aspirate_mmFromBottom']}, ")   # asprirate_mmFromBottom is a float specifying identical offset over step
                elif ordered_step.get('sourceVolumes') != None:
                    f.write(f"source_volumes={ordered_step['sourceVolumes']}, ")            # With dna-origami-db, source volume is passed to calculate offset.
                if ordered_step['dispense_mmFromBottom'] != None:
                    f.write(f"dispense_offset={ordered_step['dispense_mmFromBottom']}, ")   # dispense_mmFromBottom is a float specifying identical offset over step
                elif ordered_step.get('destVolumes') != None:
                    f.write(f"dest_volumes={ordered_step['destVolumes']},\n             ")                # With dna-origami-db, dest volume is passed to calculate offset.
                if ordered_step['aspirate_flowRate'] != None:
                    f.write(f"aspirate_flow_rate={ordered_step['aspirate_flowRate']}, ")
                if ordered_step['dispense_flowRate'] != None:
                    f.write(f"dispense_flow_rate={ordered_step['dispense_flowRate']}, ")
                if ordered_step['aspirate_mix_checkbox'] == True and ordered_step['path'] != 'multiAspirate':
                    f.write(f"mix_before=({ordered_step['aspirate_mix_times']}, {ordered_step['aspirate_mix_volume']}), ")  # mix_before is a tuple of mix times and mix volume
                if ordered_step['dispense_mix_checkbox'] == True and ordered_step['path'] != 'multiDispense':
                    f.write(f"mix_after=({ordered_step['dispense_mix_times']}, {ordered_step['dispense_mix_volume']}), ")  # mix_before is a tuple of mix times and mix volume
                if ordered_step['aspirate_touchTip_checkbox'] == True:
                    f.write(f"aspirate_touch_tip={ordered_step['aspirate_touchTip_checkbox']}, ")
                    if ordered_step['aspirate_touchTip_mmFromBottom'] != None:   # if None, default value = -1 mm from top
                        f.write(f"aspirate_touch_tip_offset={ordered_step['aspirate_touchTip_mmFromBottom']}, ")
                if ordered_step['dispense_touchTip_checkbox'] == True:
                    f.write(f"dispense_touch_tip={ordered_step['dispense_touchTip_checkbox']}, ")   # This value is either bool or float (0.25-1.0 to specify touch speed).
                    if ordered_step['dispense_touchTip_mmFromBottom'] != None:   # if None, default value = -1 mm from top
                        f.write(f"dispense_touch_tip_offset={ordered_step['dispense_touchTip_mmFromBottom']}, ")
                if ordered_step['preWetTip'] == True:
                    f.write(f"pre_wet_tip={ordered_step['preWetTip']}, ")
                if ordered_step['aspirate_airGap_checkbox'] == True:
                    f.write(f"aspirate_air_gap={ordered_step['aspirate_airGap_volume']}, ")
                if ordered_step['dispense_airGap_checkbox'] == True:
                    f.write(f"dispense_air_gap={ordered_step['dispense_airGap_volume']}, ")
                if ordered_step['aspirate_delay_checkbox'] == True:
                    f.write(f"aspirate_delay={ordered_step['aspirate_delay_seconds']}, ")
                    if ordered_step['aspirate_delay_mmFromBottom'] != None:
                        f.write(f"aspirate_delay_bottom={ordered_step['aspirate_delay_mmFromBottom']}, ")
                if ordered_step['dispense_delay_checkbox'] == True:
                    f.write(f"dispense_delay={ordered_step['dispense_delay_seconds']}, ")
                    if ordered_step['dispense_delay_mmFromBottom'] != None:
                        f.write(f"dispense_delay_bottom={ordered_step['dispense_delay_mmFromBottom']}, ")
                if ordered_step['path'] == 'reverse':
                    f.write(f"disposal_volume={ordered_step['disposalVolume_volume']}, blow_out=True, blowout_location='trash', ")    # in reverse mode, always blowout to trash.
                elif ordered_step['disposalVolume_checkbox'] == True and ordered_step['path'] == 'multiDispense':   # disposal volume is only available in reverse mode and multiDispense mode
                    f.write(f"disposal_volume={ordered_step['disposalVolume_volume']}, ")
                    if ordered_step['blowout_location'] == 'source_well': 
                        f.write(f"blowout_location='source well', ")
                    else:                                                        # blowout at trash as default
                        f.write(f"blowout_location='trash', ")
                elif ordered_step['blowout_checkbox'] == True:
                    f.write(f"blow_out=True, ")
                    if ordered_step['blowout_location'] == 'source_well': 
                        f.write(f"blowout_location='source well', ")
                    elif ordered_step['blowout_location'] == 'dest_well': 
                        f.write(f"blowout_location='destination well', ")
                    else:                                                        # blowout at trash as default
                        f.write(f"blowout_location='trash', ")
                f.write(f"new_tip='{ordered_step['changeTip']}')\n")

    # mixing liquid
            elif ordered_step['stepType'] == 'mix':
                mix_wells = sort_wells(ordered_step['wells'], ordered_step['mix_wellOrder_first'], ordered_step['mix_wellOrder_second'])
                f.write(f"    liquid_handling(mode='mix', pipette={pipettes[ordered_step['pipette']]}, repetitions={ordered_step['times']}, volume={ordered_step['volume']},\n        "   # Volume can be one of float or list of float, as same as official instrument.transfer() attribute. Tuple is no longer supported.
                        f"mix_labware={labwares[ordered_step['labware']]}, mix_wells={mix_wells},\n        ")
                if ordered_step['mix_mmFromBottom'] != None:
                    f.write(f"mix_offset={ordered_step['mix_mmFromBottom']}, ")   # asprirate_mmFromBottom is a float specifying identical offset over step
                elif ordered_step.get('mixVolumes') != None:
                    f.write(f"mix_volumes={ordered_step['mixVolumes']},\n        ")            # With dna-origami-db, source volume is passed to calculate offset.
                if ordered_step['aspirate_flowRate'] != None:
                    f.write(f"aspirate_flow_rate={ordered_step['aspirate_flowRate']}, ")
                if ordered_step['dispense_flowRate'] != None:
                    f.write(f"dispense_flow_rate={ordered_step['dispense_flowRate']}, ")
                if ordered_step['mix_touchTip_checkbox'] == True:
                    f.write(f"mix_touch_tip={ordered_step['mix_touchTip_checkbox']}, ")
                    if ordered_step['mix_touchTip_mmFromBottom'] != None:   # if None, default value = -1 mm from top
                        f.write(f"mix_touch_tip_offset={ordered_step['mix_touchTip_mmFromBottom']}, ")
                if ordered_step.get('mix_airGap_checkbox') == True:
                    f.write(f"mix_air_gap={ordered_step.get('mix_airGap_volume')}, ")
                if ordered_step['aspirate_delay_checkbox'] == True:
                    f.write(f"aspirate_delay={ordered_step['aspirate_delay_seconds']}, ")
                    if ordered_step.get('aspirate_delay_mmFromBottom') != None:
                        f.write(f"aspirate_delay_bottom={ordered_step.get('aspirate_delay_mmFromBottom')}, ")
                if ordered_step['dispense_delay_checkbox'] == True:
                    f.write(f"dispense_delay={ordered_step['dispense_delay_seconds']}, ")
                    if ordered_step.get('dispense_delay_mmFromBottom') != None:
                        f.write(f"dispense_delay_bottom={ordered_step.get('dispense_delay_mmFromBottom')}, ")
                if ordered_step.get('disposalVolume_checkbox') == True:         # custom volume for reverse mode mixing. Not official.
                    f.write(f"disposal_volume={ordered_step['disposalVolume_volume']}, ")
                    if ordered_step['blowout_location'] == 'source_well': 
                            f.write(f"blowout_location='source well', ")
                    else:                                                        # blowout at trash as default
                        f.write(f"blowout_location='trash', ")
                if ordered_step['blowout_checkbox'] == True:
                    f.write(f"blow_out=True, ")
                    if ordered_step['blowout_location'] == 'source_well': 
                            f.write(f"blowout_location='source well', ")
                    elif ordered_step['blowout_location'] == 'dest_well': 
                        f.write(f"blowout_location='destination well', ")
                    else:                                                        # blowout at trash as default
                        f.write(f"blowout_location='trash', ")
                f.write(f"new_tip='{ordered_step['changeTip']}')\n")

    # Module control
        # HeaterShaker module control
            elif ordered_step['stepType'] == 'heaterShaker':
                if ordered_step['setHeaterShakerTemperature'] == True:
                    f.write(f"    if {modules[ordered_step['moduleId']]}.target_temperature != {ordered_step['targetHeaterShakerTemperature']}:\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.set_target_temperature(celsius={ordered_step['targetHeaterShakerTemperature']})   #Returns immediately. Wait temperture step will follow always.\n")
                else:
                    f.write(f"    if {modules[ordered_step['moduleId']]}.temperature_status != 'idle':\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.deactivate_heater()\n")
                if ordered_step['latchOpen'] == True:
                    f.write(f"    if {modules[ordered_step['moduleId']]}.labware_latch_status != 'idle_open':\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.open_labware_latch()\n")
                else:
                    f.write(f"    if {modules[ordered_step['moduleId']]}.labware_latch_status != 'idle_closed':\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.close_labware_latch()\n")
                if ordered_step['setShake'] == True:
                    f.write(f"    if {modules[ordered_step['moduleId']]}.target_speed != {ordered_step['targetSpeed']}:\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.set_and_wait_for_shake_speed(rpm={ordered_step['targetSpeed']})\n")
                else:
                    f.write(f"    if {modules[ordered_step['moduleId']]}.speed_status != 'idle':\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.deactivate_shaker()\n")
                if ordered_step['heaterShakerSetTimer'] == True:
                    seconds = 0
                    if ordered_step['heaterShakerTimerSeconds'] != None:
                        seconds = int(ordered_step['heaterShakerTimerSeconds'])
                    minutes = 0
                    if ordered_step['heaterShakerTimerMinutes'] != None:
                        minutes = int(ordered_step['heaterShakerTimerMinutes'])
                    f.write(f"    message = 'Heater Shaker Timer Start: {str(minutes)} min {str(seconds)} sec. Current temperature: ' + str({modules[ordered_step['moduleId']]}.current_temperature) + '.'\n")
                    f.write(f"    protocol.delay(seconds={seconds}, minutes={minutes}, msg=message)     # Time imediately starts regardless of current temperature\n")
                    f.write(f"    message = 'Heater Shaker Timer End: {str(minutes)} min {str(seconds)} sec. Current temperature: ' + str({modules[ordered_step['moduleId']]}.current_temperature) + '.'\n")
                    f.write(f"    protocol.comment(msg=message)\n")
                    f.write(f"    {modules[ordered_step['moduleId']]}.deactivate_shaker()\n")
                    f.write(f"    {modules[ordered_step['moduleId']]}.deactivate_heater()\n")
                    # In future update, "set timer and continue protocol" function will be added.

        # temperature module control
            elif ordered_step['stepType'] == 'temperature':
                if ordered_step['setTemperature'] == 'true' or (str(type(ordered_step['setTemperature'])) == "<class 'bool'>" and ordered_step['setTemperature']):       # strange data type of Protocol Designer JSON file. It might be corrected in future update.
                    f.write(f"    if {modules[ordered_step['moduleId']]}.target != {ordered_step['targetTemperature']}:\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.start_set_temperature(celsius={ordered_step['targetTemperature']})    #Hidden API\n")
                elif ordered_step['setTemperature'] == 'false' or (str(type(ordered_step['setTemperature'])) == "<class 'str'>" and ordered_step['setTemperature']):  
                    f.write(f"    if {modules[ordered_step['moduleId']]}.status != 'idle':\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.deactivate()\n")

        # magnetic module control
            elif ordered_step['stepType'] == 'magnet':
                if ordered_step['magnetAction'] == "engage":
                    f.write(f"    if {modules[ordered_step['moduleId']]}.status != 'engage':\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.engage(height_from_base={ordered_step['engageHeight']})\n")
                elif ordered_step['magnetAction'] == "disengage":
                    f.write(f"    if {modules[ordered_step['moduleId']]}.status != 'disengage':\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.disengage()\n")

        # thermocycler module control
            # Update thermocycler state
            elif ordered_step['stepType'] == 'thermocycler':
                if ordered_step['thermocyclerFormType'] == 'thermocyclerState':
                    if ordered_step['lidOpen'] == True:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.lid_position != 'open':\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.open_lid()\n")
                    elif ordered_step['lidOpen'] == False:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.lid_position != 'close':\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.close_lid()\n")
                    if ordered_step['blockIsActive'] == True:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.block_target_temperature != {ordered_step['blockTargetTemp']}:\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.set_block_temperature(temperature={ordered_step['blockTargetTemp']})\n")
                    elif ordered_step['blockIsActive'] == False:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.block_temperature_status != 'idle':\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.deactivate_block()\n")
                    if ordered_step['lidIsActive'] == True:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.lid_target_temperature != {ordered_step['lidTargetTemp']}:\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.set_lid_temperature(temperature={ordered_step['lidTargetTemp']})\n")
                    elif ordered_step['lidIsActive'] == False:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.lid_temperature_status != 'idle':\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.deactivate_lid()\n")
            
            # Execute predefined profile
                elif ordered_step['thermocyclerFormType'] == 'thermocyclerProfile':
                    f.write(f"    if {modules[ordered_step['moduleId']]}.lid_position != 'close':  # Profile is always executed with lid closed.\n")
                    f.write(f"        {modules[ordered_step['moduleId']]}.close_lid()\n")
                    if ordered_step['profileTargetLidTemp'] != None:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.lid_target_temperature != {ordered_step['profileTargetLidTemp']}:\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.set_lid_temperature(temperature={ordered_step['profileTargetLidTemp']})\n")
                    for i in range(len(ordered_step['orderedProfileItems'])):
                        profile_item = ordered_step['profileItemsById'][ordered_step['orderedProfileItems'][i]]
                        if profile_item['type'] == 'profileStep':
                            profile = [
                                {
                                    'temperature': int(profile_item['temperature']),
                                    'hold_time_seconds': int(profile_item['durationSeconds']) if profile_item['durationSeconds'] else 0,
                                    'hold_time_minutes': int(profile_item['durationMinutes']) if profile_item['durationMinutes'] else 0
                                }
                            ]
                            repetition = 1
                        elif profile_item['type'] == 'profileCycle':
                            profile = [
                                {
                                    'temperature': int(step['temperature']),
                                    'hold_time_seconds': int(step['durationSeconds']) if step['durationSeconds'] else 0,
                                    'hold_time_minutes': int(step['durationMinutes']) if step['durationMinutes'] else 0
                                } for step in profile_item['steps']
                            ]
                            repetition = int(profile_item['repetitions'])
                        f.write(f"    {modules[ordered_step['moduleId']]}.execute_profile(steps={profile}, repetitions={repetition}, block_max_volume={ordered_step['profileVolume']})\n")
                    f.write(f"    # Profile has been executed and the thermocycler is kept hold as below.\n")
                    if ordered_step['blockIsActiveHold'] == True:
                        f.write(f"    {modules[ordered_step['moduleId']]}.set_block_temperature(temperature={ordered_step['blockTargetTempHold']})\n")
                    elif ordered_step['blockIsActiveHold'] == False:
                        f.write(f"    {modules[ordered_step['moduleId']]}.deactivate_block()\n")
                    if ordered_step['lidOpenHold'] == True:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.lid_position != 'open':\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.open_lid()\n")
                    elif ordered_step['lidOpenHold'] == False:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.lid_position != 'close':\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.close_lid()\n")
                    if ordered_step['lidIsActiveHold'] == True:
                        f.write(f"    {modules[ordered_step['moduleId']]}.set_lid_temperature(temperature={ordered_step['lidTargetTempHoldHold']})\n")
                    elif ordered_step['lidIsActiveHold'] == False:
                        f.write(f"    {modules[ordered_step['moduleId']]}.deactivate_lid()\n")

            # Hold temperature for specific time. Temperature is specified by block/lidTargetTempHold, and time is specified by the first item (profileStep type) of the profile.
                elif ordered_step['thermocyclerFormType'] == 'thermocyclerHold':
                    if ordered_step['lidIsActiveHold'] == True:
                        f.write(f"    {modules[ordered_step['moduleId']]}.set_lid_temperature(temperature={ordered_step['lidTargetTempHold']})\n")
                    elif ordered_step['lidIsActiveHold'] == False:
                        f.write(f"    {modules[ordered_step['moduleId']]}.deactivate_lid()\n")
                    if ordered_step['lidOpenHold'] == True:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.lid_position != 'open':\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.open_lid()\n")
                    elif ordered_step['lidOpenHold'] == False:
                        f.write(f"    if {modules[ordered_step['moduleId']]}.lid_position != 'close':\n")
                        f.write(f"        {modules[ordered_step['moduleId']]}.close_lid()\n")
                    if ordered_step['blockIsActiveHold'] == True:
                        key, value = list(ordered_step['profileItemsById'].items())[0]
                        f.write(f"    {modules[ordered_step['moduleId']]}.set_block_temperature(temperature={ordered_step['blockTargetTempHold']}, "        # hold time is defined by the first step of the single item profile.
                                f"hold_time_seconds={int(value['durationSeconds'])}, hold_time_minutes={int(value['durationMinutes'])}, block_max_volume={ordered_step['profileVolume']})\n")
                    elif ordered_step['blockIsActiveHold'] == False:
                        f.write(f"    {modules[ordered_step['moduleId']]}.deactivate_block()\n")
                        
        # pause control
            elif ordered_step['stepType'] == 'pause':
                if ordered_step['pauseAction'] == 'untilTime':
                    minutes = 0
                    if ordered_step['pauseMinute'] != None:
                        minutes = int(ordered_step['pauseMinute'])
                    if ordered_step['pauseHour'] != None:
                        minutes = minutes + int(ordered_step['pauseHour']) * 60
                    seconds = 0
                    if ordered_step['pauseSecond'] != None:
                        seconds = int(ordered_step['pauseSecond'])
                    f.write(f"    protocol.delay(seconds={seconds}, minutes={minutes}, msg='{ordered_step['pauseMessage']}')\n")
                elif ordered_step['pauseAction'] == 'untilResume':
                    f.write(f"    protocol.pause(msg='{ordered_step['pauseMessage']}')\n")
                elif ordered_step['pauseAction'] == 'untilTemperature':
                    if ordered_step['moduleId'].split(':')[1] == 'temperatureModuleType':
                        f.write(f"    while ({modules[ordered_step['moduleId']]}.temperature != {ordered_step['pauseTemperature']} and not protocol.is_simulating):\n")
                        f.write(f"        protocol.delay(seconds=1, msg='{ordered_step['pauseMessage']}')\n")
                    elif ordered_step['moduleId'].split(':')[1] == 'heaterShakerModuleType':
                        f.write(f"    {modules[ordered_step['moduleId']]}.wait_for_temperature()\n")

            elif ordered_step['stepType'] == 'control':     # custom step type for controling OT-2
                if ordered_step['controlAction'] == 'home':
                    f.write(f"    protocol.home()\n")
                elif ordered_step['controlAction'] == 'removeTip':
                    f.write(f"    for key in protocol.loaded_instruments:\n"
                            f"        if protocol.loaded_instruments[key].has_tip:\n"
                            f"            protocol.loaded_instruments[key].drop_tip()\n")
                elif ordered_step['controlAction'] == 'comment':
                    f.write(f"    protocol.comment(msg='{ordered_step['commentMessage']}')\n")
                    if webhook_url != None:
                        f.write(f"    send_to_slack(webhook_url,'{ordered_step['commentMessage']}')\n")
                    if ordered_step['beep'] == True:
                        pass    # beep to be supported in future update.

            else:
                f.write(f"    protocol.comment('# Step {step} is not supported yet.')\n")
            
            # drop tip if next step is not liquid handling
            if (ordered_step['stepType'] == 'moveLiquid' or ordered_step['stepType'] == 'mix') and i < len(pdjson['designerApplication']['data']['orderedStepIds']) - 1:
                next_step = pdjson['designerApplication']['data']['savedStepForms'][pdjson['designerApplication']['data']['orderedStepIds'][i + 1]]
                if next_step['stepType'] != 'moveLiquid' and next_step['stepType'] != 'mix':
                    f.write(f"    for key in protocol.loaded_instruments:\n"
                            f"        if protocol.loaded_instruments[key].has_tip:\n"
                            f"            protocol.loaded_instruments[key].drop_tip()\n")

# Home robot at last
        f.write(f"\n# Home robot\n"
                f"    protocol.home()\n"
                f"    for key in protocol.loaded_instruments:\n"
                f"        if protocol.loaded_instruments[key].has_tip:\n"
                f"            protocol.loaded_instruments[key].drop_tip()\n")

        if webhook_url != None:
            f.write(f'    if protocol.is_simulating == False:\n'
                    f'        send_to_slack(webhook_url,"Your OT-2 protocol has just been completed!")\n')

if len(args.arg2) > 7:
    webhook_url = args.arg2
    tiprack_assign = None
else:
    webhook_url = args.arg3
    tiprack_assign = args.arg2
if args.arg4 == 'command':
    otjson2py_command(args.arg1,tiprack_assign=tiprack_assign,webhook_url=webhook_url)
elif args.arg3 == 'command':
    otjson2py_command(args.arg1,tiprack_assign=tiprack_assign)
elif args.arg2 == 'command':
    otjson2py_command(args.arg1)
elif args.arg4 == 'debug':   
    otjson2py(args.arg1,tiprack_assign=tiprack_assign,webhook_url=webhook_url, debug=True)
else:
    otjson2py(args.arg1,tiprack_assign=tiprack_assign,webhook_url=webhook_url)

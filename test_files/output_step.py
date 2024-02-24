from opentrons import protocol_api
import json
import time
import math
import sys

metadata = {'protocolName': 'comprehensive_test_file', 'author': 'RIKEN/Yusuke Sakai', 'description': 'Attempt to convert JSON to Py', 'created': '2023-04-29 00:53:38.084000', 'lastModified': '2023-09-05 22:16:38.807000', 'category': 'n/a', 'subcategory': 'n/a', 'tags': '[]', 'apiLevel': '2.13'}

webhook_url = "https://hooks.slack.com/services/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"

import urllib.request

def send_to_slack(webhook_url, message):
    data = {
        'text': message,
        'username': 'MyBot',
        'icon_emoji': ':robot_face:'
    }
    data = json.dumps(data).encode('utf-8')

    headers = {'Content-Type': 'application/json'}

    req = urllib.request.Request(webhook_url, data, headers)
    with urllib.request.urlopen(req) as res:
        if res.getcode() != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (res.getcode(), res.read().decode('utf-8')))

def run(protocol: protocol_api.ProtocolContext):


    def liquid_handling(mode, pipette, volume, aspirate_labware=None, aspirate_wells=None, 
                    dispense_labware=None, dispense_wells=None, 
                    repetitions=None, mix_labware=None, mix_wells=None, new_tip='always', 
                    aspirate_offset=1, dispense_offset=0.5, mix_offset=0.5,
                    source_volumes=None, dest_volumes=None, mix_volumes=None,
                    aspirate_flow_rate=None, dispense_flow_rate=None, mix_before=None, mix_after=None, 
                    aspirate_touch_tip=False, aspirate_touch_tip_offset=None,
                    dispense_touch_tip=False, dispense_touch_tip_offset=None, 
                    mix_touch_tip=False, mix_touch_tip_offset=None, pre_wet_tip=False,
                    aspirate_air_gap=0.0, dispense_air_gap=0.0, mix_air_gap=0.0, aspirate_delay=None, aspirate_delay_bottom=1.0, dispense_delay=None, dispense_delay_bottom=0.5,
                    blow_out=False, blowout_location='trash', disposal_volume=None, step=0):
        try:
            nonlocal protocol
            if step == 0:
                raise ValueError('Step number must be 1 or more.')
            default_touchtip_offset_from_top = -1
            default_blowout_offset_from_top = 0
            min_volume = pipette.min_volume
            max_volume = pipette.max_volume
            max_carryover = 10
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
                dispense_air_gap = mix_air_gap
                aspirate_wells = mix_wells
                dispense_wells = mix_wells
            
            # 0.1 Volume/repetitions inspection and handling volume is converted to list (each well-to-well path/mixing well) of list (carryover/mixing cycle including carryover).
  
            if type(volume) == int or type(volume) == float or (type(volume) == str and volume.isnumeric()):
                volume = float(volume)
                if mode != 'mix':
                    handling_volumes = [volume] * len(aspirate_wells)
                else:
                    handling_volumes = [volume] * len(mix_wells)
            elif type(volume) == list:
                for i in range (len(volume)):
                    if type(volume[i]) == int or type(volume[i]) == float or (type(volume[i]) == str and volume[i].isnumeric()):
                        handling_volumes.append(float(volume[i]))
                    else:
                        raise TypeError(f'volume must be float or list of float, not {type(volume[i])}')
            else:
                raise TypeError(f'volume must be float or list of float, not {type(volume)}')

            if mode == 'mix':
                if type(repetitions) == int or type(repetitions) == float or (type(repetitions) == str and repetitions.isnumeric()):
                    volume = float(repetitions)
                    repetitions = [repetitions] * len(mix_wells)
                elif type(repetitions) == list:
                    for i in range (len(repetitions)):
                        if type(repetitions[i]) == int or type(repetitions[i]) == float or (type(repetitions[i]) == str and repetitions[i].isnumeric()):
                            repetitions.append(float(volume[i]))
                        else:
                            raise TypeError(f'repetitions must be float or list of float, not {type(repetitions[i])}')
                else:
                    raise TypeError(f'repetitions must be float or list of float, not {type(repetitions)}')

            for i in range(len(handling_volumes)):
                if mode != 'mix':
                    if handling_volumes[i] > max_volume - aspirate_air_gap - disposal_volume:       # disposal volume for mix stands for mixing with at least specified volume aspirated to avoid bubbles. The disposal volume will be blow out to trash.
                        left_volume = handling_volumes[i]
                        carryover_cycle = math.ceiling(left_volume / (max_volume - aspirate_air_gap - disposal_volume))
                        if carryover_cycle > max_carryover:
                            raise ValueError(f'Volume {handling_volumes[i]} exceeds maximum carryover for pipette {pipette.instrument_name}.')
                        aliquot_volume = math.ceiling( left_volume / carryover_cycle )
                        while left_volume > 0:
                            handling_volumes[i].append(min(aliquot_volume, left_volume))
                            left_volume -= min(aliquot_volume, left_volume)
                    else:
                        handling_volumes[i] = [handling_volumes[i]]
                else:
                    if handling_volumes[i] > max_volume - disposal_volume:       # disposal volume for mix stands for mixing with at least specified volume aspirated to avoid bubbles. The disposal volume will be blow out to trash.
                        mix_cycle = math.ceiling(repetitions[i] * handling_volumes[i] / (max_volume - disposal_volume))
                        if mix_cycle / repetitions[i] > max_carryover:
                            raise ValueError(f'Volume {handling_volumes[i]} for mix exceeds maximum carryover for pipette {pipette.instrument_name}.')
                        for _ in range(mix_cycle):
                            handling_volumes[i].append(ceiling(repetitions[i] * handling_volumes[i] / mix_cycle))   # the length of handling_volume[i] specifies mixing cycle repetition.
                    else:
                        handling_volumes[i] = [handling_volumes[i]] * repetitions[i]

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
                        pre_wet_volumes = [min(max_volume * 2/3, sum(item for sublist in handling_volumes for item in sublist) * 0.8)] * len(aspirate_wells)
                    else:
                        pre_wet_volumes = [min(max_volume * 2/3, sum(item for item in handling_volumes[i]) * 0.8)] * len(aspirate_wells)
                if mix_before:
                    if mix_before[0] == None and mix_before[1] == None:
                        mix_before[0] = 3
                        mix_before[1] = max_volume - disposal_volume
                    elif mix_before[0] == None:
                        mix_before[0] = ceiling( mix_before[1] / (max_volume - disposal_volume) )
                        if mix_before[0] > max_carryover:
                            raise ValueError(f'Volume {mix_before[1]} exceeds maximum carryover for pipette {pipette.instrument_name}.')
                        mix_before[1] = max_volume - disposal_volume
                    elif mix_before[1] > max_volume - disposal_volume:
                        mix_before_loop = mix_before[1] / (max_volume - disposal_volume)
                        if mix_before_loop > max_carryover:
                            raise ValueError(f'Volume {mix_before[1]} exceeds maximum carryover for pipette {pipette.instrument_name}.')
                        mix_before[0] = math.ceiling(mix_before[0] * mix_before_loop)
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
                                    raise ValueError(f'Mixing volume {mix_before[1]} for Source volume {source_volumes[i]} exceeds maximum carryover for pipette {pipette.instrument_name}.')
                                mix_before_cycles.append(ceiling (mix_before[0] * mix_before_loop))
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
                        mix_after[0] = ceiling( mix_after[1] / (max_volume) )
                        if mix_after[0] > max_carryover:
                            raise ValueError(f'Volume {mix_after[1]} exceeds maximum carryover for pipette {pipette.instrument_name}.')
                        mix_after[1] = max_volume
                    elif mix_after[1] > max_volume:
                        mix_after_loop = mix_after[1] / (max_volume)
                        if mix_after_loop > max_carryover:
                            raise ValueError(f'Volume {mix_after[1]} exceeds maximum carryover for pipette {pipette.instrument_name}.')
                        mix_after[0] = math.ceiling(mix_after[0] * mix_after_loop)
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
                                    raise ValueError(f'Mixing volume {mix_after[1]} for Destination volume {mix_after_left_volume} exceeds maximum carryover for pipette {pipette.instrument_name}.')
                                mix_after_cycles.append(ceiling (mix_after[0] * mix_after_loop))
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
            default_aspirate_flow_rate = pipette.flow_rate.aspirate
            default_dispense_flow_rate = pipette.flow_rate.dispense
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
                    if mode == 'distribute' and not cont_start_flag[i]: # skipped during path between dest to dest in distribute mode
                        pass
                    if mode == 'mix':                                   # no tip replacement during mixing the same well (over same i)
                        pass 
                    elif not (i == 0 and j == 0) and (new_tip == 'always' or (new_tip == 'auto' and dest_volumes[i] > 0 )):  # Replace tip per each transfer, 'auto' replace tip when dest is filled (tip is contaminated)
                        if pipette.has_tip:
                            if dispense_air_gap:
                                pipette.air_gap(dispense_air_gap)
                                if dispense_delay:
                                    protocol.delay(seconds=dispense_delay)
                            pipette.drop_tip()
                        pipette.pick_up_tip()

            # 2. Pre-wetting tip
                    if mode == 'distribute' and not cont_start_flag[i]: # skipped during path between dest to dest in distribute mode. Prewet seems igonred in Protocol Designer ver 6.2.2. but kept active for consistency.
                        pass
                    if mode == 'mix':                                   # skipped in mix mode
                        pass
                    elif (pre_wet_tip and j == 0) or (mode == 'consolidate' and cont_start_flag[i]):  # prewet will be done only at the first cycle of carry over, assuming carry over makes the tip wet, or the first source of consolidate
                        pipette.aspirate(pre_wet_volumes[i], aspirate_labware[aspirate_wells[i]].bottom(pre_wet_tip_offsets[i]))
                        if aspirate_delay:  # no height adjustemnt for pre-wetting
                            protocol.delay(seconds=aspirate_delay)
                        pipette.dispense(pre_wet_volumes[i], aspirate_labware[aspirate_wells[i]].bottom(pre_wet_tip_offsets[i]))
                        if aspirate_delay:  # assuming delay is determined by source solution property, aspirate delay is applied.
                            protocol.delay(seconds=dispense_delay)

            # 3. Mix before aspirating
                    if mode == 'consolidate' or mode == 'mix': # skipped in consolidate mode and mix mode
                        pass
                    elif mix_before and j == 0 and ((mode == 'transfer_mode' or mode == 'reverse_mode') or (mode == 'distribute' and l == 0)):    # first cycle of either carryover of transfer/reverse or distribute                   # mix_before only at the first cycle of carryover 
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
                        pipette.aspirate(handling_volume, mix_labware[mix_wells[i]].bottom(mix_offsets[i][j]))
                        if aspirate_delay:
                            if mix_volumes == None:
                                pipette.move_to(mix_labware[mix_wells[i]].bottom(aspirate_delay_bottom),speed=20) # slowed the speed to reduce vibration
                            protocol.delay(seconds=aspirate_delay)

                    elif mode == 'transfer' or mode == 'consolidate':
                        aspirate_volume = handling_volumes[i][j] + disposal_volume
                        pipette.aspirate(aspirate_volume, aspirate_labware[aspirate_wells[i]].bottom(aspirate_offsets[i][j]))
                        if aspirate_delay:
                            if source_volumes == None:
                                pipette.move_to(aspirate_labware[aspirate_wells[i]].bottom(aspirate_delay_bottom),speed=20) # slowed the speed to reduce vibration
                            protocol.delay(seconds=aspirate_delay)

                    elif mode == 'distribute' and cont_start_flag[i]:
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
                        pipette.dispense(handling_volumes[i][j], mix_labware[mix_wells[i]].bottom(mix_offsets[i][j]))
                        if dispense_delay:
                            if dest_volumes == None:
                                pipette.move_to(mix_labware[mix_wells[i]].bottom(dispense_delay_bottom),speed=20) # slowed the speed to reduce vibration
                            protocol.delay(seconds=dispense_delay)
                    elif mode == 'transfer' or mode == 'reverse' or mode == 'distribute':
                        pipette.dispense(handling_volumes[i][j], dispense_labware[dispense_wells[i]].bottom(dispense_offsets[i][j]))
                        if dispense_delay:
                            if dest_volumes == None:
                                pipette.move_to(dispense_labware[dispense_wells[i]].bottom(dispense_delay_bottom),speed=20) # slowed the speed to reduce vibration
                            protocol.delay(seconds=dispense_delay)
                    elif mode == 'consolidate' and cont_end_flag:
                        for m in range(len(cont_volumes[k])):
                            pipette.dispense(cont_volumes[k][m][j], dispense_labware[dispense_wells[i]].bottom(cont_dispense_offsets[k][j]))      
                            if dispense_delay:
                                if dest_volumes == None:
                                    pipette.move_to(dispense_labware[dispense_wells[i]].bottom(dispense_delay_bottom),speed=20) # slowed the speed to reduce vibration
                                protocol.delay(seconds=dispense_delay)
                            if aspirate_air_gap and pipette.current_volume > 0:
                                pipette.dispense(aspirate_air_gap, dispense_labware[dispense_wells[i]].top()) 
                                        
            # 10. Mix after dispensing
                    if mode == 'consolidate' or mode == 'mix': # skipped in distribute/mix mode
                        pass
                    elif mix_after and j == len(handling_volumes[i]) - 1 and ((mode == 'transfer_mode' or mode == 'reverse_mode') or (mode == 'consolidate' and l == len(cont_volumes[k]) - 1)):    # last cycle of either carryover of transfer/reverse or consolidate
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

            # 11. Touch tip
                    if mode == 'consolidate' and not cont_end_flag: # skipped during path between source to source in consolidate mode
                        pass
                    elif mode == 'mix' and j < len(handling_volumes[i]) - 1: # skipped in mix mode apart from the last cycle
                        pass
                    elif dispense_touch_tip:
                        if dispense_touch_tip_offset == None:
                            offset=default_touchtip_offset_from_top
                        else:
                            offset = dispense_touch_tip_offset - dispense_labware[dispense_wells[i]].depth
                        pipette.touch_tip(v_offset=offset, speed=aspirate_touch_tip)

            # 12. Air gap and delay for carryover                           
                    if mode == 'distribute' and not cont_end_flag: # skipped during path between dest to dest in distribute mode, for accuracy of dispense volume
                        pass
                    elif mode == 'consolidate' and not cont_end_flag: # skipped during path between source to source in consolidate mode
                        pass
                    elif mode == 'mix' and j < len(handling_volumes[i]) - 1: # skipped in mix mode apart from the last cycle
                        pass
                    elif blow_out:  # dispense air gap is applied in case blowout is specified
                        if dispense_air_gap:
                            pipette.air_gap(dispense_air_gap)
                            if dispense_delay:
                                protocol.delay(seconds=dispense_delay)
                    elif len(handling_volumes[i]) > 1 and j < len(handling_volumes[i]) - 1 and aspirate_air_gap:    # air gap for aspirate is applied for return trip of carryover
                        pipette.air_gap(aspirate_air_gap)
                        if dispense_delay:
                            protocol.delay(seconds=dispense_delay)
                                    
            # 13. Blow out (applied every carryover cycle)
                    if blow_out:
                        if mode == 'distribute' and not cont_end_flag: # skipped during path between dest to dest in distribute mode
                            pass
                        elif mode == 'consolidate' and not cont_end_flag: # skipped during path between source to source in consolidate mode
                            pass
                        elif mode == 'mix' and j < len(handling_volumes[i]) - 1: # skipped in mix mode apart from the last cycle
                            pass
                        elif blowout_location == 'source well':
                            pipette.blow_out(aspirate_labware[aspirate_wells[i]].top(default_blowout_offset_from_top))
                        elif blowout_location == 'destination well' and disposal_volume == 0:   # blow out to destination well is not allowed in distribute mode
                            pipette.blow_out(dispense_labware[dispense_wells[i]].top(default_blowout_offset_from_top))
                        else:
                            pipette.blow_out(protocol.fixed_trash['A1'])

            # 14. Drop tip when air gap specified, for consistensy of Protocol designer
            if dispense_air_gap:
                pipette.air_gap(dispense_air_gap)
                if dispense_delay:
                    protocol.delay(seconds=dispense_delay)
                pipette.drop_tip()
               
            # 15. Resume flow rate
            pipette.flow_rate.aspirate = default_aspirate_flow_rate
            pipette.flow_rate.dispense = default_dispense_flow_rate
            protocol.comment(f"# handling_volumes:{handling_volumes} cont_volumes:{cont_volumes}") 
        except Exception as e:
            raise Exception(f"{str(sys.exc_info()[0]).split('.')[-1][:-2]} in Step {step}. transfer-{mode}: {e}, line {sys.exc_info()[2].tb_lineno}") # Left for debug {handling_volumes} {cont_volumes} {cont_start_flag} i:{i} j:{j} k:{k} {blowout_location}")
# load modules
    mod_heater_1 = protocol.load_module(module_name='heaterShakerModuleV1',location='1')
    mod_magnet_9 = protocol.load_module(module_name='magnetic module gen2',location='9')
    mod_temper_6 = protocol.load_module(module_name='temperature module gen2',location='6')
    mod_thermo_7 = protocol.load_module(module_name='thermocycler module',location='7')

# load labwares
    tiprack_5 = protocol.load_labware(load_name='opentrons_96_tiprack_20ul', location='5')
    tiprack_4 = protocol.load_labware(load_name='opentrons_96_tiprack_300ul', location='4')
    wellplate_mod_thermo_7 = mod_thermo_7.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    aluminumblock_mod_temper_6 = mod_temper_6.load_labware('opentrons_24_aluminumblock_nest_2ml_snapcap')
    aluminumblock_mod_heater_1 = mod_heater_1.load_labware('opentrons_96_deep_well_adapter_nest_wellplate_2ml_deep')
    wellplate_mod_magnet_9 = mod_magnet_9.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    tuberack_3 = protocol.load_labware(load_name='opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', location='3')

# load pipettes
    left_pipette = protocol.load_instrument(instrument_name='p20_single_gen2', mount='left',tip_racks=[tiprack_5])
    left_pipette.starting_tip = tiprack_5.well('B4')
    right_pipette = protocol.load_instrument(instrument_name='p300_multi_gen2', mount='right',tip_racks=[tiprack_4])
    right_pipette.starting_tip = tiprack_4.well('D1')

# Protocol section
    protocol.comment('# Step 1.')

# Step 1. transfer
    liquid_handling(mode='transfer', step=1, pipette=right_pipette, volume=20,
             aspirate_labware=wellplate_mod_magnet_9, aspirate_wells=['A1', 'A2', 'A3', 'A4'],
             dispense_labware=wellplate_mod_magnet_9, dispense_wells=['A5', 'A6', 'A7', 'A8'],
             aspirate_touch_tip=True, dispense_touch_tip=True, pre_wet_tip=True, aspirate_air_gap=20, dispense_air_gap=20, aspirate_delay=1, dispense_delay=1, new_tip='always')
    protocol.comment('# Step 2.')

# Step 2. transfer
    liquid_handling(mode='distribute', step=2, pipette=left_pipette, volume=5,
             aspirate_labware=tuberack_3, aspirate_wells=['A1'],
             dispense_labware=aluminumblock_mod_temper_6, dispense_wells=['D1', 'C1', 'B1', 'A1', 'D2', 'C2', 'B2', 'A2'],
             aspirate_touch_tip=True, dispense_touch_tip=True, pre_wet_tip=True, aspirate_air_gap=1, dispense_air_gap=1, aspirate_delay=1, dispense_delay=1, new_tip='always')
    protocol.comment('# Step 3.')

# Step 3. transfer
    liquid_handling(mode='consolidate', step=3, pipette=left_pipette, volume=5,
             aspirate_labware=tuberack_3, aspirate_wells=['A1', 'B1'],
             dispense_labware=aluminumblock_mod_temper_6, dispense_wells=['A1'],
             aspirate_touch_tip=True, dispense_touch_tip=True, pre_wet_tip=True, aspirate_air_gap=1, dispense_air_gap=1, aspirate_delay=1, dispense_delay=1, new_tip='once')
    protocol.comment('# Step 4.')

# Step 4. transfer
    liquid_handling(mode='transfer', step=4, pipette=left_pipette, volume=5,
             aspirate_labware=tuberack_3, aspirate_wells=['C1'],
             dispense_labware=aluminumblock_mod_temper_6, dispense_wells=['A1', 'B1', 'C1'],
             aspirate_touch_tip=True, dispense_touch_tip=True, pre_wet_tip=True, aspirate_air_gap=1, dispense_air_gap=1, aspirate_delay=1, dispense_delay=1, blow_out=True, blowout_location='source well', new_tip='perDest')
    protocol.comment('# Step 5.')

# Step 5. transfer
    liquid_handling(mode='transfer', step=5, pipette=left_pipette, volume=5,
             aspirate_labware=tuberack_3, aspirate_wells=['C1'],
             dispense_labware=aluminumblock_mod_temper_6, dispense_wells=['A1'],
             aspirate_touch_tip=True, dispense_touch_tip=True, pre_wet_tip=True, aspirate_delay=1, dispense_delay=1, blow_out=True, blowout_location='trash', new_tip='perSource')
    protocol.comment('# Step 6.')

# Step 6. transfer
    liquid_handling(mode='transfer', step=6, pipette=left_pipette, volume=5,
             aspirate_labware=tuberack_3, aspirate_wells=['C1'],
             dispense_labware=aluminumblock_mod_temper_6, dispense_wells=['A1'],
             dispense_offset=33.5, blow_out=True, blowout_location='destination well', new_tip='never')
    protocol.comment('# Step 7.')

# Step 7. heater-shaker
    mod_heater_1.deactivate_heater()
    mod_heater_1.close_labware_latch()
    mod_heater_1.deactivate_shaker()
    protocol.comment('# Step 8.')

# Step 8. mix
    liquid_handling(step=8, mode='mix', pipette=right_pipette, repetitions=5, volume=300,
        mix_labware=aluminumblock_mod_heater_1, mix_wells=['A1'],
        mix_offset=2, dispense_flow_rate=30, mix_touch_tip=True, aspirate_delay=1, dispense_delay=1, blow_out=True, blowout_location='trash', new_tip='always')
    protocol.comment('# Step 9.')

# Step 9. pause
    protocol.pause(msg='Pause until told to resume')
    protocol.comment('# Step 10.')

# Step 10. pause
    protocol.delay(seconds=3, minutes=62, msg='Delay of 1:2:3')
    protocol.comment('# Step 11.')

# Step 11. temperature
    mod_temper_6.start_set_temperature(celsius=37)    #Hidden API
    protocol.comment('# Step 12.')

# Step 12. heater-shaker Notes: Note field is tested.
    protocol.comment(msg='Note field is tested.')
    mod_heater_1.set_target_temperature(celsius=42)   #Returns immediately. Wait temperture step will follow always.
    mod_heater_1.close_labware_latch()
    mod_heater_1.set_and_wait_for_shake_speed(rpm=300)
    message = 'Heater Shaker Timer: 10 min 0 sec. Current temperature: ' + str(mod_heater_1.current_temperature) + '.'
    protocol.delay(seconds=0, minutes=10, msg=message)     # Time imediately starts regardless of current temperature
    protocol.comment('# Step 13.')

# Step 13. pause
    while (mod_temper_6.temperature != 37 and not protocol.is_simulating):
        protocol.delay(seconds=1, msg='Temp module is reached to 37˚C')
    protocol.comment('# Step 14.')

# Step 14. magnet Notes: Note of magnet module engage
    protocol.comment(msg='Note of magnet module engage')
    mod_magnet_9.engage(height_from_base=6)
    protocol.comment('# Step 15.')

# Step 15. magnet Notes: disengage
    protocol.comment(msg='disengage')
    mod_magnet_9.disengage()
    protocol.comment('# Step 16.')

# Step 16. temperature
    mod_temper_6.deactivate()
    protocol.comment('# Step 17.')

# Step 17. thermocycler
    if mod_thermo_7.lid_position != 'open':
        mod_thermo_7.open_lid()
    mod_thermo_7.deactivate_lid()
    mod_thermo_7.deactivate_block()
    protocol.comment('# Step 18.')

# Step 18. thermocycler Notes: note on thermal cycler
    protocol.comment(msg='note on thermal cycler')
    if mod_thermo_7.lid_position != 'close':
        mod_thermo_7.close_lid()
    if mod_thermo_7.lid_target_temperature != 110:
        mod_thermo_7.set_lid_temperature(temperature=110)
    if mod_thermo_7.block_target_temperature != 70:
        mod_thermo_7.set_block_temperature(temperature=70)
    protocol.comment('# Step 19.')

# Step 19. thermocycler
    if mod_thermo_7.lid_position != 'open':
        mod_thermo_7.open_lid()
    mod_thermo_7.deactivate_lid()
    mod_thermo_7.deactivate_block()
    protocol.comment('# Step 20.')

# Step 20. thermocycler Notes: PCR from Profile
    protocol.comment(msg='PCR from Profile')
    if mod_thermo_7.lid_position != 'close':  # Profile is always executed with lid closed.
        mod_thermo_7.close_lid()
    if mod_thermo_7.lid_target_temperature != 110:
        mod_thermo_7.set_lid_temperature(temperature=110)
    mod_thermo_7.execute_profile(steps=[{'temperature': 95, 'hold_time_seconds': 10, 'hold_time_minutes': 0}, {'temperature': 72, 'hold_time_seconds': 15, 'hold_time_minutes': 1}], repetitions=10, block_max_volume=50)
    # Profile has been executed and the thermocycler is kept hold as below.
    mod_thermo_7.execute_profile(steps=[{'temperature': 95, 'hold_time_seconds': 10, 'hold_time_minutes': 0}], repetitions=1, block_max_volume=50)
    # Profile has been executed and the thermocycler is kept hold as below.
    mod_thermo_7.set_block_temperature(temperature=10)
    if mod_thermo_7.lid_position != 'close':
        mod_thermo_7.close_lid()
    mod_thermo_7.deactivate_lid()
    protocol.comment('# Step 21.')

# Step 21. temperature
    mod_temper_6.start_set_temperature(celsius=4)    #Hidden API
    protocol.comment('# Step 22.')

# Step 22. pause for 4˚C Notes: Note of the stape
    protocol.comment(msg='Note of the stape')
    while (mod_temper_6.temperature != 4 and not protocol.is_simulating):
        protocol.delay(seconds=1, msg='Message to Display')
    protocol.comment('# Step 23.')

# Step 23. heater-shaker
    mod_heater_1.deactivate_heater()
    mod_heater_1.close_labware_latch()
    mod_heater_1.deactivate_shaker()
    protocol.comment('# Step 24.')

# Step 24. transfer
    liquid_handling(mode='transfer', step=24, pipette=left_pipette, volume=20,
             aspirate_labware=aluminumblock_mod_heater_1, aspirate_wells=['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2'],
             dispense_labware=aluminumblock_mod_heater_1, dispense_wells=['H3', 'F3', 'H4', 'F4', 'C4', 'A4', 'C5', 'G6', 'F8', 'E8', 'H10', 'C10', 'A10', 'H12', 'F12', 'A12'],
             new_tip='always')
    protocol.comment('# Step 25.')

# Step 25. pause
    protocol.delay(seconds=10, minutes=0, msg='')
    protocol.comment('# Step 26.')

# Step 26. temperature
    mod_temper_6.start_set_temperature(celsius=15)    #Hidden API
    protocol.comment('# Step 27.')

# Step 27. heater-shaker
    mod_heater_1.set_target_temperature(celsius=50)   #Returns immediately. Wait temperture step will follow always.
    mod_heater_1.close_labware_latch()
    mod_heater_1.set_and_wait_for_shake_speed(rpm=500)
    protocol.comment('# Step 28.')

# Step 28. pause
    while (mod_temper_6.temperature != 15 and not protocol.is_simulating):
        protocol.delay(seconds=1, msg='')
    protocol.comment('# Step 29.')

# Step 29. thermocycler
    if mod_thermo_7.lid_position != 'open':
        mod_thermo_7.open_lid()
    if mod_thermo_7.lid_target_temperature != 50:
        mod_thermo_7.set_lid_temperature(temperature=50)
    if mod_thermo_7.block_target_temperature != 10:
        mod_thermo_7.set_block_temperature(temperature=10)
    protocol.comment('# Step 30.')

# Step 30. thermocycler
    if mod_thermo_7.lid_position != 'open':
        mod_thermo_7.open_lid()
    if mod_thermo_7.lid_target_temperature != 50:
        mod_thermo_7.set_lid_temperature(temperature=50)
    if mod_thermo_7.block_target_temperature != 20:
        mod_thermo_7.set_block_temperature(temperature=20)
# Home robot
    protocol.home()
    for key in protocol.loaded_instruments:
        if protocol.loaded_instruments[key].has_tip:
            protocol.loaded_instruments[key].drop_tip()
    send_to_slack(webhook_url,"Your OT-2 protocol has just been completed!")

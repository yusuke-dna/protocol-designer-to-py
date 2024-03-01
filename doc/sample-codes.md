# Sample Codes
Here is sample codes taken from old version of the project. Note that all are for example and the coding including function names and parameter names may be changed by programmer.
## json2py()
```python

def json2py(filename: str, left="A1", right="A1", webhook_url=None) -> str:

    # Specifying starting well of the used tiprack.
    if left == "A1" and right == "A1":
        used_tiprack = False
    else:
        used_tiprack = True
        starting_tip_well = used_tiprack_parse(tiprack_assign)
        
    try:
        with open(filename, 'r') as f:
            pdjson = json.load(f)
    except FileNotFoundError:
        return 'Error: File not found.'

    # parse metadata
    metadata = pdjson['metadata']
    metadata['created'] = datetime.datetime.fromtimestamp(float(metadata['created'])/1000).strftime('%Y-%m-%d %H:%M:%S.%f')
    metadata['lastModified'] = datetime.datetime.fromtimestamp(float(metadata['lastModified'])/1000).strftime('%Y-%m-%d %H:%M:%S.%f')
    for key, value in metadata.items(): 
        if value is None:
            metadata[key] = "n/a"
    metadata['tags'] = str(metadata['tags'])
    metadata['apiLevel'] = '2.16'
    module_dict = {
        'temperatureModuleV2':'temperature module gen2',
        'magneticModuleV2':'magnetic module gen2',
        'thermocyclerModuleV2':'thermocycler module gen2',
        'heaterShakerModuleV1':'heaterShakerModuleV1',
        'magneticModuleV1':'magnetic module',
        'temperatureModuleV1':'temperature module',
        'thermocyclerModuleV1':'thermocycler module'
    }

    # parse pipettes, labwares, modules and liquid from JSON file to variables

    # pipettes name: p20_single_gen2 etc ; pipettes: left_pipette etc. Key is pipetteId of the pipette.
    pipettes_name = {}
    pipettes = {}

    # labwares name: opentrons_96_tiprack_20ul etc ; labwares: tiprack1 etc. Key is definitionId of the labware.
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

    write_header('output.py', metadata, filename, webhook_url) # check later

    with open('output.py', 'w') as f:
        f.write('def run(protocol: protocol_api.ProtocolContext):\n')

# For every command...
        for i in range(len(pdjson['commands'])):
            command_step = pdjson['commands'][i]

# Serial numbering for debug
            if i%10 == 0 and i > 9:
                f.write(f'\n# command no. {i}\n')

# load pipettes
            if command_step['commandType'] == 'loadPipette':
                mount = command_step['params']['mount']
                pipette_id = command_step['params']['pipetteId']
                # Store pipette name and pipette object
                pipettes_name[pipette_id] = command_step['params']['pipetteName']
                pipettes[pipette_id] = f"{mount}_pipette"

                if used_tiprack == True:
                    tiprack_name = pdjson['designerApplication']['data']['pipetteTiprackAssignments'][pipette_id]
                    tipracks = []
                    for key, value in pdjson['designerApplication']['data']['savedStepForms']['__INITIAL_DECK_SETUP_STEP__']['labwareLocationUpdate'].items() :
                        if key.split(':')[len(key.split(':'))-1] == tiprack_name :
                            tipracks.append(labwares[key])
                            tipracks_str = '[' + ']['.join(tipracks) + ']'
                    ini_tiprack = tipracks[0]
                    f.write(f"    {mount}_pipette = protocol.load_instrument(instrument_name='{pipettes_name[pipette_id]}', mount='{mount}',tip_racks={tipracks_str})\n")
                    f.write(f"    {mount}_pipette.starting_tip = {ini_tiprack}.well('{starting_tip_well[mount]}')\n")
                else:
                    f.write(f"    {mount}_pipette = protocol.load_instrument(instrument_name='{pipettes_name[pipette_id]}', mount='{mount}')\n")
                pipettes[command_step['params']['pipetteId']] = f"{mount}_pipette"

# load labwares and modules
            if command_step['commandType'] == 'loadLabware':
                labware_id = command_step['params']['labwareId']
                # If the labware is loaded on slot...
                if list(command_step['params']['location'].keys())[0] == 'slotName':
                    f.write(f"    labware{i} = protocol.load_labware(load_name='{labwares_name[labware_id]}', "
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
# load liquid
            elif command_step['commandType'] == 'loadLiquid':
                # Code for Load liquid here

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
            elif command_step['commandType'] == 'moveLabware':
                # Code for labware relocation here
            elif command_step['commandType'] == 'loadLiquid' or command_step['commandType'] == 'loadPipette' or command_step['commandType'] == 'loadLabware' or command_step['commandType'] == 'loadModule':
                None    # Thery are already handled above
            else:
                f.write(f"not parsed: {command_step['commandType']}, {i}\n")

        if webhook_url != None:
            f.write(f'    send_to_slack(webhook_url,"Your OT-2 protocol has just completed!")\n')
```

## json2csv()
```python
```

## csv2dict()
```python
```

## dict2py()
```python
```

## write_header()
```python
def write_header(output_filename, metadata, webhook_url):
    with open(output_filename, 'w') as f:

# Print header
        f.write(f'''

        ...(inside quate is extracted below)...
 
        '''
```
Contents are as below. Note that it is in f-string format, with variable `metadata` and `webhook_url` are used.
```python
from opentrons import protocol_api
import json, time, math, sys, urllib.request, subprocess, types

# Options
metadata = {json.dumps(metadata, indent=4)}
left = {left} # starting tip for left pipette for overwriting
right = {right} # starting tip for right pipette for overwriting
webhook_url = {webhook_url}
audio_path = '/etc/audio/alarm.mp3' # hard-coded path to audio file.

# Send notifications to slack 
def send_to_slack(webhook_url, message):
    data = {{
        'text': message,
        'username': 'MyBot',
        'icon_emoji': ':robot_face:'
    }}
    data = json.dumps(data).encode('utf-8')

    headers = {{'Content-Type': 'application/json'}}

    req = urllib.request.Request(webhook_url, data, headers)
    with urllib.request.urlopen(req) as res:
        if res.getcode() != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (res.getcode(), res.read().decode('utf-8')))

# Beep alarm according to this document: https://support.opentrons.com/s/article/How-to-play-sounds-out-of-the-OT-2
# Error handling is required. If no file found in audio_path, return `pass`.
def beep_alarm(audio_path):
    # Code here

```

## write_liquid_handling()
```python
def write_liquid_handling(output_filename, default_values:dict={'default_aspirate_clearance':0.5,'default_dispense_clearance':1,'default_touchtip_offset':1, 'default_blowout_offset':1}):
    with open(output_filename, 'a') as f:

# Print liquid handling method
        f.write(f'''

            def liquid_handling(mode, pipette, volume, aspirate_labware=None, aspirate_wells:list=None, ...

            # nested method for liquid handling is extracted below

        ''')
```

Contents are as below. Note that it is in f-string format, with variable `default_values`

```python
    def liquid_handling(mode:str, pipette:object, volume, aspirate_labware:=None, aspirate_wells:list=None, 
                    dispense_labware:object=None, dispense_wells:list=None, 
                    repetitions=None, mix_labware=None, mix_wells=None, new_tip='always', 
                    aspirate_clearance={default_values['default_aspirate_clearance']}, dispense_clearance={default_values['default_dispense_clearance']}, mix_clearance={default_values['default_dispense_clearance']},
                    source_volumes:list=None, dest_volumes:list=None, mix_volumes:list=None,
                    aspirate_flow_rate=None, dispense_flow_rate=None, mix_before=None, mix_after=None, 
                    aspirate_touch_tip=False, aspirate_touch_tip_offset=None,
                    dispense_touch_tip=False, dispense_touch_tip_offset=None, 
                    mix_touch_tip=False, mix_touch_tip_offset=None, pre_wet_tip=False,
                    aspirate_air_gap=0.0, dispense_air_gap=0.0, mix_air_gap=0.0, aspirate_delay=None, aspirate_delay_bottom={default_values['default_aspirate_clearance']}, dispense_delay=None, dispense_delay_bottom={default_values['default_dispense_clearance']},
                    blow_out=False, blowout_location='trash', disposal_volume=None):
        try:
            nonlocal protocol, step_num
            if step_num == 0:
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
                aspirate_clearances = []
                for i in range(len(source_volumes)):
                    aspirate_clearances.append([])
                    for j in range(len(handling_volumes[i])):
                        diameter = aspirate_labware[aspirate_wells[i]].diameter
                        width = aspirate_labware[aspirate_wells[i]].width
                        length = aspirate_labware[aspirate_wells[i]].length
                        depth = aspirate_labware[aspirate_wells[i]].depth
                        # source_left_volume is source_volume - all transfer volume until j - all disposal volume until j.
                        source_left_volume = source_volumes[i] - sum(handling_volumes[i][:(j+1)]) - disposal_volume * (j + 1)
                        if 'PCR' in aspirate_labware_name:
                            aspirate_clearances[i].append(max(0.5, ( (2 * depth / diameter) ** (2/3) * (27 / 4 * depth * diameter ** 2 + 150 * source_left_volume / math.pi) ** 3 - 3 * depth) / 2 - min (depth / 5 , 10)))
                        elif aspirate_labware[aspirate_wells[i]].diameter == None:
                            aspirate_clearances[i].append(max(0.5, source_left_volume / (width * length) - min (depth / 5 , 10)))
                        else:
                            aspirate_clearances[i].append(max(0.5, source_left_volume * 4 / (math.pi * diameter ** 2) - min (depth / 5 , 10)))
            elif mode != 'mix':
                aspirate_clearances = [aspirate_clearance] * len(aspirate_wells)
                for i in range(len(aspirate_clearances)):
                    aspirate_clearances[i] = [aspirate_clearances[i]]
                    if len(handling_volumes[i]) > 1:
                        aspirate_clearances[i] = aspirate_clearances[i] * len(handling_volumes[i])
            if dest_volumes != None and mode != 'mix':
                aspirate_clearances = []
                for i in range(len(dest_volumes)):
                    dispense_clearances.append([])
                    for j in range(len(handling_volumes[i])):
                        diameter = dispense_labware[dispense_wells[i]].diameter
                        width = dispense_labware[dispense_wells[i]].width
                        length = dispense_labware[dispense_wells[i]].length
                        depth = dispense_labware[dispense_wells[i]].depth
                        # dest_left_volume is dest_volume + all transfer volume until j.
                        dest_left_volume = dest_volumes[i] + sum(handling_volumes[i][:j])
                        if 'PCR' in dispense_labware_name:
                            dispense_clearances[i].append(max(0.5, ( (2 * depth / diameter) ** (2/3) * (27 / 4 * depth * diameter ** 2 + 150 * dest_left_volume / math.pi) ** 3 - 3 * depth) / 2 - min (depth / 5 , 10)))
                        elif dispense_labware[dispense_wells[i]].diameter == None:
                            dispense_clearances[i].append(max(0.5, dest_left_volume / (width * length) - min (depth / 5 , 10)))
                        else:
                            dispense_clearances[i].append(max(0.5, dest_left_volume * 4 / (math.pi * diameter ** 2) - min (depth / 5 , 10)))
            elif mode != 'mix':
                dispense_clearances = [dispense_clearance] * len(dispense_wells)
                for i in range(len(dispense_clearances)):
                    dispense_clearances[i] = [dispense_clearances[i]]
                    if len(handling_volumes[i]) > 1:
                        dispense_clearances[i] = dispense_clearances[i] * len(handling_volumes[i])
            if mix_volumes != None and mode == 'mix':
                mix_clearances = []
                for i in range(len(mix_volumes)):
                    mix_clearances.append([])
                    for j in range(len(handling_volumes[i])):   # mix offset is identical over i, but stored as list for consistency to aspirate/dispense offset.
                        diameter = mix_labware[mix_wells[i]].diameter
                        width = mix_labware[mix_wells[i]].width
                        length = mix_labware[mix_wells[i]].length
                        depth = mix_labware[mix_wells[i]].depth
                        mix_left_volume = mix_volumes[i] - handling_volumes[i][j] - disposal_volume
                        if 'PCR' in mix_labware_name:
                            mix_clearances[i].append(max(0.5, ( (2 * depth / diameter) ** (2/3) * (27 / 4 * depth * diameter ** 2 + 150 * mix_left_volume / math.pi) ** 3 - 3 * depth) / 2 - min (depth / 5 , 10)))
                        elif mix_labware[mix_wells[i]].diameter == None:
                            mix_clearances[i].append(max(0.5, mix_left_volume / (width * length) - min (depth / 5 , 10)))
                        else:
                            mix_clearances[i].append(max(0.5, mix_left_volume * 4 / (math.pi * diameter ** 2) - min (depth / 5 , 10)))
                aspirate_clearances = mix_clearances  # to reuse following script without modification
                dispense_clearances = mix_clearances
            elif mode == 'mix':
                mix_clearances = [mix_clearance] * len(mix_wells)
                for i in range(len(mix_clearances)):
                    mix_clearances[i] = [mix_clearances[i]]
                    if len(handling_volumes[i]) > 1:
                        mix_clearances[i] = mix_clearances[i] * len(handling_volumes[i])
                aspirate_clearances = mix_clearances  # to reuse following script without modification
                dispense_clearances = mix_clearances

            # 0.3 Distribute/Consolidate pass is arranged based on volume. List (each distribute) of List (each well-to-well path) of list (carryover).
            cont_volumes = []
            cont_aspirate_clearances = []
            cont_dispense_clearances = []
            cont_start_flag = []
            for i in range(len(handling_volumes)):
                if len(handling_volumes[i]) > 1:    # in case of carry over, one distribute/consolidate cycle assigned
                    cont_volumes.append([handling_volumes[i]])           # [..,[[carry,over,volumes]]]
                    cont_aspirate_clearances.append(aspirate_clearances[i])
                    cont_dispense_clearances.append(dispense_clearances[i])
                    cont_start_flag.append(True)
                elif len(cont_volumes) == 0:  # fist path to be distributed 
                    cont_volumes.append([handling_volumes[i]])  # [[[transfer_volume: float]]]
                    cont_aspirate_clearances.append(aspirate_clearances[i])
                    cont_dispense_clearances.append(dispense_clearances[i])
                    cont_start_flag.append(True)
                elif mode == 'distribute' and sum(item for sublist in cont_volumes[-1] for item in sublist) + handling_volumes[i][0] + disposal_volume + aspirate_air_gap <= max_volume: # if next path does not exeed max volume, distribute cycle is kept same
                    cont_volumes[-1].append(handling_volumes[i])    # [..,[..,[former_volume],[transfered_volume]]]
                    cont_aspirate_clearances[-1][0] = min(cont_aspirate_clearances[-1][0], aspirate_clearances[i][0])
                    cont_dispense_clearances[-1][0] = min(cont_dispense_clearances[-1][0], dispense_clearances[i][0])
                    cont_start_flag.append(False)
                elif mode == 'consolidate' and sum(item for sublist in cont_volumes[-1] for item in sublist) + len(cont_volumes[-1]) * dispense_air_gap + handling_volumes[i][0] + disposal_volume + dispense_air_gap <= max_volume: # if next path does not exeed max volume, distribute cycle is kept same
                    cont_volumes[-1].append(handling_volumes[i])    # [..,[..,[former_volume],[transfered_volume]]]
                    cont_aspirate_clearances[-1][0] = min(cont_aspirate_clearances[-1][0], aspirate_clearances[i][0])
                    cont_dispense_clearances[-1][0] = min(cont_dispense_clearances[-1][0], dispense_clearances[i][0])
                    cont_start_flag.append(False)
                else:   # new distribute cycle when it exceeds max volume
                    cont_volumes.append([handling_volumes[i]])
                    cont_aspirate_clearances.append(aspirate_clearances[i])
                    cont_dispense_clearances.append(dispense_clearances[i])
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
                    pre_wet_tip_offsets = [aspirate_clearance] * len(aspirate_wells)
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
                        mix_before_offsets = [aspirate_clearance] * len(aspirate_wells)
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
                        mix_after_offsets = [aspirate_clearance] * len(dispense_wells)
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
                        pipette.aspirate(handling_volume, mix_labware[mix_wells[i]].bottom(mix_clearances[i][j]))
                        if aspirate_delay:
                            protocol.delay(seconds=aspirate_delay)

                    elif mode == 'transfer' or mode == 'consolidate':
                        aspirate_volume = handling_volumes[i][j] + disposal_volume
                        if debug == True:
                            protocol.comment("aspirate-transfer/consoludate")
                        pipette.aspirate(aspirate_volume, aspirate_labware[aspirate_wells[i]].bottom(aspirate_clearances[i][j]))
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
                        pipette.aspirate(aspirate_volume, aspirate_labware[aspirate_wells[i]].bottom(cont_aspirate_clearances[k][j]))
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
                        pipette.dispense(handling_volumes[i][j], mix_labware[mix_wells[i]].bottom(mix_clearances[i][j]))
                        if dispense_delay:
                            protocol.delay(seconds=dispense_delay)

                    elif mode == 'transfer' or mode == 'reverse' or mode == 'distribute':
                        if debug == True:
                            protocol.comment("dispense-transfer/reverses/distribute")
                        pipette.dispense(handling_volumes[i][j], dispense_labware[dispense_wells[i]].bottom(dispense_clearances[i][j]))
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
                                pipette.dispense(cont_volumes[k][m][j], dispense_labware[dispense_wells[i]].bottom(cont_dispense_clearances[k][j]))      
                                if pipette.current_volume > 0:
                                    pipette.dispense(aspirate_air_gap, dispense_labware[dispense_wells[i]].top()) 
                            if dispense_delay:
                                if dest_volumes == None:
                                    pipette.move_to(dispense_labware[dispense_wells[i]].bottom(dispense_delay_bottom),speed=20) # slowed the speed to reduce vibration
                                protocol.delay(seconds=dispense_delay)
                        else:
                            if debug == True:
                                protocol.comment("dispense-consolidate")
                            pipette.dispense(pipette.current_volume, dispense_labware[dispense_wells[i]].bottom(cont_dispense_clearances[k][j])) # dispense all the volume in the pipette if no air gap
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
```

## bottom2top()
Convert between "height from top of the well" and "height from bottom of the well". It is used for touchTip configuration in command mode.  
Sample code:
```python
def bottom2top(json_dict: dict, labware_name_full: str, well_name: str, v_mm:float) -> float:
    # top2bottom conversion is the same. Only used in Command mode.
    well_depth = json_dict['labwareDefinitions'][labware_name_full]['wells'][well_name]['depth']
    return v_mm - well_depth
```

### used_tiprack_parse()
Generate dictionary of starting tip well from input string. If input string is missing alphabetic part, calculate it based on numeric part assuming the labware has eight rows.  
Sample code:
```python
def used_tiprack_parse(left='A1', right='A1') -> dict:
    starting_tip_well = {'left': '', 'right': ''}
    
    # Assign left and right values, use left value for right if right is None
    starting_tip_well['left'] = left
    starting_tip_well['right'] = right
    
    for key in starting_tip_well.keys():
        well_name = starting_tip_well[key].upper()
        alphabetic_part = ''.join(filter(str.isalpha, well_name))
        numeric_part = ''.join(filter(str.isdigit, well_name))
        numeric_part = str(int(numeric_part))
        
        # If alphabetic part is missing, calculate it based on numeric part
        if alphabetic_part == '':
            row = (int(numeric_part) - 1) % 8
            col = (int(numeric_part) - 1) // 8 + 1
            alphabetic_part = chr(row + ord('A'))
            numeric_part = str(col)
        
        starting_tip_well[key] = alphabetic_part + numeric_part 
    
    return starting_tip_well
```

### sort_wells()
Wells are sorted based on first_sort and second_sort.  
Sample code:
```python
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
```
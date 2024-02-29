# Sample Codes
Here is sample codes taken from old version of the project. Note that all are for example and the coding including function names and parameters may be changed by programmer.
## json2py()
Code block for command mode. `commands` object of JSON file is used to generate python script. The script is not organized and is not recommended for editing.  
Sample code:
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
```

## json2csv()
Code block for converting JSON file to CSV file. The CSV file is designed to be human-readable and editable.  
Sample code:
```python
```

## csv2step()
Code block for converting CSV file to dict form, similar to command object of JSON file.The Python dictionary is used as an intermediate data structure.
Sample code:
```python
```

## step2py()
Code block for converting CSV file to Python script. The Python script is designed to be human-readable and suitable for used as a template.

Sample code:
```python
```

## write_header()
Common script block of protocol.py and protocol_command.py is printed by this method. Output is a header section of python script in str, with `output_filename`. Main section of the script continues by `json2py()` or `step2py` method.

Sample Code:
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
Comprehensive `liquid_handling()` method is printed by this method. The method is hard-copied to output Python file by `step2py()` method. Command mode does not use it.
Sample code:
```python
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
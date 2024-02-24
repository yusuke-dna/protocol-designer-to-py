# Documents for new version of pdjson2py
The content is under preparation for future update. Latest version, utilising Step instead of Command of JSON file is available as default setting. For debug or specific purpose, command mode is available by adding fourth argument `command`
# Overview
protocol-designer-to-py, or `pdjson2py`, is to convert JSON file exported from the Opentrons Protocol Designer (ver. 8.01) into Python script for Opentrons Python API 2.16. `pdjson2py` only supports OT-2. The generated python script (and intermedial CSV file) will be used as a template of users' in-house protocol coding.

For that purpose, the output python script is designed to be flexible for editing and is equiped with user-friendly variables and comments ready for edit.

The code is consists of (1) simple logical substitution to Openrons API, (2) Opentrons API naming and loading pipettes, liquid, tipracks, modules, and labware according to Protocol Designer configuration, (3) comprehensive `liquid_handling()` method and (4) miscellaneous methods and variables, (3) and (4) are to be hard-copied to generated Python file.

## Data Handling Flow Chart
[scheme image]
### JSON file scenario (New Protocol Preparation)
1. Design your own protocol using `Opentrons Protocol Designer` and export `JSON file`.
2. Input `JSON file` to `pdjson2py` with optional parameters via `Opentrons Protocol Library (Web app)` or `Command Line Interface (CLI)`.
3. In `pdjson2py`, if input file is `JSON file`, go to step 4. If input file is `CSV file`, skip step 4-5 and go to step 6.
4. In `pdjson2py`, if command mode is not specified, go to step 5-1 (default). If command mode is specified, go to step 5-2.
5. In `pdjson2py`, 
    1. `json2csv()` converts `JSON file` to `CSV file`. The CSV file is available from the form link (`Web app`) or generated in the directly (`CLI`). The CSV file name is `protocol.csv`.
    2. `json2py()` converts `JSON file` to `Python script`. The Python script is available from the form link (`Web app`) or generated in the directly (`CLI`). The Python script name is `protocol_command.py`.
6. In `pdjson2py`, `csv2py()` converts `CSV file` to `Python script`. The Python script is available from the form link (`Web app`) or generated in the directly (`CLI`). The Python script name is `protocol.py`.
7. Run the Python script in `Opentrons App`.

### CSV file scenario (Edit Existing Protocol)
1. Design your own protocol by modifying existing `CSV file` (previously generated from `pdjson2py`) or using external CSV source.
2. Input `CSV file` to `pdjson2py` with optional parameters via `Web app` or `CLI`.
3. In `pdjson2py`, if input file is `CSV file`, skip step 4-5 and go to step 6. If input file is `JSON file`, go to step 4.
4. Skipped
5. Skipped
6. In `pdjson2py`, `csv2py()` converts `CSV file` to `Python script`. The Python script is available from the form link (`Web app`) or generated in the directly (`CLI`). The Python script name is `protocol.py`.
7. Run the Python script in `Opentrons App`.

## Command mode (JSON file input is required)
The protocol of liquid handling is stored in JSON file in two different ways. Simpler one is in `commands` object. Command mode traces and literally translates commands to Python API step by step. Serial number is marked every 10 commands for readability.

## Debug mode (mutually exclusive with Command mode)
This mode increase the comments in the generated Python script. It is useful for debugging and understanding the protocol.

## CSV file
CSV file is an intermediate file format to describe the protocol. It is generated from JSON file and can be used as an input for pdjson2py. The CSV file is designed to be human-readable and editable. The CSV file is also useful for debugging and understanding the protocol.
Detail of CSV file is described in lower section.

# Script Structure
## Top level
- import libraries
- parse arguments
    - JSON file or CSV file
    - Starting tip for left pipette (optional, default="A1")
    - Starting tip for right pipette (optional, default="A1")
    - Slack Notification Webhook URL (optional)
    - mode (optional, default="step")
- evaluate the extension of primary argument
    - if JSON:
        - load JSON file as dict
        - if mode is "command":
            - json2py()
        - else:
            - json2csv()
            - csv2py()
    - if CSV
        - load CSV file as dict
        - csv2py()
## json2py()
For command mode. `commands` object of JSON file is used to generate python script. The script is not organized and is not recommended for editing.
### Input
filename (JSON file), left (optional), right (optional), webhook_url (optional)
### Output
Python script in str
### Sample Code
```python

def json2py(filename: str, left=None, right=None, webhook_url=None) -> str:

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
### Input

## csv2py()
### Input
## Miscellaneous methods
### bottom2top()
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
sample code:
```python
def used_tiprack_parse(left=None, right=None) -> dict:
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



 The script is generated by tracing commands in `commands` object. The script is not organized and is not recommended for editing.

Step mode (default)
More organized one is in `designerApplication` object, as displayed in Protocol Designer web app. For readability, every step number and step notes are inserted as comments.
Step mode of pdjson2py features a few extended control compared to protocol designer, detailed later. 





# Input/Usage
The pdjson2py receive JSON file input in two ways.
1. Published in Opentrons Protocol Library. Input fields are as below.
    1. **`JSON file`:** To upload JSON file. 
    2. **`Starting tip for left pipette (optional)`:** type=str, default="A1" 
    3. **`Starting tip for right pipette (optional)`:** type=str, default="A1"
    4. **`Slack Notification Webhook URL (optional)`:** type=str, default=""
2. Commandline input. A positional argument and keyword arguments as below are accepted. Help comments are just for example.
    1. Primary positional argument. help="The JSON file exported from Protocol Designer."
    2. **`left`:** default="A1", help="For used tiprack reuse of left pipette, input e.g. 'C1'. Not specified indicates all tipracks are filled."
    3. **`right`:** default="A1", help="For used tiprack reuse of right pipette, input e.g. 'E10'. Not specified indicates all tipracks are filled."
    4. **`url`:** default="", help="Slack Webhook URL here like 'https://hooks.slack.com/services/[YOUR]/[WEBHOOK]/[URL]' to enable notification via Slack.
    5. **`source`:** default="step", help="Specify 'command' to enable command mode for debugging. 'commands' object is used to generate python script. By default, GUI equivalent steps in 'designerApplication' obejct is used."
# Supported Protocol Options (Object in JSON file)
## Default Step Mode (designerApplication/data/savedStepForms/[stepId]/**stepType:_____**)
### Transfer (stepType:moveLiquid*)
- passed as argument for `liquid_handling()` method
  - volume per well
  - path (single or multiAspirate or multiDispense)
  - __aspirate_wells_grouped (unclear what is this)__
  - aspirate_flowRate
  - aspirate_labware
  - aspirate_mix_checkbox
  - aspirate_mix_times
  - aspirate_mix_volume
  - aspirate_mmFromBottom
  - aspirate_touchTip_checkbox
  - aspirate_touchTip_mmFromBottom
  - aspirate_touchTip_mmFromBottom
  - dispense_flowRate
  - dispense_labware
  - dispense_mix_checkbox
  - dispense_mix_times
  - dispense_mix_volume
  - dispense_mmFromBottom
  - dispense_touchTip_checkbox
  - dispense_touchTip_mmFromBottom
  - disposalVolume_checkbox
  - disposalVolume_volume
  - blowout_checkbox
  - blowout_location
  - preWetTip
  - aspirate_airGap_checkbox
  - aspirate_airGap_volume
  - aspirate_delay_checkbox
  - aspirate_delay_mmFromBottom
  - aspirate_delay_seconds
  - dispense_airGap_checkbox
  - dispense_airGap_volume
  - dispense_delay_checkbox
  - dispense_delay_seconds
  - dispense_delay_mmFromBottom
- Converted in different way
  - pipette (specified by UUID, stored in pipettes and left/right infor in  StepForms/__INITIAL_DECK_SETUP_STEP__/pipetteLocationUpdate): extract left or right, and specified as pipette object. (Assume no pipettes exchange happen during protocol.)
  - changeTip rule: Configured in script block
  - aspirate_wells/aspirate_wellOrder_first/aspirate_wellOrder_second: Aspilate wells are sorted in advance accroding to wellOrder_first/second in list format, and executed in `liquid_handling()` method.
  - dispense_wells/dispense_wellOrder_first/dispense_wellOrder_second: Dispense wells are sorted in advance accroding to wellOrder_first/second in list format, and executed in `liquid_handling()` method.
  - stepName/stepDetails (print right before script step as a comment in format: [stepName]: [stepDetails] )
### Mix (stepType:mix)
- passed as arguments for `liquid_handling()` method
  - times
  - labware
  - blowout_checkbox
  - blowout_location
  - mix_mmFromBottom
  - volume
  - aspirate_flowRate
  - dispense_flowRate
  - aspirate_delay_checkbox
  - aspirate_delay_seconds
  - dispense_delay_checkbox
  - dispense_delay_seconds
  - mix_touchTip_checkbox
  - mix_touchTip_mmFromBottom
- Converted in different way
  - pipette (specified by UUID, stored in pipettes and left/right **infor** in  StepForms/__INITIAL_DECK_SETUP_STEP__/pipetteLocationUpdate): extract left or right, and specified as pipette object. (Assume no pipettes exchange happen during protocol.)
  - changeTip: Configured in script block
  - wells/mix_wellOrder_first/mix_wellOrder_second: Dispense wells are sorted in advance accroding to wellOrder_first/second in list format, and executed in `liquid_handling()` method.
  - stepName/stepDetails (print right before script step as a comment in format: [stepName]: [stepDetails] )
### HeaterShaker module control (stepType:heaterShaker)
- passed as arguments for official module API.
  - setHeaterShakerTemperature
  - targetHeaterShakerTemperature
  - targetSpeed
  - setShake
  - latchOpen
  - heaterShakerSetTimer
  - heaterShakerTimerMinutes
  - heaterShakerTimerSeconds
- Converted in different way
  - moduleId (specified by UUID, stored in modules.)
  - stepName/stepDetails (print right before script step as a comment in format: [stepName]: [stepDetails] )
### temperature module control (stepType:temperature)
- passed as arguments for official module API.
  - setTemperature
  - targetTemperature
- Converted in different way
  - moduleId (specified by UUID, stored in modules.)
  - stepName/stepDetails (print right before script step as a comment in format: [stepName]: [stepDetails] )
### magnetic module control (stepType:magnet)
- passed as arguments for official module API.
  - magnetAction
  - engageHeight
- Converted in different way
  - moduleId (specified by UUID, stored in modules.)
  - stepName/stepDetails (print right before script step as a comment in format: [stepName]: [stepDetails] )
### thermocycler module control (stepType:thermocycler)
- passed as arguments for official module API. One API line per profileStep/profileCycle due to nesting number limitation of API.
  - thermocyclerFormType (thermocyclerState or thermocyclerProfile)
  - blockIsActive
  - blockTargetTemp
  - lidIsActive
  - lidTargetTemp
  - lidOpen
  - profileVolume
  - profileTargetLidTemp
  - profileItemsById (sort by orderedProfileItems)
    - type (profileStep or profileCycle)
    - repetitions (only in profileCycle)
    - steps (only in profileCycle)
      - temperature
      - durationMinutes
      - durationSeconds
    - temperature (only in profileStep)
    - durationMinutes (only in profileStep)
    - durationSeconds (only in profileStep)
  - blockIsActiveHold
  - blockTargetTempHold
  - lidIsActiveHold
  - lidTargetTempHold
  - lidOpenHold
- Converted in different way
  - moduleId (specified by UUID, stored in modules.)
  - stepName/stepDetails (print right before script step as a comment in format: [stepName]: [stepDetails] )
### Pause control (stepType:pause)
- passed as arguments for official module API. One API line per profileStep/profileCycle due to nesting number limitation of API.
  - pauseAction
  - pauseHour
  - pauseMinute
  - pauseSecond
  - pauseMessage
- Converted in different way
  - moduleId (specified by UUID, stored in modules. monitor temperature of the module by API)
  - stepName/stepDetails (print right before script step as a comment in format: [stepName]: [stepDetails] )
### Move labware (stepType:moveLabware)
- passed as arguments for official module API. One API line per profileStep/profileCycle due to nesting number limitation of API.
  - newLocation
- Converted in different way
  - labware (specified by UUID, stored in modules. print arg as loaded labware variable)
  - stepName/stepDetails (print right before script step as a comment in format: [stepName]: [stepDetails] )
### Extended control (stepType:control)
Extended step type definition to add following features:
- home->protocol.home()
- removeTip->remove tips from all pipettes
- comment->show comment on Opentron app and optionally notify via Slack.
## Command mode


# Limitation and Future Update
- Currently, the pipette exchange is not supported. The pipette is assumed to be fixed during the protocol.
- Liquid level based tip position adjustment is not supported. This feature will be added when liquid volume can be called by API.
- This program is only for OT-2. Opentrons Flex is not supported.
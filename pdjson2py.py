try:
    import json, datetime, argparse
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
args = parser.parse_args()

def bottom2top(json_dict: dict, labware_name_full: str, well_name: str, v_mm:float) -> float:
    # indeed, top2bottom too.
    well_depth = json_dict['labwareDefinitions'][labware_name_full]['wells'][well_name]['depth']
    return v_mm - well_depth

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

def otjson2py(filename: str, tiprack_assign=None, webhook_url=None) -> str:
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
    metadata['apiLevel'] = '2.13'
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

    # Specifying starting well of the used tiprack.
    if tiprack_assign == None or tiprack_assign == 'auto':
        used_tiprack = False
    else:
        used_tiprack = True
        starting_tip_well = used_tiprack_parse(tiprack_assign)
        
    with open('output.py', 'w') as f:
# header
        f.write('from opentrons import protocol_api\n\n')
        f.write(f'metadata = {metadata}\n\n')
        if webhook_url != None:
            f.write(f'webhook_url = "{webhook_url}"\n\n')
            f.write("import json\nimport urllib.request\n\ndef send_to_slack(webhook_url, message):\n    data = {\n        'text': message,\n        'username': 'MyBot',\n        'icon_emoji': ':robot_face:'\n    }\n    data = json.dumps(data).encode('utf-8')\n\n    headers = {'Content-Type': 'application/json'}\n\n    req = urllib.request.Request(webhook_url, data, headers)\n    with urllib.request.urlopen(req) as res:\n        if res.getcode() != 200:\n            raise ValueError(\n                'Request to slack returned an error %s, the response is:\\n%s'\n                % (res.getcode(), res.read().decode('utf-8'))\n            )\n\n")
        f.write('def run(protocol: protocol_api.ProtocolContext):\n')
        
# load modules
        for key in modules.keys():
            if pdjson['designerApplication']['data']['savedStepForms']['__INITIAL_DECK_SETUP_STEP__']['moduleLocationUpdate'][key] == 'span7_8_10_11':
                slot = '7'
            else:
                slot = pdjson['designerApplication']['data']['savedStepForms']['__INITIAL_DECK_SETUP_STEP__']['moduleLocationUpdate'][key]
            f.write(f"  {modules_name[key][0:6].lower()}mod_{slot} = protocol.load_module(module_name='{modules_name[key]}',"
                        f"location='{slot}')\n")
            modules[key] = f"{modules_name[key][0:6].lower()}mod_{slot}"
            
# load labwares
        for key in labwares.keys():
            slot = pdjson['designerApplication']['data']['savedStepForms']['__INITIAL_DECK_SETUP_STEP__']['labwareLocationUpdate'][key]
            if slot in modules :
                f.write(f"  {pdjson['labwareDefinitions'][key.split(':')[1]]['metadata']['displayCategory'].lower()}_{modules[slot]} = {modules[slot]}.load_labware('{labwares_name[key]}')\n")
                labwares[key] = f"{pdjson['labwareDefinitions'][key.split(':')[1]]['metadata']['displayCategory'].lower()}_{modules[slot]}"
            elif key != 'fixedTrash':
                f.write(f"  {pdjson['labwareDefinitions'][key.split(':')[1]]['metadata']['displayCategory'].lower()}_{slot} = protocol.load_labware(load_name='{labwares_name[key]}', "
                            f"location='{slot}')\n")
                labwares[key] = f"{pdjson['labwareDefinitions'][key.split(':')[1]]['metadata']['displayCategory'].lower()}_{slot}"

# load pipettes
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
                f.write(f"  {mount}_pipette = protocol.load_instrument(instrument_name='{pipettes_name[pipId]}', mount='{mount}',tip_racks={tipracks_str})\n")
                if used_tiprack == True:
                    f.write(f"  {mount}_pipette.starting_tip = {ini_tiprack}.well('{starting_tip_well[mount]}')\n")
            else:
                f.write(f"  {mount}_pipette = protocol.load_instrument(instrument_name='{pipettes_name[pipId]}', mount='{mount}')\n")
            pipettes[pipId] = f"{mount}_pipette"
        
# Commands
        for i in range(len(pdjson['commands'])):
            command_step = pdjson['commands'][i]
# for debug
            if i%20 == 0 and i > 19:
                f.write(f'# command no. {i}\n')
                
# liquid handling
            if command_step['commandType'] == 'pickUpTip' and (tiprack_assign == 'auto' or used_tiprack == True):
                f.write(f"  {pipettes[command_step['params']['pipetteId']]}.pick_up_tip()\n")
            elif command_step['commandType'] == 'pickUpTip':
                f.write(f"  {pipettes[command_step['params']['pipetteId']]}"
                        f".pick_up_tip(location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'])\n")
            elif command_step['commandType'] == 'aspirate':
                f.write(f"  {pipettes[command_step['params']['pipetteId']]}"
                        f".aspirate(volume={command_step['params']['volume']}, "
                        f"location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'].bottom(z={command_step['params']['wellLocation']['offset']['z']}), "
                        f"rate={command_step['params']['flowRate']})\n")
            elif command_step['commandType'] == 'dispense':
                f.write(f"  {pipettes[command_step['params']['pipetteId']]}"
                        f".dispense(volume={command_step['params']['volume']}, "
                        f"location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'].bottom(z={command_step['params']['wellLocation']['offset']['z']}), "
                        f"rate={command_step['params']['flowRate']})\n")
            elif command_step['commandType'] == 'blowout':
                f.write(f"  {pipettes[command_step['params']['pipetteId']]}"
                        f".blow_out(location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'].bottom(z={command_step['params']['wellLocation']['offset']['z']}))\n")
            elif command_step['commandType'] == 'dropTip':
                f.write(f"  {pipettes[command_step['params']['pipetteId']]}.drop_tip()\n")
            elif command_step['commandType'] == 'touchTip':
                f.write(f"  {pipettes[command_step['params']['pipetteId']]}"
                        f".touch_tip(location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'], "
                        f"v_offset={bottom2top(pdjson, str(command_step['params']['labwareId'].split(':')[1]), command_step['params']['wellName'], command_step['params']['wellLocation']['offset']['z'])})\n")
            elif command_step['commandType'] == 'moveToWell':   # used in delay
                f.write(f"  {pipettes[command_step['params']['pipetteId']]}." 
                        f"move_to(location={labwares[command_step['params']['labwareId']]}['{command_step['params']['wellName']}'].bottom(z={command_step['params']['wellLocation']['offset']['z']}))\n")

# heater-shaker module control
            elif command_step['commandType'] == 'heaterShaker/closeLabwareLatch':
                f.write(f"  {modules[command_step['params']['moduleId']]}." 
                        f"close_labware_latch()\n")
            elif command_step['commandType'] == 'heaterShaker/setTargetTemperature':
                f.write(f"  {modules[command_step['params']['moduleId']]}." 
                        f"set_target_temperature({command_step['params']['celsius']})\n")
            elif command_step['commandType'] == 'heaterShaker/setAndWaitForTemperature':
                f.write(f"  {modules[command_step['params']['moduleId']]}." 
                        f"set_and_wait_for_temperature({command_step['params']['celsius']})\n")
            elif command_step['commandType'] == 'heaterShaker/setAndWaitForShakeSpeed':
                f.write(f"  {modules[command_step['params']['moduleId']]}." 
                        f"set_and_wait_for_shake_speed({command_step['params']['rpm']})\n")
            elif command_step['commandType'] == 'heaterShaker/deactivateShaker':
                f.write(f"  {modules[command_step['params']['moduleId']]}." 
                        f"deactivate_shaker()\n")
            elif command_step['commandType'] == 'heaterShaker/deactivateHeater':
                f.write(f"  {modules[command_step['params']['moduleId']]}." 
                        f"deactivate_heater()\n")
            elif command_step['commandType'] == 'heaterShaker/waitForTemperature':
                f.write(f"  {modules[command_step['params']['moduleId']]}." 
                        f"wait_for_temperature({command_step['params']['celsius']})\n")
            elif command_step['commandType'] == 'heaterShaker/deactivateHeater':
                f.write(f"  {modules[command_step['params']['moduleId']]}." 
                        f"deactivate()\n")         

# magnetic module control
            elif command_step['commandType'] == 'magneticModule/engage':
                f.write(f"  {modules[command_step['params']['moduleId']]}.engage(height_from_base={command_step['params']['height']})\n")
            elif command_step['commandType'] == 'magneticModule/disengage':
                f.write(f"  {modules[command_step['params']['moduleId']]}.disengage()\n")
# temperature module control
            elif command_step['commandType'] == 'temperatureModule/setTargetTemperature':
                if pdjson['commands'][i+1].get('commandType') == 'temperatureModule/waitForTemperature':
                    f.write(f"  {modules[command_step['params']['moduleId']]}.set_temperature(celsius={command_step['params']['celsius']})\n")
                else:
                    f.write(f"  {modules[command_step['params']['moduleId']]}.start_set_temperature(celsius={command_step['params']['celsius']}) # Hidden API\n")
            elif command_step['commandType'] == 'temperatureModule/waitForTemperature':
                f.write(f"  while {modules[command_step['params']['moduleId']]}.temperature != {command_step['params']['celsius']}:\n    protocol.delay(seconds=1)\n")
            elif command_step['commandType'] == 'temperatureModule/deactivate':
                f.write(f"  {modules[command_step['params']['moduleId']]}.deactivate()\n")
            
# thermocycler module control
            elif command_step['commandType'] == 'thermocycler/openLid':
                f.write(f"  {modules[command_step['params']['moduleId']]}.open_lid()\n")
            elif command_step['commandType'] == 'thermocycler/closeLid':
                f.write(f"  {modules[command_step['params']['moduleId']]}.close_lid()\n")
            elif command_step['commandType'] == 'thermocycler/deactivateBlock':
                f.write(f"  {modules[command_step['params']['moduleId']]}.deactivate_block()\n")
            elif command_step['commandType'] == 'thermocycler/deactivateLid':
                f.write(f"  {modules[command_step['params']['moduleId']]}.deactivate_lid()\n")
            elif command_step['commandType'] == 'thermocycler/setTargetBlockTemperature':
                f.write(f"  {modules[command_step['params']['moduleId']]}.set_block_temperature(temperature={command_step['params']['celsius']})\n")
            elif command_step['commandType'] == 'thermocycler/setTargetLidTemperature':
                f.write(f"  {modules[command_step['params']['moduleId']]}.set_lid_temperature(temperature={command_step['params']['celsius']})\n")
            elif command_step['commandType'] == 'thermocycler/waitForLidTemperature' or command_step['commandType'] == 'thermocycler/waitForBlockTemperature':
                None # set_*_temperature pauses protocol untill the temperature reaches
            elif command_step['commandType'] == 'thermocycler/deactivateLid':
                f.write(f"  {modules[command_step['params']['moduleId']]}.deactivate_lid()\n")
            elif command_step['commandType'] == 'thermocycler/deactivateBlock':
                f.write(f"  {modules[command_step['params']['moduleId']]}.deactivate_block()\n")
            elif command_step['commandType'] == 'thermocycler/runProfile':
                steps = []
                for item in command_step['params']['profile']:
                    step = {}
                    step['temperature'],step['hold_time_seconds'] = item['celsius'],item['holdSeconds']
                    steps.append(step)
                steps = str(steps)
                f.write(f"  {modules[command_step['params']['moduleId']]}.execute_profile(steps={steps},repetitions=1,block_max_volume={command_step['params']['blockMaxVolumeUl']})\n")
# other control      
            elif command_step['commandType'] == 'delay' and command_step['params'].get('seconds') == None :
                message = str(command_step['params'].get('message'))
                if webhook_url != None:
                    f.write(f'  send_to_slack(webhook_url,"Your OT-2 has said: {message}")\n')
                f.write('  protocol.pause(msg="' + message + '")\n')
            elif command_step['commandType'] == 'delay' :
                message = str(command_step['params'].get('message'))
                f.write(f"  protocol.delay(seconds={command_step['params'].get('seconds')}, msg='{message}')\n")
            elif command_step['commandType'] == 'loadLiquid' or command_step['commandType'] == 'loadPipette' or command_step['commandType'] == 'loadLabware' or command_step['commandType'] == 'loadModule':
                # loading liquid, begins from API 2.14 is not supported.
                None
            else:
                f.write(f"not persed: {command_step['commandType']}, {i}\n")
                
        if webhook_url != None:
            f.write(f'  send_to_slack(webhook_url,"Your OT-2 protocol has just completed!")\n')

otjson2py2(args.arg1,tiprack_assign=args.arg2,webhook_url=args.arg3)

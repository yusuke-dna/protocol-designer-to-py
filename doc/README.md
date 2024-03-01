# Documents for new version of pdjson2py
The content is under preparation for future update. Latest version, utilising Step instead of Command of JSON file is available as default setting. For debug or specific purpose, command mode is available with `command` option.
# Overview
protocol-designer-to-py, or `pdjson2py`, is to convert JSON file exported from the Opentrons Protocol Designer (ver. 8.01) into Python script for Opentrons Python API 2.16. `pdjson2py` only supports OT-2, for now. The generated python script (`.py`) or step file (`.csv`) will be used as a template of users' in-house protocol coding (e.g. introducing logics or loop, change pipetting parameters), to minimize users' coding efforts and to avoid human errors.

For that purpose, the output python script is designed to be flexible for editing and is equiped with user-friendly variables and comments ready for edit.

The code is consists of (1) Simple JSON to Python converter (`json2py()`), (2) JSON to CSV converter (`json2csv()`), (3) step CSV file to step dictionary converter (`csv2dict()`), (4) step dictionary to Python converter (`dict2py()`), (5) comprehensive `liquid_handling()` method (hard-copied to output Python file by `write_liquid_handling()`) and (6) miscellaneous methods and variables.

## Data Processing Flow Chart
<img width="1344" alt="image" src="https://github.com/yusuke-dna/protocol-designer-to-py/assets/70700401/7317b51b-92b9-4ad3-a664-98808e91fc47">

### JSON file scenario (New Protocol Preparation)
1. Design your own protocol using `Opentrons Protocol Designer` and export `JSON file`.
2. Input `JSON file` to `pdjson2py` with optional parameters via `Opentrons Protocol Library (Web app)` or `Command Line Interface (CLI)`.
3. In `pdjson2py`, if input file is `JSON file`, go to step 4. If input file is `CSV file`, skip step 4-5 and go to step 6.
4. In `pdjson2py`, if command option is not specified, go to step 5-1 (default). If command option is specified, go to step 5-2.
5. In `pdjson2py`, 
    1. `json2csv()` converts `JSON file` to `CSV file` storing protocol steps. The step CSV file is available from the form link (`Web app`) or generated in the directly (`CLI`). The CSV file name is `[input_file_name].csv`.
    2. `json2py()` converts `JSON file` to `Python script`. The Python script is available from the form link (`Web app`) or generated in the directly (`CLI`). The Python script name is `[input_file_name]_command.py`.
6. In `pdjson2py`, `csv2dict()` converts `CSV file` to `step_dict (Python dictionary)`. The `step_dict` is an internal and intermediate data structure.
7. In `pdjson2py`, `dict2py()` converts `step_dict` to `Python script`. The Python script is available from the form link (`Web app`) or generated in the directly (`CLI`). The Python script name is `[input_file_name].py`. The user may modify configurations or add logics in the Python script.
8. Run the Python script in `Opentrons App`.

### CSV file scenario (Edit Existing Protocol)
1. Design your own protocol by modifying existing `CSV file` (step file previously generated from `pdjson2py`) or using external step CSV generator.
2. Input `CSV file` to `pdjson2py` with optional parameters via `Web app` or `CLI`.
3. In `pdjson2py`, if input file is `CSV file`, skip step 4-5 and go to step 6. ~~If input file is `JSON file`, go to step 4.~~
4. Skipped
5. Skipped
6. In `pdjson2py`, `csv2dict()` converts `CSV file` to `step_dict (Python dictionary)`. The `step_dict` is an internal and intermediate data structure.
7. In `pdjson2py`, `dict2py()` converts `CSV file` to `Python script`. The Python script is available from the form link (`Web app`) or generated in the directly (`CLI`). The Python script name is `protocol.py`. The user may modify configurations or add logics in the Python script.
8. Run the Python script in `Opentrons App`.

## Options
### Command mode (JSON file input is required)
The protocol of liquid handling is stored in JSON file in two different ways. Simpler one is in `commands` object. Command mode traces and literally translates commands to Python API step by step. Serial number is marked every 10 commands for readability.
### Default mode, both JSON and CSV file input are available)
More organized one is in `designerApplication` object, as displayed in Protocol Designer web app. For readability, every step number and step notes are inserted as comments.
### Debug mode (both JSON and CSV file input are available)
Step mode with detailed comments in the generated Python script. It is useful for debugging and understanding the protocol.

## CSV file
CSV file is an intermediate file format to describe the protocol. It is converted from JSON file, particulary `designerApplication` object and can be used as an input for pdjson2py. The CSV file is designed to be human-readable and editable. The CSV file is also useful for debugging and understanding the protocol.
Detail of CSV file is described in lower section.

# Script Structure
## Top level
- import libraries
- parse arguments
    - `input_filename` # JSON file or CSV file
    - `left` # Starting tip for left pipette (optional, default="A1")
    - `right` # Starting tip for right pipette (optional, default="A1")
    - `webhook_url` # Slack Notification Webhook URL (optional, default=None)
    - `option` #Logic selection (optional, default=None, one of [None, "command", "debug"])
- set global variables
    - `tiprack_assign` = used_tiprack_parse(left, right)
- if primary argument is JSON file:
    - load JSON file as dict, `pdjson`
    - set global variables
      - `default_aspirate_offset` = pdjson['designerApplication']['data']['defaultValues']['aspirate_mmFromBottom']
      - `default_dispense_offset` = pdjson['designerApplication']['data']['defaultValues']['dispense_mmFromBottom']
      - `default_touch_tip_offset` = pdjson['designerApplication']['data']['defaultValues']['touchTip_mmFromTop']
      - `default_blowout_offset` = pdjson['designerApplication']['data']['defaultValues']['blowout_mmFromTop']
    - if mode is "command":
        - `json2py()` to generate Python script, end.
    - else:
        - `json2csv()` to generate intermediate CSV file
        - `csv2step()` to load CSV file as dict
        - `step2py()` to generate Python script, end.
- else if primary argument is CSV file:
    - `csv2step()` to load CSV file as dict, `step_dict`
    - set global variables
      - `default_aspirate_offset` = step_dict['defaultValues']['aspirate_offset']
      - `default_dispense_offset` = step_dict['defaultValues']['dispense_offset']
      - `default_touch_tip_offset` = step_dict['defaultValues']['touch_tip_offset']
      - `default_blowout_offset` = step_dict['defaultValues']['blowout_offset']
    - `step2py()` to generate Python script, end.
## json2py()
A method for command mode. `commands` object of JSON file is used to generate python script. The script is not organized and is not recommended for editing.
### Input
- filename (JSON file)
- left (optional, default="A1")
- right (optional, default="A1")
- webhook_url (optional, default=None)
### Output
- Python script in str, with file name `[filename of json without extension]_command.py`.
### [Sample Code](./sample-codes.md#json2py)

## json2csv()
A method for converting JSON file to CSV file. The CSV file is designed to be human-readable and editable.
### Input
- filename (JSON file)
- left (optional, default="A1")
- right (optional, default="A1")
- webhook_url (optional, default=None)
- option (optional, default=None, either None or "debug")
### Output
- CSV file in str, with file name `[filename of json file without extension].csv`.
### CSV structure
See [another file].
### [Sample Code](./sample-codes.md#json2csv)

## csv2dict()
Code block for converting CSV file to dict form, similar to command object of JSON file.The Python dictionary is used as an intermediate data structure.
### Input
- filename (CSV file)
### Output
- step_dict (dict format object)
### [Sample Code](./sample-codes.md#csv2step)

## dict2py()
Code block for converting CSV file to Python script. The Python script is designed to be human-readable and suitable for used as a template.
### Input
- step_dict (dict format object)
- left (optional, default="A1")
- right (optional, default="A1")
- webhook_url (optional, default=None)
- option (optional, default=None, either None or "debug")
### Output
- Python script in str, with file name `[filename of csv file without extension].py`.
### [Sample Code](./sample-codes.md#step2py)

## write_header()
Common script block of protocol.py and protocol_command.py is printed by this method.
### Input
- output_filename (str)
- metadata (dict)
- webhook_url (str)
### Output
- Python script in str, with `output_filename`. Main script block continues by `json2py()` or `dict2py` method.
### [Sample Code](./sample-codes.md#write_header)

## write_liquid_handling()
Comprehensive `liquid_handling()` method is printed by this method. The method is hard-copied to output Python file by `dict2py()` method. Command mode does not use it.
### Input
- aspirate_offset (float)
- dispense_offset (float)
- touch_tip_offset (float)
- blowout_offset (float)
### Output

### [Sample Code](./sample-codes.md#write_liquid_handling)

## Miscellaneous methods in pdjson2py

### bottom2top()
Convert between "height from top of the well" and "height from bottom of the well". It is used for touchTip configuration in command mode. [Sample code here](./sample-codes.md#bottom2top).

### used_tiprack_parse()
Generate dictionary of starting tip well from input string. If input string is missing alphabetic part, calculate it based on numeric part assuming the labware has eight rows. [Sample code here](./sample-codes.md#used_tiprack_parse).

### sort_wells()
Wells (list) are sorted based on first_sort and second_sort. [Sample code here](./sample-codes.md#sort_wells).

# How to use pdjson2py
The pdjson2py receive JSON file input in two ways.
1. Published in Opentrons Protocol Library. Input fields are as below.
    1. **`JSON file or CSV file`:** To upload JSON file or CSV file. 
    2. **`Starting tip for left pipette (optional)`:** type=str, default="A1" 
    3. **`Starting tip for right pipette (optional)`:** type=str, default="A1"
    4. **`Slack Notification Webhook URL (optional)`:** type=str, default=""
    5. **`Mode (optional)`:** type=str, default="step", choices=["step", "command", "debug"] 
        - If "command" is selected and the input file is CSV, default "step" mode is applied. (CSV file does not have information for command mode.)
2. Command line input. A positional argument and keyword arguments as below are accepted. Help comments are just for example.
    1. Primary positional argument. help="The JSON file exported from Protocol Designer or the CSV file generated by pdjson2py."
    2. **`left`:** default="A1", help="For used tiprack reuse of left pipette, input first filled well, e.g. 'C1'. Not specified indicates all tipracks are filled."
    3. **`right`:** default="A1", help="For used tiprack reuse of right pipette, input first filled well, e.g. 'E10'. Not specified indicates all tipracks are filled."
    4. **`url`:** default="", help="Slack Webhook URL here like 'https://hooks.slack.com/services/[YOUR]/[WEBHOOK]/[URL]' to enable notification via Slack.
    5. **`mode`:** default="step", help="Specify 'command' to enable command mode for debugging. 'commands' object is used to generate python script. By default, GUI equivalent steps in 'designerApplication' obejct is used."
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
- Currently, the pipette exchange and module relocation are not supported. The pipette and module is assumed to be fixed during the protocol.
- Liquid level based tip position adjustment is not supported. This feature will be added when liquid volume of the specific labware can be called by API. For now, liquid object is just loaded to protocol but not traced.
- This program is only for OT-2. Opentrons Flex is not supported.
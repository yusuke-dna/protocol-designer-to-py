# Documents for new version of pd2py
The content is under preparation for future update. Latest version, utilising Step instead of Command of JSON file is available as default setting. For debug or specific purpose, command mode is available by adding fourth argument `command`
# Overview
protocol-designer-to-py, `pd2py`, is to convert JSON file exported from Opentrons Protocol Designer (ver. 8.01) into Python script for Opentrons Python API 2.16. `pd2py` only support OT-2. The generated python file will be used as a template of users' in-house protocol coding. Thus the python protocol should be flexible and is equiped with user-friendly variables and comments ready for edit.
## Command mode (only available in CLI)
The protocol of liquid handling is stored in JSON file in two different ways. Simpler one is in `commands` object. Command mode traces and literally translates commands to Python API step by step. Serial number is marked every 10 commands for readability.
## Step mode (default)
More organized one is in `designerApplication` object, as displayed in Protocol Designer web app. For readability, every step number and step notes are inserted as comments.
Step mode of pd2py features a few extended control compared to protocol designer, detailed later. 
# Input/Usage
The pd2py receive JSON file input in two ways.
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
## Transfer (designerApplication/data/savedStepForms/[stepId]/**stepType:moveLiquid**)
- passed as argument for `liquid_handling()` method
  - volume per well
  - path (single or multiAspirate or multiDispense)
  __- aspirate_wells_grouped (unclear what is this)__
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
## Mix (designerApplication/data/savedStepForms/[stepId]/**stepType:mix**)
- passed as argument for `liquid_handling()` method
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
  - pipette (specified by UUID, stored in pipettes and left/right infor in  StepForms/__INITIAL_DECK_SETUP_STEP__/pipetteLocationUpdate): extract left or right, and specified as pipette object. (Assume no pipettes exchange happen during protocol.)
  - changeTip: Configured in script block
  - wells/mix_wellOrder_first/mix_wellOrder_second: Dispense wells are sorted in advance accroding to wellOrder_first/second in list format, and executed in `liquid_handling()` method.



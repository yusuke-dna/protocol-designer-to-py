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
# Supported Protocol Block
## Transfer

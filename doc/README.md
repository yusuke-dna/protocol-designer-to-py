# Documents for new version of pd2py
The content is under preparation. New version, utilising Step instead of Command of JSON file is available as default setting. For debug or specific purpose, command mode is available by adding fourth argument `command`
# Overview
This `protocol`, pd2py, is to convert JSON file format OT-2 protocol prepared by Opentrons Protocol Designer (ver. 8.01) into Python script for Opentrons Python API 2.17. The generated python file will be used as a template of users' in-house protocol coding. Thus the python protocol should be flexible and is equiped with user-friendly variables and comments ready for edit.
# Input
The pd2py accepts JSON file input in two ways.
1. Published in Opentrons Protocol Library. The protocol has only single field, `JSON file` to upload JSON file.
2. 

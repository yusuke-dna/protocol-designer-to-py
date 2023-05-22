# protocol-designer-to-py
A tool to convert JSON file generated by Opentrons' official Protocol Designer to python script for OT-2.
# How to use
1. Create protocol using Opentrons' official Protocol Designer.
2. Export JSON file.
3. Go to the directory containing the python script, "pdjson2py.py".
4. type below:
```
$ python3 pdjson2py.py file/path/to/protocol/designer/json/file
```
5. Then the python script, "output.py" will be generated in the directory.
6. By default, the script selects tips based on the JSON file's "commands" object, which may result in picking tips in unexpected order when you edit the output Python file. Use the "auto" secondary argument to remove the pre-assigned tip locations and automatically assign tipracks from the Protocol Designer's initial deck state to the pipettes.
```
$ python3 pdjson2py.py file/path/to/protocol/designer/json/file auto
```
# Limitations
* Not all of parameters are supported, but to be supported in future.
* Only API version 2.13 is and will be supported, but not restricted. (liquid status is not supported)
* Transfer in Commands object of JSON file is expressed as a combination of aspriate and dispense. The generated python file keeps the structure. Same to single cycle long profile in thermocycler.
* Bug reports are welcome to improve the script.

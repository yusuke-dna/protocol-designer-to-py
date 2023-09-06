# protocol-designer-to-py
A tool to convert JSON file generated by Opentrons' official Protocol Designer to python script for OT-2.
# How to use
1. Create protocol using Opentrons' official Protocol Designer.
2. Export JSON file.
3. Go to the directory containing the python script, "pdjson2py.py".
4. type below:
```
python3 pdjson2py.py file/path/to/protocol/designer/json/file
```
5. Then the python script, "output.py" will be generated in the directory.
6. Optionally, you can assign one used tiprack per pipette by specifying the starting well associated with either the left or the right pipette.
```
# For two pipettes, specify the wells in the format [left pipette]/[right pipette]. No blanks are allowed. Use 'A1' if the left pipette uses a new tiprack, like:
$ python3 pdjson2py.py /path/to/protocol/designer/json/file A1/C3

# For single pipette usage (left/right unspecified), specify the well as follows:
$ python3 pdjson2py.py /path/to/protocol/designer/json/file B10
```
7. A Slack notification feature is available when you include the Slack webhook URL as the third argument. In this case, the second argument should be used tiprack option as above or None.
```
$ python3 pdjson2py.py file/path/to/protocol/designer/json/file None https://hooks.slack.com/services/[YOUR]/[WEBHOOK]/[URL]
```
8. Former version, extracting command list from JSON file, is available by adding the fourth argument `command`. By default in command mode, the script selects tips hard-written in "commands" object within the JSON file. This could lead to an unexpected order of tip selection when modifying the output Python file. To mitigate this, use the "auto" argument in used tip option. This removes pre-defined tip locations and allows the automatic assignment of tipracks to the pipettes, from the initial deck state in the Protocol Designer.
```
$ python3 pdjson2py.py /path/to/protocol/designer/json/file auto https://hooks.slack.com/services/[YOUR]/[WEBHOOK]/[URL] command
```
```
$ python3 pdjson2py.py /path/to/protocol/designer/json/file auto command
```
```
$ python3 pdjson2py.py /path/to/protocol/designer/json/file command
```

# Limitations
* Not all of parameters are supported, but to be supported in future.
* Used tip assignment limits API version to 2.13 (due to API bug). When used tip is not assigned, API version is 2.14 and liquid status is loaded.
* Transfer in Commands mode object of JSON file is expressed as a combination of aspriate and dispense. The generated python file keeps the structure. Same to single cycle long profile in thermocycler.
* Bug reports are welcome to improve the script.

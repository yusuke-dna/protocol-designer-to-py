# protocol-designer-to-py
A tool to convert JSON file generated by Opentrons' official Protocol Designer to python script for OT-2.
# How to use
1. Prepare OT-2 protocol using Opentrons' official Protocol Designer.
2. Export JSON file.
3. Navigate to the directory containing the python script, "pdjson2py.py".
4. type below:
```
python3 pdjson2py.py file/path/to/protocol/designer/json/file.json
```
5. Then the python script, "output.py" will be generated in the directory.
6. Optionally, you can assign one used tiprack per pipette by specifying the starting well associated with either the left or the right pipette.
```
# For two pipettes, specify the wells in the format [left pipette]/[right pipette].
# No blanks are allowed. Use 'A1' if the left pipette uses a new tiprack, like:
python3 pdjson2py.py file/path/to/protocol/designer/json/file.json A1/C3
```
```
# For single pipette usage (left/right unspecified), specify the well as follows:
python3 pdjson2py.py file/path/to/protocol/designer/json/file.json B10
```
7. A Slack notification feature is available when you include the Slack webhook URL as the second or third argument.
```
python3 pdjson2py.py file/path/to/protocol/designer/json/file.json A1/C3 https://hooks.slack.com/services/[YOUR]/[WEBHOOK]/[URL]
```
```
python3 pdjson2py.py file/path/to/protocol/designer/json/file.json https://hooks.slack.com/services/[YOUR]/[WEBHOOK]/[URL]
```
8. Former version, extracting command list from JSON file, is available by adding the fourth argument `command` (all below three work). In command mode, the pipette picks up tips from hard-written location in "commands" object in the JSON file. This could lead to an unexpected order of tip selection when modifying the output Python file. To mitigate this, use the "auto" argument in used tip option. This removes pre-defined tip locations and allows the automatic assignment of tipracks to the pipettes, from the initial deck state in the Protocol Designer.
```
python3 pdjson2py.py /path/to/protocol/designer/json/file.json auto https://hooks.slack.com/services/[YOUR]/[WEBHOOK]/[URL] command
```
```
python3 pdjson2py.py /path/to/protocol/designer/json/file.json auto command
```
```
python3 pdjson2py.py /path/to/protocol/designer/json/file.json command
```

# Limitations
* All options in Protocol Designer ver. 6.2.2. is supported but the behavior is not identical. For instance, Default pipette flow rate of current API is twice faster than that of Protocol Designer adopts. Other intentional difference is commented in the code.
* Used tip assignment limits API version to 2.13 (due to API bug). When used tip is not assigned, API version is 2.14 and liquid status is loaded.
* Transfer in Commands mode object of JSON file is expressed as a combination of aspriate and dispense. The generated python file keeps the structure. Same to single cycle long profile in thermocycler.
* Bug reports are welcome to improve the script.

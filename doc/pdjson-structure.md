# Data structure of Protocol Designer JSON in aspect of data handling
Not atempting to generate PY2JSON, but the JSON file will be scaffold of collecting OT-2 control info, given in CSV form.
#  root
## metadata
### protocolName
- copied from CSV file name
### author
- copied from metadata
### description
- copied from metadata
### created
- copied from metadata
- converted to millisecond timestamp
### lastmodified
- copied from metadata
- converted to millisecond timestamp
## designerApplication
- 3 item dict[various]
### name
### version
### data
- 8 item dict[various]
- mainly used to generate python protocol file
#### _internalAppBuildDate
#### defaultValues
- 4 item dict[various]
##### aspirate_mmFromBottom	:	1
##### dispense_mmFromBottom	:	0.5
##### touchTip_mmFromTop	:	-1
##### blowout_mmFromTop	:	0
#### pipetteTiprackAssignments
- dict[pipette UUID], value: definitionId
#### dismissedWarnings
- two item dict.
#### ingredients
- dict[liquidGroupId]
##### [liquidGroupId]
- 5 items dict[various]
###### name
###### displayColor
###### description
###### serialize
###### liquidGroupId
#### ingredLocations
- dict[UUID:definitionId]
- used to load liquid into labwares
##### [UUID]
- dict[well name]
###### well name
- dict[liquidGroupId]
####### volume
#### savedStepForms
- dict[step UUID, __INITIAL_DECK_SETUP_STEP__]
- initial deck setup is also used in loading
##### [__INITIAL_DECK_SETUP_STEP__]
- 5 items dict[various]
###### labwareLocationUpdate
- 8 items dict[UUID:definitionId], value: slot or UUID:ModuleType
##### [step UUID]
- various number items dict[various] depending on step type.
- Used in loading steps.
#### orderedStepIds
- list in order of execution
- UUID of steps

## robot
- dict[model/decId]
### model
### decId
## pipettes
- dict[UUID]
### name
- used to load pipette. Name format is e.g. p20_single_gen2
## labware
- dict[UUID:definitionId or fixedTrash]
- Used to load labware, by extracting second word of labware definition ID (e.g. opentrons_96_tiprack_20ul)
### displayName
### definitionId
## liquids
- dict[liquid serial]
- Used to load liquid (≥API 2.14)
### displayName
### description
### displayColor
## labwareDefinitions
- dict[definitionId]
- labware definition ID is in strange format like opentrons/opentrons_96_tiprack_20ul/1
- Some difinition is used in calculation
  ### ordering
  ### brand
  ### metadata
  ### dimensions
  ### wells
  ### groups
  ### parameters
  ### namespace
  ### version
  ### schemaVersion
  ### cornerOffsetFromSlot
## $otSharedSchema
## schemaVersion
## modules
- dict[UUID] of module model
- UUID key, dict value
- Used to load modules
### [UUID]
#### model
## commands
- list of command dict.
- used in current pdjson2py

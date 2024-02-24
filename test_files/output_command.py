from opentrons import protocol_api
import json, urllib.request, math

metadata = {'protocolName': 'comprehensive_test_file', 'author': 'RIKEN/Yusuke Sakai', 'description': 'Attempt to convert JSON to Py', 'created': '2023-04-29 00:53:38.084000', 'lastModified': '2023-09-05 22:16:38.807000', 'category': 'n/a', 'subcategory': 'n/a', 'tags': '[]', 'apiLevel': '2.13'}

webhook_url = "https://hooks.slack.com/services/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"

def send_to_slack(webhook_url, message):
    data = {
        'text': message,
        'username': 'MyBot',
        'icon_emoji': ':robot_face:'
    }
    data = json.dumps(data).encode('utf-8')

    headers = {'Content-Type': 'application/json'}

    req = urllib.request.Request(webhook_url, data, headers)
    with urllib.request.urlopen(req) as res:
        if res.getcode() != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (res.getcode(), res.read().decode('utf-8'))
            )

def run(protocol: protocol_api.ProtocolContext):
    module2 = protocol.load_module(module_name='heaterShakerModuleV1',location='1')
    module3 = protocol.load_module(module_name='magnetic module gen2',location='9')
    module4 = protocol.load_module(module_name='temperature module gen2',location='6')
    module5 = protocol.load_module(module_name='thermocycler module',location='7')
    labware6 = protocol.load_labware(load_name='opentrons_96_tiprack_20ul', location='5')
    labware7 = protocol.load_labware(load_name='opentrons_96_tiprack_300ul', location='4')
    labware8 = module5.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    labware9 = module4.load_labware('opentrons_24_aluminumblock_nest_2ml_snapcap')
    labware10 = module2.load_labware('opentrons_96_deep_well_adapter_nest_wellplate_2ml_deep')
    labware11 = module3.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    labware12 = protocol.load_labware(load_name='opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', location='3')
    pipette0 = protocol.load_instrument(instrument_name='p20_single_gen2', mount='left',tip_racks=[labware6])
    pipette0.starting_tip = labware6.well('B4')
    pipette1 = protocol.load_instrument(instrument_name='p300_multi_gen2', mount='right',tip_racks=[labware7])
    pipette1.starting_tip = labware7.well('D1')
    pipette1.pick_up_tip()
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A1'].bottom(z=1))

# command no. 20
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A1'].bottom(z=1))
    pipette1.move_to(location=labware11['A1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette1.touch_tip(location=labware11['A1'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A1'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A5'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A5'].bottom(z=0.5))
    pipette1.move_to(location=labware11['A5'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette1.touch_tip(location=labware11['A5'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A5'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.drop_tip()
    pipette1.pick_up_tip()
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A2'].bottom(z=1))

# command no. 40
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A2'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A2'].bottom(z=1))
    pipette1.move_to(location=labware11['A2'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette1.touch_tip(location=labware11['A2'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A2'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A6'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A6'].bottom(z=0.5))
    pipette1.move_to(location=labware11['A6'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette1.touch_tip(location=labware11['A6'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A6'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.drop_tip()
    pipette1.pick_up_tip()
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A3'].bottom(z=1))

# command no. 60
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A3'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A3'].bottom(z=1))
    pipette1.move_to(location=labware11['A3'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette1.touch_tip(location=labware11['A3'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A3'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A7'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A7'].bottom(z=0.5))
    pipette1.move_to(location=labware11['A7'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette1.touch_tip(location=labware11['A7'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A7'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.drop_tip()
    pipette1.pick_up_tip()
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A4'].bottom(z=1))

# command no. 80
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A4'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A4'].bottom(z=1))
    pipette1.move_to(location=labware11['A4'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette1.touch_tip(location=labware11['A4'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A4'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A8'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 94
    pipette1.dispense(volume=20, location=labware11['A8'].bottom(z=0.5))
    pipette1.move_to(location=labware11['A8'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette1.touch_tip(location=labware11['A8'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=20, location=labware11['A8'].bottom(z=15.78))
    protocol.delay(seconds=1)
    pipette1.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=16, location=labware12['A1'].bottom(z=1))

# command no. 100
    pipette0.move_to(location=labware12['A1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware12['A1'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['A1'].bottom(z=118.5))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=1, location=labware9['D1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['D1'].bottom(z=0.5))
    pipette0.move_to(location=labware9['D1'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['D1'], v_offset=-1.0)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['C1'].bottom(z=0.5))
    pipette0.move_to(location=labware9['C1'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['C1'], v_offset=-1.0)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['B1'].bottom(z=0.5))
    pipette0.move_to(location=labware9['B1'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['B1'], v_offset=-1.0)
    pipette0.blow_out(location=labware12['A1'].bottom(z=117.5))

# command no. 120
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['A1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=16, location=labware12['A1'].bottom(z=1))
    pipette0.move_to(location=labware12['A1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware12['A1'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['A1'].bottom(z=118.5))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=1, location=labware9['A1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['A1'].bottom(z=0.5))
    pipette0.move_to(location=labware9['A1'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['A1'], v_offset=-1.0)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['D2'].bottom(z=0.5))
    pipette0.move_to(location=labware9['D2'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['D2'], v_offset=-1.0)

# command no. 140
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['C2'].bottom(z=0.5))
    pipette0.move_to(location=labware9['C2'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['C2'], v_offset=-1.0)
    pipette0.blow_out(location=labware12['A1'].bottom(z=117.5))
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['A1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=11, location=labware12['A1'].bottom(z=1))
    pipette0.move_to(location=labware12['A1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware12['A1'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['A1'].bottom(z=118.5))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=1, location=labware9['B2'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['B2'].bottom(z=0.5))
    pipette0.move_to(location=labware9['B2'].bottom(z=0.5))
    protocol.delay(seconds=1)

# command no. 160
    pipette0.touch_tip(location=labware9['B2'], v_offset=-1.0)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['A2'].bottom(z=0.5))
    pipette0.move_to(location=labware9['A2'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['A2'], v_offset=-1.0)
    pipette0.blow_out(location=labware12['A1'].bottom(z=117.5))
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['A1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['A1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware12['A1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['A1'].bottom(z=1))
    pipette0.move_to(location=labware12['A1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware12['A1'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['A1'].bottom(z=118.5))
    protocol.delay(seconds=1)

# command no. 180
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['B1'].bottom(z=1))
    pipette0.move_to(location=labware12['B1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware12['B1'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['B1'].bottom(z=118.5))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=12, location=labware9['A1'].bottom(z=0.5))
    pipette0.move_to(location=labware9['A1'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['A1'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware9['A1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['C1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware12['C1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['C1'].bottom(z=1))
    pipette0.move_to(location=labware12['C1'].bottom(z=1))

# command no. 200
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware12['C1'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['C1'].bottom(z=118.5))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=1, location=labware9['A1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['A1'].bottom(z=0.5))
    pipette0.move_to(location=labware9['A1'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['A1'], v_offset=-1.0)
    pipette0.blow_out(location=labware12['C1'].bottom(z=117.5))
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['C1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['C1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware12['C1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['C1'].bottom(z=1))

# command no. 220
    pipette0.move_to(location=labware12['C1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware12['C1'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['C1'].bottom(z=118.5))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=1, location=labware9['B1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['B1'].bottom(z=0.5))
    pipette0.move_to(location=labware9['B1'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['B1'], v_offset=-1.0)
    pipette0.blow_out(location=labware12['C1'].bottom(z=117.5))
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['C1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['C1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware12['C1'].bottom(z=1))
    protocol.delay(seconds=1)

# command no. 240
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['C1'].bottom(z=1))
    pipette0.move_to(location=labware12['C1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware12['C1'], v_offset=-1.0)
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['C1'].bottom(z=118.5))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=1, location=labware9['C1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['C1'].bottom(z=0.5))
    pipette0.move_to(location=labware9['C1'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['C1'], v_offset=-1.0)
    pipette0.blow_out(location=labware12['C1'].bottom(z=117.5))
    protocol.comment('Air gap')
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=1, location=labware12['C1'].bottom(z=40.28))
    protocol.delay(seconds=1)
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['C1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware12['C1'].bottom(z=1))

# command no. 260
    protocol.delay(seconds=1)
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['C1'].bottom(z=1))
    pipette0.move_to(location=labware12['C1'].bottom(z=1))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware12['C1'], v_offset=-1.0)
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['A1'].bottom(z=0.5))
    pipette0.move_to(location=labware9['A1'].bottom(z=0.5))
    protocol.delay(seconds=1)
    pipette0.touch_tip(location=labware9['A1'], v_offset=-1.0)
    pipette0.blow_out(location=protocol.fixed_trash['A1'].bottom(z=0))
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=5, location=labware12['C1'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=5, location=labware9['A1'].bottom(z=33.5))
    pipette0.blow_out(location=labware9['A1'].bottom(z=39.28))
    pipette0.drop_tip()
    module2.close_labware_latch()
    module2.deactivate_heater()
    pipette1.pick_up_tip()
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=300, location=labware10['A1'].bottom(z=2))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 30
    pipette1.dispense(volume=300, location=labware10['A1'].bottom(z=2))

# command no. 280
    protocol.delay(seconds=1)
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=300, location=labware10['A1'].bottom(z=2))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 30
    pipette1.dispense(volume=300, location=labware10['A1'].bottom(z=2))
    protocol.delay(seconds=1)
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=300, location=labware10['A1'].bottom(z=2))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 30
    pipette1.dispense(volume=300, location=labware10['A1'].bottom(z=2))
    protocol.delay(seconds=1)
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=300, location=labware10['A1'].bottom(z=2))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 30
    pipette1.dispense(volume=300, location=labware10['A1'].bottom(z=2))
    protocol.delay(seconds=1)
    pipette1.flow_rate.aspirate = 94
    pipette1.aspirate(volume=300, location=labware10['A1'].bottom(z=2))
    protocol.delay(seconds=1)
    pipette1.flow_rate.dispense = 30
    pipette1.dispense(volume=300, location=labware10['A1'].bottom(z=2))
    protocol.delay(seconds=1)
    pipette1.blow_out(location=protocol.fixed_trash['A1'].bottom(z=0))
    pipette1.touch_tip(location=labware10['A1'], v_offset=-1)
    pipette1.drop_tip()

# command no. 300
    send_to_slack(webhook_url,"Your OT-2 has said: Pause until told to resume")
    protocol.pause(msg='Pause until told to resume')
    protocol.delay(seconds=3723, msg='Delay of 1:2:3')
    module4.start_set_temperature(celsius=37) # Hidden API
    module2.close_labware_latch()
    module2.set_target_temperature(42)
    module2.set_and_wait_for_shake_speed(300)
    protocol.delay(seconds=600)
    module2.deactivate_shaker()
    module2.deactivate_heater()
    while (module4.temperature != 37 and not protocol.is_simulating()):
        protocol.delay(seconds=1)
    module3.engage(height_from_base=6)
    module3.disengage()
    module4.deactivate()
    module5.open_lid()
    module5.close_lid()
    module5.set_block_temperature(temperature=70)
    module5.set_lid_temperature(temperature=110)
    module5.open_lid()

# command no. 320
    module5.deactivate_block()
    module5.deactivate_lid()
    module5.close_lid()
    module5.set_lid_temperature(temperature=110)
    module5.execute_profile(steps=[{'temperature': 95, 'hold_time_seconds': 10}, {'temperature': 72, 'hold_time_seconds': 75}, {'temperature': 95, 'hold_time_seconds': 10}, {'temperature': 72, 'hold_time_seconds': 75}, {'temperature': 95, 'hold_time_seconds': 10}, {'temperature': 72, 'hold_time_seconds': 75}, {'temperature': 95, 'hold_time_seconds': 10}, {'temperature': 72, 'hold_time_seconds': 75}, {'temperature': 95, 'hold_time_seconds': 10}, {'temperature': 72, 'hold_time_seconds': 75}, {'temperature': 95, 'hold_time_seconds': 10}, {'temperature': 72, 'hold_time_seconds': 75}, {'temperature': 95, 'hold_time_seconds': 10}, {'temperature': 72, 'hold_time_seconds': 75}, {'temperature': 95, 'hold_time_seconds': 10}, {'temperature': 72, 'hold_time_seconds': 75}, {'temperature': 95, 'hold_time_seconds': 10}, {'temperature': 72, 'hold_time_seconds': 75}, {'temperature': 95, 'hold_time_seconds': 10}, {'temperature': 72, 'hold_time_seconds': 75}, {'temperature': 95, 'hold_time_seconds': 10}],repetitions=1,block_max_volume=50)
    module5.set_block_temperature(temperature=10)
    module5.deactivate_lid()
    module4.set_temperature(celsius=4)
    while (module4.temperature != 4 and not protocol.is_simulating()):
        protocol.delay(seconds=1)
    module2.close_labware_latch()
    module2.deactivate_heater()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['A1'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['H3'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['B1'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['F3'].bottom(z=0.5))

# command no. 340
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['C1'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['H4'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['D1'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['F4'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['E1'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['C4'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['F1'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['A4'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['G1'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['C5'].bottom(z=0.5))

# command no. 360
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['H1'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['G6'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['A2'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['F8'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['B2'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['E8'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['C2'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['H10'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['D2'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['C10'].bottom(z=0.5))

# command no. 380
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['E2'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['A10'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['F2'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['H12'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['G2'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['F12'].bottom(z=0.5))
    pipette0.drop_tip()
    pipette0.pick_up_tip()
    pipette0.flow_rate.aspirate = 3.78
    pipette0.aspirate(volume=20, location=labware10['H2'].bottom(z=1))
    pipette0.flow_rate.dispense = 3.78
    pipette0.dispense(volume=20, location=labware10['A12'].bottom(z=0.5))
    pipette0.drop_tip()
    protocol.delay(seconds=10, msg='')
    module4.start_set_temperature(celsius=15) # Hidden API
    module2.close_labware_latch()

# command no. 400
    module2.set_target_temperature(50)
    module2.set_and_wait_for_shake_speed(500)
    while (module4.temperature != 15 and not protocol.is_simulating()):
        protocol.delay(seconds=1)
    module5.open_lid()
    module5.set_lid_temperature(temperature=50)
    module5.set_block_temperature(temperature=20)
    send_to_slack(webhook_url,"Your OT-2 protocol has just completed!")

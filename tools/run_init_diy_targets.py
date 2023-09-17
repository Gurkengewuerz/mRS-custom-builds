#!/usr/bin/env python

import os
import glob
import json
import sys
from redbaron import RedBaron

mLRSProjectdirectory = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
mLRSdirectory = os.path.join(mLRSProjectdirectory, "mLRS")
makeFirmwareScript = os.path.join(mLRSProjectdirectory, "tools", "run_make_firmwares3.py")
copySTDriversScript = os.path.join(mLRSProjectdirectory, "tools", "run_copy_st_drivers.py")
commonHALDirectory = os.path.join(mLRSdirectory, "Common", "hal")
commonHALDeviceConf = os.path.join(commonHALDirectory, "device_conf.h")
commonHAL = os.path.join(commonHALDirectory, "hal.h")

newTLIST = []
newUSBDriver = []

print("Parsing defines.json")
for define in glob.glob(os.path.join(mLRSdirectory, "**", "defines.json"), recursive=True):
    with open(define, encoding="utf-8") as define_file:
        parsed_json = json.load(define_file)
        target = os.path.basename(os.path.dirname(define))
        
        useUSB = os.path.join(os.path.dirname(define), '.usb')
        if os.path.isfile(useUSB):
            print("Target", target, "requires usb")
            newUSBDriver.append(target)

        print("Parsing", target)

        for index, definition in enumerate(parsed_json):
            targetD = target.upper().replace("-", "_") + "_DEF" + str(index)
            print("Definition", definition["name"])

            make = {"target": target, "target_D": targetD, "extra_D_list": definition["make"]["extra_D_list"], "appendix": definition["make"]["appendix"]}
            if "package" in definition["make"]:
                make["package"] = definition["make"]["package"]
            newTLIST.append(make)
            print(newTLIST[len(newTLIST) - 1])

            with open(commonHALDeviceConf, "r+", encoding="utf-8") as commonHALDeviceConf_file:
                commonHALDeviceConf_content = commonHALDeviceConf_file.read()

                idx = commonHALDeviceConf_content.index("#endif")
                halDef = ''.join(['  #define ' + x + '\r\n' for x in definition['deviceConf']])
                commonHALDeviceConf_content = commonHALDeviceConf_content[:idx] + "\r\n" + f"#endif\r\n#ifdef {targetD}\r\n  #define DEVICE_NAME \"{definition['name']}\"\r\n  #define {'DEVICE_IS_TRANSMITTER' if 'tx-' in definition['hal'] else 'DEVICE_IS_RECEIVER'}\r\n{halDef}" + "\r\n" + commonHALDeviceConf_content[idx:]
                
                print("Wrote", commonHALDeviceConf)
                commonHALDeviceConf_file.seek(0)
                commonHALDeviceConf_file.write(commonHALDeviceConf_content)
                commonHALDeviceConf_file.truncate()

            with open(commonHAL, "r+", encoding="utf-8") as commonHAL_file:
                commonHAL_content = commonHAL_file.read()

                idx = commonHAL_content.index("#endif")
                commonHAL_content = commonHAL_content[:idx] + "\r\n" + f"#endif\r\n#ifdef {targetD}\r\n  #include \"{definition['hal']}.h\"" + "\r\n" + commonHAL_content[idx:]

                print("Wrote", commonHAL)
                commonHAL_file.seek(0)
                commonHAL_file.write(commonHAL_content)
                commonHAL_file.truncate()


print("Write new build targets")
with open(makeFirmwareScript, "r+", encoding="utf-8") as makemakeFirmwareScript_file:
    makemakeFirmwareScript_content = makemakeFirmwareScript_file.read()

    red = RedBaron(makemakeFirmwareScript_content)
    
    for assignment in red.find_all('assignment'):
        if assignment.target.value == 'TLIST':
            assignment.value = "{}".format(newTLIST)
            print("New value for TLIST", assignment.value.dumps())

    modified_code = red.dumps()
    print("Wrote", makeFirmwareScript)
    makemakeFirmwareScript_file.seek(0)
    makemakeFirmwareScript_file.write(modified_code)
    makemakeFirmwareScript_file.truncate()


with open(copySTDriversScript, "r+", encoding="utf-8") as copySTDriversScript_file:
    copySTDriversScript_content = copySTDriversScript_file.read()

    red = RedBaron(copySTDriversScript_content)

    for assignment in red.find_all('assignment'):
        if assignment.target.value == 'targets_with_usb_to_include':
            targets_list = assignment.value
            if targets_list.type == 'list':
                new_target_nodes = [RedBaron(f"'{target}'") for target in newUSBDriver]
                targets_list.extend(new_target_nodes)
                print("New value for targets_with_usb_to_include", targets_list.dumps())
            else:
                print("targets_with_usb_to_include is not a list. Is this script up to date?")
                sys.exit(1)
    
    modified_code = red.dumps()
    print("Wrote", copySTDriversScript)
    copySTDriversScript_file.seek(0)
    copySTDriversScript_file.write(modified_code)
    copySTDriversScript_file.truncate()

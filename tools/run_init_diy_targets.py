#!/usr/bin/env python

import os
import glob
import json
import ast
import sys

mLRSProjectdirectory = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
mLRSdirectory = os.path.join(mLRSProjectdirectory, "mLRS")
makeFirmwareScript = os.path.join(mLRSProjectdirectory, "tools", "run_make_firmwares3.py")
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
        halDefines = target.replace("tx-", "tx-hal-").replace("rx-", "rx-hal-") + ".h"
        
        useUSB = os.path.join(os.path.dirname(define), '.usb')
        if os.path.isfile(useUSB):
            print("Target", target, "requires usb")
            newUSBDriver.append(target)

        print("Parsing", target)

        for index, definition in enumerate(parsed_json):
            targetD = target.upper().replace("-", "_") + "_DEF" + str(index)
            print("Definition", definition["name"])

            newTLIST.append({"target": target, "target_D": targetD, "extra_D_list": definition["make"]["extra_D_list"], "appendix": definition["make"]["appendix"]})
            print(newTLIST[len(newTLIST) - 1])

            with open(commonHALDeviceConf, "r+", encoding="utf-8") as commonHALDeviceConf_file:
                commonHALDeviceConf_content = commonHALDeviceConf_file.read()

                idx = commonHALDeviceConf_content.index("#endif")
                halDef = ''.join(['  #define ' + x + '\r\n' for x in definition['deviceConf']])
                commonHALDeviceConf_content = commonHALDeviceConf_content[:idx] + "\r\n" + f"#endif\r\n#ifdef {targetD}\r\n  #define DEVICE_NAME \"{definition['name']}\"\r\n  #define {'DEVICE_IS_TRANSMITTER' if 'tx-' in target else 'DEVICE_IS_RECEIVER'}\r\n{halDef}" + "\r\n" + commonHALDeviceConf_content[idx:]
                
                print("Wrote", commonHALDeviceConf)
                commonHALDeviceConf_file.seek(0)
                commonHALDeviceConf_file.write(commonHALDeviceConf_content)
                commonHALDeviceConf_file.truncate()

            with open(commonHAL, "r+", encoding="utf-8") as commonHAL_file:
                commonHAL_content = commonHAL_file.read()

                idx = commonHAL_content.index("#endif")
                commonHAL_content = commonHAL_content[:idx] + "\r\n" + f"#endif\r\n#ifdef {targetD}\r\n  #include \"{halDefines}\"" + "\r\n" + commonHAL_content[idx:]

                print("Wrote", commonHAL)
                commonHAL_file.seek(0)
                commonHAL_file.write(commonHAL_content)
                commonHAL_file.truncate()


print("Write new build targets")
with open(makeFirmwareScript, "r+", encoding="utf-8") as makemakeFirmwareScript_file:
    makemakeFirmwareScript_content = makemakeFirmwareScript_file.read()

    # Parse the script content into an abstract syntax tree (AST)
    tree = ast.parse(makemakeFirmwareScript_content)

    # Find the assignment statement for TLIST
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'TLIST':
                    node.value = ast.List(elts=[ast.Dict(keys=[ast.Str(k) for k in item.keys()], values=[ast.Str(v) for v in item.values()]) for item in newTLIST])
                    print("New value for TLIST", ast.dump(node.value))
                elif isinstance(target, ast.Name) and target.id == 'targets_with_usb_to_include':
                    # Update the value of 'targets_with_usb_to_include' by merging with newUSBDriver
                    if isinstance(node.value, ast.List):
                        node.value.elts.extend([ast.Str(target) for target in newUSBDriver])
                        print("New value for usb to include", ast.dump(node.value))
                    else:
                        print("targets_with_usb_to_include is not a list. Is this script up to date?")
                        sys.exit(1)

    modified_code = ast.unparse(tree)
    print("Wrote", makeFirmwareScript)
    makemakeFirmwareScript_file.seek(0)
    makemakeFirmwareScript_file.write(modified_code)
    makemakeFirmwareScript_file.truncate()

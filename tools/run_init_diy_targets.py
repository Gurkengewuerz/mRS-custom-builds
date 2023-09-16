#!/usr/bin/env python

import os
import glob
import json
import re
import ast

mLRSProjectdirectory = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
mLRSdirectory = os.path.join(mLRSProjectdirectory, "mLRS")
makeFirmwareScript = os.path.join(mLRSProjectdirectory, "tools", "run_make_firmwares3.py")
commonHALDirectory = os.path.join(mLRSdirectory, "Common", "hal")
commonHALDeviceConf = os.path.join(commonHALDirectory, "device_conf.h")
commonHAL = os.path.join(commonHALDirectory, "hal.h")

newTLIST = []

print("Parsing defines.json")
for define in glob.glob(os.path.join(mLRSdirectory, "**", "defines.json"), recursive=True):
    with open(define, encoding="utf-8") as define_file:
        parsed_json = json.load(define_file)
        halDefines = str(parsed_json["target"]).replace("tx-", "tx-hal-").replace("rx-", "rx-hal-") + ".h"
        print("Parsing",parsed_json["name"])

        newTLIST.append({"target": parsed_json["target"], "target_D": parsed_json["target_D"], "extra_D_list": parsed_json["make"]["extra_D_list"], "appendix": parsed_json["make"]["appendix"]})
        print(newTLIST[len(newTLIST) - 1])

        with open(commonHALDeviceConf, "r+", encoding="utf-8") as commonHALDeviceConf_file:
            commonHALDeviceConf_content = commonHALDeviceConf_file.read()

            idx = commonHALDeviceConf_content.index("#endif")
            halDef = ''.join(['  #define ' + x + '\r\n' for x in parsed_json['deviceConf']])
            commonHALDeviceConf_content = commonHALDeviceConf_content[:idx] + "\r\n" + f"#endif\r\n#ifdef {parsed_json['target_D']}\r\n  #define DEVICE_NAME \"{parsed_json['name']}\"\r\n  #define {'DEVICE_IS_RECEIVER' if 'tx-' in parsed_json['target'] else 'DEVICE_IS_RECEIVER'}\r\n{halDef}" + "\r\n" + commonHALDeviceConf_content[idx:]
            
            print("Wrote", commonHALDeviceConf)
            commonHALDeviceConf_file.write(commonHALDeviceConf_content)

        with open(commonHAL, "r+", encoding="utf-8") as commonHAL_file:
            commonHAL_content = commonHAL_file.read()

            idx = commonHAL_content.index("#endif")
            commonHAL_content = commonHAL_content[:idx] + "\r\n" + f"#endif\r\n#ifdef {parsed_json['target_D']}\r\n  #include {halDefines}" + "\r\n" + commonHAL_content[idx:]

            print("Wrote", commonHAL)
            commonHAL_file.write(commonHAL_content)

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
                    print("New value", ast.dump(node.value))
    
    modified_code = ast.unparse(tree)
    print("Wrote", makeFirmwareScript)
    makemakeFirmwareScript_file.write(modified_code)

#!/usr/bin/env python

import os
import glob
import hjson
import sys
import shutil
from redbaron import RedBaron

mLRSProjectdirectory = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
mLRSdirectory = os.path.join(mLRSProjectdirectory, "mLRS")
makeFirmwareScript = os.path.join(mLRSProjectdirectory, "tools", "run_make_firmwares.py")
copySTDriversScript = os.path.join(mLRSProjectdirectory, "tools", "run_copy_st_drivers.py")
commonHALDirectory = os.path.join(mLRSdirectory, "Common", "hal")
commonHALDeviceConf = os.path.join(commonHALDirectory, "device_conf.h")
commonHAL = os.path.join(commonHALDirectory, "hal.h")

newTLIST = []

print("Parsing defines.json")
for define in glob.glob(os.path.join(mLRSdirectory, "**", "defines.hjson"), recursive=True):
    with open(define, encoding="utf-8") as define_file:
        parsed_json = hjson.load(define_file)
        target_name = os.path.basename(os.path.dirname(define))
        
        useUSB = os.path.join(os.path.dirname(define), '.usb')

        print("Parsing", target_name)

        for index, definition in enumerate(parsed_json):
            for hal in definition['hal']:
                is_tx = 'tx-' in hal.lower()
                target = (('tx' if is_tx else 'rx') + "-" + "def" + str(index) + "-" + target_name).lower()
                targetD = target.upper().replace("-", "_")
                
                target_path = os.path.join(mLRSdirectory, target)
                if os.path.exists(target_path):
                    print("Failed to create symlink for target", target, "with definition", targetD)
                    sys.exit(1)
                shutil.copytree(os.path.dirname(define), target_path)
                
                print("Definition", definition["name"], "sym target is", target, "with path", target_path)

                make = {"target": target, "target_D": targetD, "extra_D_list": definition["make"]["extra_D_list"], "appendix": definition["make"]["appendix"]}
                if "package" in definition["make"]:
                    make["package"] = definition["make"]["package"]
                newTLIST.append(make)
                print(newTLIST[len(newTLIST) - 1])

                with open(commonHALDeviceConf, "r+", encoding="utf-8") as commonHALDeviceConf_file:
                    commonHALDeviceConf_content = commonHALDeviceConf_file.read()

                    idx = commonHALDeviceConf_content.index("#endif")
                    halDef = ''.join(['  #define ' + x + '\r\n' for x in definition['deviceConf']])
                    commonHALDeviceConf_content = commonHALDeviceConf_content[:idx] + "\r\n" + f"#endif\r\n#ifdef {targetD}\r\n  #define DEVICE_NAME \"{definition['name']}\"\r\n  #define {'DEVICE_IS_TRANSMITTER' if is_tx else 'DEVICE_IS_RECEIVER'}\r\n{halDef}" + "\r\n" + commonHALDeviceConf_content[idx:]
                    
                    print("Wrote", commonHALDeviceConf)
                    commonHALDeviceConf_file.seek(0)
                    commonHALDeviceConf_file.write(commonHALDeviceConf_content)
                    commonHALDeviceConf_file.truncate()

                with open(commonHAL, "r+", encoding="utf-8") as commonHAL_file:
                    commonHAL_content = commonHAL_file.read()

                    idx = commonHAL_content.index("#endif")
                    commonHAL_content = commonHAL_content[:idx] + "\r\n" + f"#endif\r\n#ifdef {targetD}\r\n  #include \"{hal}.h\"" + "\r\n" + commonHAL_content[idx:]

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

print("*******************************************")
print("Init complete with", len(newTLIST), "targets")
print("*******************************************")
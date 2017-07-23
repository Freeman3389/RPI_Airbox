"""This script will execute all the python script enabled of RPi_Airbox."""
# !/usr/bin/python -u
# -*- coding:Utf-8 -*-
# License: GPL 2.0
# Copyright 2017-2018 - Freeman Lee <freeman.lee@quantatw.com>
# Version 0.1.0 @ 2017.07.19

# Get settings from '../settings.json'
import sys, json, syslog, os, time, subprocess, psutil, pdb
syslog.openlog(sys.argv[0], syslog.LOG_PID)
with open('settings.json') as json_handle:
    configs = json.load(json_handle)
account = configs['global']['account']
message_disabled = []
message_noattr = []
message_running = []
message_load = []
w = 0
x = 0
y = 0
z = 0


def index_containing_substring(the_list, substring):
    """Get index number of list where subtring contained."""
    for i, s in enumerate(the_list):
        if substring in s:
            return i
    return -1

def get_enabled_attrs(dictionary, sensor):
    """Get specific attribute if the sensor is enabled."""
    if dictionary.get(sensor).get('status') == '1':
        return (dictionary.get(sensor).get('sensor_name', None), dictionary.get(sensor).get('executable_path', None))
    else:
        return None

def check_process_running(cmd_path, cmd_str, model):
    """Check if specific python script is running"""
    running_process_str = []
    for pid in psutil.pids():
        p = psutil.Process(pid)
        if len(p.cmdline()) > 1 and 'python' in p.cmdline():
            index = index_containing_substring(p.cmdline(), 'python')
            for proc_str in p.cmdline()[index + 1:len(p.cmdline())]:
                running_process_str.append(proc_str)
    if cmd_path in running_process_str:
        y += 1
        message_running.append(model)
    else:
        z += 1
        message_load.append(model)
        subprocess.call(cmd_str, shell=True)
    time.sleep(0.1)

def main():
    try:
        syslog.syslog(syslog.LOG_INFO, 'Begin to check RPi_Airbox enabled scripts.')
        for model in configs.keys():
            if model != 'global':
                enabled_attrs = get_enabled_attrs(configs, model)
                
                if enabled_attrs is None:
                    w += 1
                    message_disabled.append(model)
                elif not all(enabled_attrs):
                    x += 1
                    message_noattr.append(model)
                else:
                    cmd_path = str(configs['global']['base_path']) + str(configs[model]['executable_path'])
                    cmd_str = str('/usr/bin/python ' + cmd_path + ' &')
                    check_process_running(cmd_path, cmd_str, model)
        message_str = 'Loader summary: Loading - ' + str(z) + ' ; Running - ' + str(y) + ' ; Disabled - ' + str(w) + ' ; No Attr - ' + str(x) + '\nLoading Model - ' + (','.join(message_load)) + '\nRunning Model - ' + (','.join(message_running)) + '\nDisabled Model - ' + (','.join(message_disabled)) + '\nNo Attribute Model - ' + (','.join(message_noattr))
        syslog.syslog(syslog.LOG_INFO, 'Finished checking RPi_Aribox scripts\n'+ message_str)
        print syslog.LOG_INFO, 'Finished checking RPi_Aribox scripts\n'+ message_str
    except BaseException:
        pass

if __name__ == "__main__":
    start_time = time.time()
    main()
    print os.path.basename(__file__) + 'execution time = ' + str(time.time() - start_time)
    syslog.syslog(syslog.LOG_INFO, os.path.basename(__file__) + 'execution time = ' + str(time.time() - start_time))

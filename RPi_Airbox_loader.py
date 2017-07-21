"""This script will execute all the python script enabled of RPi_Airbox."""
# !/usr/bin/python -u
# -*- coding:Utf-8 -*-
# License: GPL 2.0
# Copyright 2017-2018 - Freeman Lee <freeman.lee@quantatw.com>
# Version 0.1.0 @ 2017.07.19

# Get settings from '../settings.json'
import sys, json, syslog, os, time, subprocess, psutil, pdb
syslog.openlog(sys.argv[0], syslog.LOG_PID)
with open('/opt/RPi_Airbox/settings.json') as json_handle:
    configs = json.load(json_handle)
account = configs['global']['account']
message_str=[]

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

def check_process_running(cmd_path, cmd_str):
    """Check if specific python script is running"""
    running_process_str = []
    for pid in psutil.pids():
        p = psutil.Process(pid)
        if len(p.cmdline()) > 1 and 'python' in p.cmdline():
            index = index_containing_substring(p.cmdline(), 'python')
            for proc_str in p.cmdline()[index + 1:len(p.cmdline())]:
                running_process_str.append(proc_str)
    if cmd_path in running_process_str:
        message_str.append(cmd_path + 'is running.')
    else:
        message_str.append(cmd_path + ' is not running, and try to start it up.')
        subprocess.call(cmd_str, shell=True)
    time.sleep(0.1)

def main():
    try:
        for model in configs.keys():
            print model
            if model != 'global':
                enabled_attrs = get_enabled_attrs(configs, model)
            if enabled_attrs is None:
                message_str.append(model + ' is not enabled, skip to load it.')
            elif not all(enabled_attrs):
                message_str.append('some attribute of ' + model + 'is Null.')
            else:
                cmd_path = str(configs['global']['base_path']) + str(configs[model]['executable_path'])
                cmd_str = str('/usr/bin/python ' + cmd_path + ' &')
                check_process_running(cmd_path, cmd_str)
        print "/n".join(message_str)
    except BaseException:
        pass

if __name__ == "__main__":
    main()

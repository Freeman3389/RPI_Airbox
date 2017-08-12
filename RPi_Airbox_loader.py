"""This script will execute all the python script enabled of RPi_Airbox."""
# !/usr/bin/python
# -*- coding:Utf-8 -*-
# License: GPL 2.0
# Copyright 2017-2018 - Freeman Lee <freeman.lee@quantatw.com>
# Version 0.1.0 @ 2017.07.19

# Get settings from '../settings.json'
import sys, json, syslog, os, time, subprocess, psutil, pdb
with open(os.path.dirname(os.path.abspath(__file__)) + '/settings.json') as json_handle:
    configs = json.load(json_handle)

def check_proc_running(module, pid_file):
    """check if enabled module running"""
    global configs
    global y
    global z
    global message_running
    global message_load
    cmd_account = str(configs['global']['account'])
    cmd_path = str(configs['global']['base_path']) + str(configs[module]['executable_path'])
    cmd_str = str('/usr/bin/sudo -u ' + cmd_account + ' /usr/bin/python ' + cmd_path + ' &')
    if os.path.isfile(pid_file):
        with open(pid_file) as f_pid:
            pid = int(f_pid.read().replace('\n', ''))
        if psutil.pid_exists(pid):
            message_running.append(module + '(PID=' + str(pid) + ')')
            y += 1
        else:
            subprocess.call(cmd_str, shell=True)
            message_load.append(module)
            z += 1
    else:
        subprocess.call(cmd_str, shell=True)
        message_load.append(module)
        z += 1


def main():
    """Execute main function"""
    retry_count = 0
        syslog.openlog(sys.argv[0], syslog.LOG_PID)
        enabled_module_list = []
        disabled_module_list = []
        global configs
        global message_running
        global message_load
        message_running = []
        message_load = []
        global y
        global z
        w = 0
        x = 0
        y = 0
        z = 0

        try:
            syslog.syslog(syslog.LOG_INFO, 'Begin to check RPi_Airbox enabled scripts.')
            for module in configs['global']['loading_order']:
                if int(configs.get(module).get('status')) == 1:
                    pid_file = str(configs['global']['base_path']) + str(configs[module]['sensor_name']) + '.pid'
                    w += 1
                    enabled_module_list.append(module)
                    check_proc_running(module, pid_file)
                    time.sleep(5)
                else:
                    x += 1
                    disabled_module_list.append(module)
                    time.sleep(5)
            message_str = 'Loader summary: Enabled - ' + str(w) + ' ; Disabled - ' + str(x) + ' ; Running - ' + str(y) + ' ; Loading - ' + str(z) + '\nEnabled Modules - ' + (', '.join(enabled_module_list)) + '\nDisabled Modules - ' + (', '.join(disabled_module_list)) + '\nRunning Modules - ' + (', '.join(message_running)) + '\nLoading Modules - ' + (', '.join(message_load))
            syslog.syslog(syslog.LOG_INFO, 'Finished checking RPi_Aribox scripts\n'+ message_str)
            print 'Finished checking RPi_Aribox scripts\n' + message_str
            time.sleep(1)

        except IOError as (errno, strerror):
            print "I/O error({0}): {1}".format(errno, strerror)
            syslog.syslog(syslog.LOG_INFO, "I/O error({0}): {1}".format(errno, strerror))
            retry_count += 1
            time.sleep(60)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            time.sleep(60)
            retry_count += 1
            raise
        break


if __name__ == "__main__":
    start_time = time.time()
    main()
    print os.path.basename(__file__) + ' execution time = ' + '{:10.4f}'.format(time.time() - start_time)  + ' Secs'
    syslog.syslog(syslog.LOG_INFO, os.path.basename(__file__) + ' execution time = ' + '{:10.4f}'.format(time.time() - start_time) + 'Secs')

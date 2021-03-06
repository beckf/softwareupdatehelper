import os
import plistlib
import datetime
import logging
import sys
import getopt
import random
import subprocess
import shlex
import shutil

plist = "/Library/Application Support/JAMF/org.da.softwareupdatehelper.plist"
current_datetime = datetime.datetime.now()
logdir = "/Library/Logs/softwareupdatehelper/"
logfile = logdir + str(current_datetime) + ".log"
reserves_location = "/usr/local/share/SUH/"
reserves_disk_image = "SUH"
# set default days in case we don't get any sent
delay_days = 14
icon = "/Library/Application\ Support/JAMF/bin/jamfHelper.app/Contents/Resources/Message.png"

__version__ = "3.7.1"


def log(data):
    """
    Logs data to the log file and prints to stdout
    :param data:
    :return:
    """
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    logging.basicConfig(filename=logfile, level=logging.DEBUG)
    logging.debug(data)
    print(data)


def save_plist(path, d):
    """
    Saves plist
    :param path:
    :param d:
    :return:
    """
    try:
        with open(plist, "wb") as file:
            return plistlib.dump(d, file)
    except:
        return False


def random_date(start, end):
    """
    Return a random datetime between two datetime
    objects.
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + datetime.timedelta(seconds=random_second)


def read_plist(path):
    """
    Read plist
    :param path:
    :return:
    """
    try:
        with open(plist, "rb") as file:
            return plistlib.load(file)
    except:
        return False


def create_reserves():
    """
    Creates the reserves if space is available.
    :return: True(Success)/False(Fail)
    """
    if sys.version_info[0] == 3:
        root_disk_space = shutil.disk_usage('/')
        root_disk_space_in_gigs = int(root_disk_space.free / 1024 / 1024 / 1024)
    else:
        root_disk_space = os.statvfs("/")
        root_disk_space_in_gigs = (root_disk_space.f_bavail * root_disk_space.f_frsize) / 1024 / 1024 / 1024

    if root_disk_space_in_gigs > 7:
        if not os.path.exists(reserves_location):
            os.makedirs(reserves_location)
        file = reserves_location + "/" + reserves_disk_image + ".dmg"
        if not os.path.isfile(file):
            create_cmd = shlex.split('/usr/bin/hdiutil create -size 10g -fs HFS+ -volname ' +
                                     reserves_disk_image +
                                     ' ' +
                                     file)
            create = subprocess.check_output(create_cmd)

            if create:
                return True
            else:
                return False
    else:
        return False


def remove_reserves():
    """
    Removes the reserves to make room for updates.
    :return:
    """
    file = reserves_location + "/" + reserves_disk_image + ".dmg"
    if os.path.isfile(file):
        os.remove(file)
        if not os.path.isfile(file):
            return True
        else:
            return False
    else:
        return True


def run_update():
    """
    Run the update
    :return:
    """
    log("Running scheduled update")
    update_check = os.popen("softwareupdate -l").read()
    if "*" in update_check:
        log("New Updates Available.")
        log(update_check)

        try:
            cmd = shlex.split('/Library/Application\ Support/JAMF/bin/jamfHelper.app/Contents/MacOS/jamfHelper'
                              ' -windowType hud '
                              '-title "Software Update Helper" '
                              '-heading "Installing Software Update" '
                              '-windowPosition lr '
                              '-button1 "OK" '
                              '-defaultButton 1 '
                              '-timeout 30 '
                              '-icon ' + icon + " "
                              '-description "Updates will now be installed in silently in the background." ')
            # Get user decision, although we do not care.
            user_decision = subprocess.check_output(cmd)
        except:
            log("Exception in run_update notification.")

        if "restart" in update_check:
            restart = True
        else:
            restart = False

        remove_reserves()
        update_result = os.popen("softwareupdate -ai").read()
        log(update_result)

        if restart is True:
            log("Restart requested")
            cmd = shlex.split('/Library/Application\ Support/JAMF/bin/jamfHelper.app/Contents/MacOS/jamfHelper'
                  ' -windowType hud '
                  '-title "Software Update Helper" '
                  '-heading "Restart Required" '
                  '-button1 "Restart" '
                  '-defaultButton 1 '
                  '-icon ' + icon + " "
                  '-description "Software updates have been installed. You must restart to finish installing updates. '
                                    'DO NOT power off or sleep the computer. Doing so can result in data loss." ')
            # Get user decision, although we do not care.
            user_decision = subprocess.check_output(cmd)
            os.popen("sudo shutdown -h now").read()
        else:
            try:
                cmd = shlex.split('/Library/Application\ Support/JAMF/bin/jamfHelper.app/Contents/MacOS/jamfHelper'
                                  ' -windowType hud '
                                  '-title "Software Update Helper" '
                                  '-heading "Installing Software Update" '
                                  '-windowPosition lr '
                                  '-button1 "OK" '
                                  '-defaultButton 1 '
                                  '-timeout 30 '
                                  '-icon ' + icon + " "
                                  '-description "Updates have been installed.  A restart will not be required." ')
                # Get user decision, although we do not care.
                user_decision = subprocess.check_output(cmd)
            except:
                log("Exception to run_update notification.")

    plist_data = {"last_run": current_datetime}
    save_plist(plist, plist_data)


def nag():
        plist_data = read_plist(plist)
        if "scheduled_install" in plist_data.keys():
            log("Update scheduled for " + str(plist_data["scheduled_install"]))
            log("Triggering nag")

            if "pending_updates" in plist_data.keys():
                updates = plist_data["pending_updates"]
            else:
                updates = ""

            try:
                cmd = shlex.split('/Library/Application\ Support/JAMF/bin/jamfHelper.app/Contents/MacOS/jamfHelper'
                                  ' -windowType hud '
                                  '-title "Software Update Helper" '
                                  '-heading "New Software Updates" '
                                  '-windowPosition lr '
                                  '-button1 "Delay Updates" '
                                  '-button2 "Update Now" '
                                  '-defaultButton 1 '
                                  '-timeout 30 '
                                  '-icon ' + icon + " "
                                  '-description "Software Updates have been scheduled for ' +
                                  str(plist_data['scheduled_install']) +
                                  '. Updates include:\n\n' +
                                  '\n'.join(updates) +
                                  '"')

                user_decision = subprocess.check_output(cmd)
                log("User delayed update.")
            except subprocess.CalledProcessError as error:
                if error.returncode == 2:
                    run_update()
        else:
            print("Nothing to do")


def check_updates(delay):
    log("Looking for new updates")

    try:
        create_reserves()
    except:
        log("Unable to reserve space")

    update_check = os.popen("softwareupdate -l").read()
    if "*" in update_check:
        log("New Updates Available.")
        log(update_check)

        plist_data = read_plist(plist)
        if "scheduled_install" in plist_data.keys():
            log("Update already scheduled for " + str(plist_data["scheduled_install"]))
            if "pending_updates" in plist_data.keys():
                updates = plist_data["pending_updates"]
        else:
            updates = []
            for line in update_check.split('\n'):
                if '*' in line:
                    updates.append(line.lstrip(" *").rstrip(" -"))
            plist_data.update({"pending_updates": updates})
            scheduled_install = datetime.datetime.now() + datetime.timedelta(days=int(delay))
            plist_data.update({"scheduled_install": scheduled_install})
            save_plist(plist, plist_data)

        try:
            cmd = shlex.split('/Library/Application\ Support/JAMF/bin/jamfHelper.app/Contents/MacOS/jamfHelper'
                              ' -windowType hud '
                              '-title "Software Update Helper" '
                              '-heading "New Software Updates" '
                              '-windowPosition lr '
                              '-button1 "Delay Updates" '
                              '-button2 "Update Now" '
                              '-defaultButton 1 '
                              '-timeout 30 '
                              '-icon ' + icon + " "
                              '-description "Software Updates have been scheduled for ' +
                              str(plist_data['scheduled_install']) +
                              '. Updates include:\n\n' +
                              '\n'.join(updates) +
                              '"')

            user_decision = subprocess.check_output(cmd)
            log("User delayed update.")
        except subprocess.CalledProcessError as error:
            if error.returncode == 2:
                run_update()


def run_schedule():
    plist_data = read_plist(plist)
    if "scheduled_install" in plist_data.keys():
        if datetime.datetime.now() > plist_data['scheduled_install']:
            log("Begin scheduled install for " + str(plist_data['scheduled_install']))
            try:
                cmd = shlex.split('/Library/Application\ Support/JAMF/bin/jamfHelper.app/Contents/MacOS/jamfHelper '
                  '-windowType hud '
                  '-title "Software Update Helper" '
                  '-heading "Software Update" '
                  '-windowPosition lr '
                  '-button1 "OK" '
                  '-defaultButton 1 '
                  '-timeout 20 '
                  '-icon ' + icon + " "
                  '-description "Software updates will now installed as scheduled.')
                # Get user decision, although we do not care.
                user_decision = subprocess.check_output(cmd)
                run_update()
            except:
                run_update()

            del plist_data['scheduled_install']
            save_plist(plist, plist_data)

        else:
            log("Install already scheduled for " + str(plist_data['scheduled_install']))
            try:
                cmd = shlex.split('/Library/Application\ Support/JAMF/bin/jamfHelper.app/Contents/MacOS/jamfHelper'
                      ' -windowType hud '
                      '-title "Software Update Helper" '
                      '-heading "Software Update Reminder" '
                      '-windowPosition lr '
                      '-button1 "Delay Updates" '
                      '-button2 "Update Now" '
                      '-defaultButton 1 '
                      '-timeout 30 '
                      '-icon ' + icon + " "
                      '-description "Software Updates have been scheduled for ' + str(plist_data['scheduled_install']) +
                                  '. Updates include:\n' + '\n'.join(plist_data['pending_updates']) + '"')
                user_decision = subprocess.check_output(cmd)
                log ("User delayed update.")
            except subprocess.CalledProcessError as error:
                if error.returncode == 2:
                    run_update()
    else:
        check_updates(delay_days)


def usage():
    """
    print usage information
    :return:
    """
    print(
        "Note the order when using switches\n\n"
        "--help (-h) : This help."
        "--version (-v) : Print Version.\n"
        "--lastrun (-l) : Print last time script was run.\n"
        "--icon= (-i) : Full path to icon.png\n"
        "--delay= (-d) : How long in days since last run to wait before checking again.\n"
        "--runnow (-r) : Run software update now.\n"
        "--runschedule (-s) : Run software update based on schedule.\n"
        "--nag (-n) : Check to if updates are scheduled and prompt to install again.\n"
        "--reserves= (-z) : Set to on to create reserves space and off to remove it.\n"
    )


def main(argv):
    if os.path.isfile(plist):
        plist_data = read_plist(plist)
        plist_data.update({'last_run': datetime.datetime.now()})
        save_plist(plist, plist_data)
    else:
        log("Plist not found, making a new one.")
        open(plist, 'a').close()
        plist_data = {'last_run': datetime.datetime.now()}
        save_plist(plist, plist_data)

    try:
        opts, args = getopt.getopt(argv, "d:i:z:rhslvcn", ["delay=",
                                                           "icon=",
                                                           "reserves=",
                                                           "runnow",
                                                           "runschedule",
                                                           "lastrun",
                                                           "version",
                                                           "help",
                                                           "check_schedule",
                                                           "nag"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-v', '--version'):
            print(__version__)
        if opt in ('-i', '--icon'):
            global icon
            icon = arg
        if opt in ('-n', '--nag'):
            nag()
        if opt in ('-c', '--check_schedule'):
            plist_data = read_plist(plist)
            if "scheduled_install" in plist_data.keys():
                print(str(plist_data['scheduled_install']))
            else:
                print("No scheduled install set.")
        if opt in ('-d', '--delay'):
            global delay_days
            delay_days = arg
        if opt in ('-l', '--lastrun'):
            plist_data = read_plist(plist)
            if plist_data:
                last_run = plist_data['last_run']
                print(str(last_run))
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        if opt in ("-s", "--runschedule"):
            run_schedule()
        if opt in ("-r", "--runnow"):
            run_update()
        if opt in ('-z', '--reserves'):
            if arg == 'on':
                create_reserves()
            elif arg == 'off':
                remove_reserves()


if __name__ == '__main__':
    main(sys.argv[1:])

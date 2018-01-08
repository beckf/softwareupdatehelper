import os
import plistlib
import datetime
import logging
import sys
import getopt

plist = "/Library/Application Support/JAMF/org.da.softwareupdatehelper.plist"
current_datetime = datetime.datetime.now()
logdir = "/Library/Logs/softwareupdatehelper/"
logfile = logdir + str(current_datetime) + ".log"


def log(data):
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    logging.basicConfig(filename=logfile, level=logging.DEBUG)
    logging.debug(data)


def save_plist(path, d):
    plistlib.writePlist(d, path)


def read_plist(path):
    try:
        return plistlib.readPlist(path)
    except:
        return False


def run_scheduled_update():
    log("Running scheduled update")
    update_check = os.popen("softwareupdate -l").read()
    if "*" in update_check:
        log("New Updates Available.")

        if "[restart]" in update_check:
            restart = True
        update_result = os.popen("softwareupdate -ai").read()
        log(update_result)

        if restart is True:
            log("Restart requested")
            log(os.popen("sudo jamf policy -event schedule_restart").read())

    plist_data = {"last_run": current_datetime}
    save_plist(plist, plist_data)


def usage():
    print(
        "--runnow (-r) : Run software update now.\n"
        "--runschedule (-s) : Run software update based on schedule"
    )


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "rs", ["runnow", "runschedule"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        if opt in ("-s", "--runschedule"):
            plist_data = read_plist(plist)
            if plist_data:
                last_run = plist_data['last_run']
                duration_time = last_run + datetime.timedelta(weeks = 2)
                if duration_time < current_datetime:
                    run_scheduled_update()
                else:
                    print("Nothing to do.")
            else:
                print("Ready to run and create plist")
                run_scheduled_update()
        if opt in ("-r", "--runnow"):
            run_scheduled_update()


if __name__ == '__main__':
    main(sys.argv[1:])
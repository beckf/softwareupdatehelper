# Software Update Helper

The purpose of this project is to provide a wrapper 
around softwareupdate that gives admins more control 
over applying updates to Macs.  

Software Update Helper allows you to schedule regular updates 
and report back to a management system like JAMF Pro.

## Build Package
Using Luggage:
```
make pkg
```

## JAMF Policies
Create a policy that runs at a frequency you prefer for the machine to checkin with SUS and get updates.

If updates are available they will be scheduled a force install in --delay days in the future.

```
python /usr/local/bin/softwareupdatehelper.py --delay=16 --runschedule
```

Create a policy to nag the user at the frequency you prefer to prompt them to install the updates.  This gives the 
end-user a chance to install at a convenient time before the forced scheduled install.

```
python /usr/local/bin/softwareupdatehelper.py --nag
```

Create a Self-Service Policy that allows users to run SoftwareUpdate anytime.

```
python /usr/local/bin/softwareupdatehelper.py --runnow
```

## Help
```
sudo python ./softwareupdatehelper.py --help
Note the order when using switches

--help (-h) : This help.--version (-v) : Print Version.
--lastrun (-l) : Print last time script was run.
--icon (-i) : Full path to icon.png
--delay (-d) : How long in days since last run to wait before checking again.
--runnow (-r) : Run software update now.
--runschedule (-s) : Run software update based on schedule.
--nag (-n) : Check to if updates are scheduled and prompt to install again.
```
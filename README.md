startup
====

Here is  some documentation on making a startup script for `syslogger`. There are different variations on making
a startup script:

* SystemV (aka `init.d`) : is the traditional one.
* Upstart : used on Debian, Ubuntu(till 14.04) and Redhat.
* Systemd : which is the latest, and everybody is migrating to this one.



### upstart

for Ubuntu 9 - 14.04 we should use `upstart`.

make a `syslogger.conf` file in `/etc/init/` and add the following lines:

	start on runlevel [2345]
	respawn

	pre-start script
		chdir /path/to/working/directory
		echo `pwd`
	end script

	script
		cd /path/to/working/directory
		exec /path/to/twistd -y /path/to/syslogger/syslogger.tac
	end script

	post-stop sleep 10

`respawn`  will start the program on crash or if it has been stopped.
`post-stop` will wait for `10` seconds before starting again.(after a crash(you can test with `kill -9`)).
`cd /path/to/working/directory` in the `script` stanza might not be necessary.But I don't have time to make sure.(TODO)
`pre-start` is a stanza and is executed before main start script which is `script`.


run `init-checkconf /path/to/service.conf` before saving and restarting to check of correct syntax.

#### running the php webserver

make a `syslogger_php.conf` in `/etc/init/` and add the following lines:

	start on runlevel [2345]
	respawn
	
	pre-start script
		chdir /path/to/working directory
		echo `pwd`
	end script

	script
		exec /usr/bin/php -S 0.0.0.0:8000 -t /home/ubuntu/farahoosh/webanalyzer/public
	end script
	
	post-stop sleep 10

`chdir /path/to/working directory` is probably not needed here. I don't have time to make sure.(TODO)



### SysV (aka init.d)


### query for cleaning up the database

delete from weblogs where weblog_id in (select weblog_id from weblogs where to_timestamp(visited_at) < NOW() - INTERVAL '30 days')



# purpose

This directory will hold the deliverables to NABU when the project is finished.
Currently it is used to provide a **DEMO**, used to build a running system with minimal dependencies.

🚀🚀 We have a **running DEMO** now. Just use   https://quick-notes.de/nabu-demo.html
You have to wait 16 seconds until the data appears. This will be much faster in production environment.

- functionality
  - 🟢initial system installation & setup
  - 🟢download GBIF data via python
  - ✍data cleaning (on work)
  - 🟢convert to csv
  - 🟢show datapoints in a map (demo only, loads directly from GBIF database)
      using nabu-asian-hornet-project-dashboard\mockups\v0-june8
  - ✍daily csv update
  - (optional) simulate 1000 new points daily, simulate high load (70.000 data points per year) 

NOTE: the data will be wrong or even simulated. It's just a demo.



Legend: 🔴(error) 🟡(open issue) 🟢(okay) ✍(on work)

# directories in output/

dashboard/ -- a demo website for internal use. e.g. integration as IFRAME 
  deploy with C:\data\vsstudiocode-repo\Dokumentationssystem\tools\upload_f2f_onl.cmd

research/ 
    src/    -- python scripts

# Deployment 
tbd

External website has to include https://f2f.onl/CorrelAid-NABU-Demo/  as an IFRAME.

Example:
~~~
<html>
<title> CorrelAid-NABU Demo </title>
<body>
<pre>
DEMO Page which includes an IFRAME
This is before the IFRAME
</pre>
<iframe src="https://f2f.onl/CorrelAid-NABU-Demo" style="width:100%; height:100vh; border:2px solid;" sandbox="allow-scripts ">
</iframe>
<p>
This is after the IFRAME
</p>
</body>
</html>
~~~

- Alternative: include generated images only, non-interactive

# requirements
- cron ?
- disc space: x MB
- SFTP user/password for data upload (or locally?)
- GBIF user/pw/email
  It is necessary to register as a user on GBIF.org to create a download request.
- external dependencies: Leaflet/Map ??

# configuration
- credentials
  Edit .env file or use UI ???

- IFRAME target
  - .htaccess must have
~~~
<IfModule mod_headers.c>
    Header set Access-Control-Allow-Origin "*"
    Header always set Content-Security-Policy "frame-ancestors 'self' https://Nabu.de/  https://correlaid.org/"
</IfModule>
~~~

- cronjob
    daily (in case of db errors)


# Operations
- deploy
- setup: install dependencies (python Libs) etc
~~~
  bash install.bash
~~~
- Logfile
- Error handling
- Alerting
- Backup
- Support after GO-Live
  Data Engineer: tbd 
  Deployment support: Achim

# Tn-Core Webserver

This directory contains the files used to run the Tn-Core web application. These files are based heavily on the files used to run the MeDuSa web application (https://github.com/combogenomics/medusa-webapp) prepared by Marco Galardini.

## Test the server

"Redis" and "atd deamon" need to be running prior to testing the server. It is also necessary to place a 3.x version of bootstrap in the "static" directory, as well as jquery.min.js in the "static/js" directory. MATLAB must also be installed, and the iLOG CPLEX solver must be on the MATLAB path.

Create a directory called "Software". Within this directory, place the following directories: i) "cobratoolbox" containing the COBRA Toolbox , ii) "FastCore" containing FASTCORE, iii) "libSBML" containing libSBML, iv) "SBML-Toolbox" containing the SBML Toolbox, v) "tiger" containing the TIGER Toolbox, and vi) "Tn-Core" containing the Tn-Core Toolbox. 

Set up the virtual environment with the following code:

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python tncore.py

Open a browser on the same machine and go to 127.0.0.1:5000

## Production

First, install all the dependencies:

    sudo pip install -r requirements.txt

Then install in apache the tncore.conf file (changing the paths).

Create a production.py file which can then be used to override the settings.py debug options.

Restart apache and start redis.

If the tncore.py script is modified, please resart apache to initialize the changes.

Edit the mail_log.py file to setup the error logging through email.

You may also want to set up a cron job to wipe out the uploads directly every now and then

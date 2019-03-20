#!/usr/bin/env python

import os
import sys
import json
import subprocess
import time
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, escape, Response, send_from_directory
from werkzeug.utils import secure_filename

from utils import generate_hash
from utils import generate_time_hash

from store import add_job
from store import update_job
from store import retrieve_job
from store import cumulative_jobs
from store import unique_ips
from store import unique_emails

import settings

app = Flask(__name__)

# App config from settings.py
app.config.from_object(settings)

# Production settings that override the testing ones
try:
    import production
    app.config.from_object(production)
except ImportError:
    pass

# Mail log setup
try:
    import mail_log as ml
    if not app.debug:
        import logging
        mail_handler = ml.TlsSMTPHandler(ml.MAIL_HOST,
                               ml.MAIL_FROM,
                               ml.ADMINS, 'Tn-Core webapp Failed!',
                               credentials=(ml.MAIL_USER,
                                            ml.MAIL_PWD))
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
except ImportError:
    pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['GET', 'POST'])
def run():
    # Here handle submissions and run the analysis
    # Send emails on failures, success
    # Use redis to store user stats (hashed for privacy)
    if request.method == 'POST':
        # First things first, compute user hash
        req_id = generate_time_hash(request.remote_addr)

        # To avoid slow-downs in the running directory
        # create subdirs w/ the first 2 chars of the hash
        h2c = req_id[:2]
        try:
            os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'],
                                  h2c))
        except:
            pass

        # Prepare the working directory
        # Our hash scheme ensures that it should be unique
        wdir = os.path.join(app.config['UPLOAD_FOLDER'],
                            h2c, req_id)
        wdir = os.path.abspath(wdir)
        os.mkdir(wdir)

        # Save model file
        model = request.files['model']
        if model:
            filename = secure_filename(model.filename)
            model.save(os.path.join(wdir, filename))
            modelName = filename
        else:
            flash(u'Something went wrong with your metabolic reconstruction',
                  'danger')
            return redirect(url_for('index'))
       
        # Save exchange reaction file
        excRxns = request.files['excRxns']
        if excRxns:
           filename = secure_filename(excRxns.filename)
           excRxns.save(os.path.join(wdir, filename))
           excRxnsName = filename
        else:
           flash(u'Something went wrong with your exchange reaction list',
                 'danger')
           return redirect(url_for('index'))
               
        # Save objective reaction file
        objRxn = request.files['objRxn']
        if objRxn:
           filename = secure_filename(objRxn.filename)
           objRxn.save(os.path.join(wdir, filename))
           objRxnName = filename
        else:
           flash(u'Something went wrong with your objective reaction file',
                 'danger')
           return redirect(url_for('index'))

        # Save TnSeq data file
        tnseq = request.files['tnseq']
        if tnseq:
           filename = secure_filename(tnseq.filename)
           tnseq.save(os.path.join(wdir, filename))
           tnseqName = filename
        else:
           flash(u'Something went wrong with your TnSeq data file',
                 'danger')
           return redirect(url_for('index'))
               
        # Save RNAseq data file
        rnaseq = request.files['rnaseq']
	if rnaseq:
           filename = secure_filename(rnaseq.filename)
           rnaseq.save(os.path.join(wdir, filename))
           rnaseqName = filename
        else:
           rnaseqName = 'empty'
               
        # Save the minimal growth rate
        growthFrac = request.form['growthFrac']
        if growthFrac:
           gFrac = growthFrac
        else:
           gFrac = 'empty'

        # Save the expression threshold
        expressThresh = request.form['expressThresh']
        if expressThresh:
           eThresh = expressThresh
        else:
           eThresh = 'empty'

        # Check email, hash it
        email = request.form['email']
        if email:
            hemail = generate_hash(email)
        else:
            flash(u'Something went wrong with your email', 'danger')
            return redirect(url_for('index'))
        
        # Secure my results?
        passphrase = request.form['passphrase']
        if passphrase:
            hpass = generate_hash(passphrase)
        else:
            hpass = None
        # In case of a passphrase, don't bother the current submitter
        session['req_id'] = req_id       

        # Submit the job
        # Then redirect to the waiting page
        try:
            # Send details to redis
            # where the job's status is monitored
            add_job(req_id, request.remote_addr, hemail, hpass)
        except Exception as e:
            flash(u'Could not save your job details (%s)' % e, 'danger')
            return redirect(url_for('index')) 
        try:
            # prepare a bash script wrapping the wrapper
            # the wrapper inside the bash script updates the redis db
            # informing on the job status
            cmd = 'python tasks.py %s %s %s %s %s %s %s %s %s' % (req_id,
                                                   wdir,
                                                   modelName,
                                                   excRxnsName,
                                                   objRxnName,
                                                   tnseqName,
                                                   rnaseqName,
                                                   gFrac,
                                                   eThresh)
            f = open(os.path.join(wdir, 'cmd.sh'), 'w')
            f.write(cmd + '\n')
            f.close()
            cmd = 'at -q b -M now -f %s' % os.path.join(wdir, 'cmd.sh')
            proc = subprocess.Popen(cmd,
                                    shell=(sys.platform!="win32"),
				    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
				    stderr=subprocess.PIPE)
	    out = proc.communicate()
	    
	    return_code = proc.returncode
	    if return_code != 0:
		raise Exception('%s'%str(out[1]))
        except Exception as e:
            flash(u'Could not submit your job "%s"' % e,
                  'danger')
            return redirect(url_for('index'))
            
        return redirect(url_for('results',
                        req_id=req_id))

    # No POST, return to start
    flash(u'No job details given, would you like to start a new one?',
          'warning')
    return redirect(url_for('index'))

@app.route('/log/<req_id>')
def log(req_id):
    # Get details from redis
    j = retrieve_job(req_id)

    # TODO: avoid access to redirect to results
    # Check passphrase
    if 'req_id' not in session:
        # bother the user
        return redirect(url_for('access',
                        req_id=req_id))
    if 'req_id' in session and req_id != escape(session['req_id']):
        # clean the session, then bother the user
        session.pop('req_id', None)
        return redirect(url_for('access',
                        req_id=req_id))
    
    # Return the log, if present
    h2c = req_id[:2]
    if not os.path.exists(os.path.join(
                              app.config['UPLOAD_FOLDER'],
                              h2c, req_id)):
        flash('Could not retrieve the log: is your job older than one week?', 'danger')
        return render_template('index.html') 
    if 'log.txt' not in os.listdir(os.path.join(
                                      app.config['UPLOAD_FOLDER'],
                                      h2c, req_id)):
        flash('Could not retrieve the log.txt file', 'danger')
        return render_template('error.html', req_id=req_id)

    path = os.path.join(app.config['UPLOAD_FOLDER'],
                        h2c, req_id, 'log.txt')
    return Response(''.join(open(path).readlines()),
                    mimetype='text/plain')

@app.route('/err/<req_id>')
def err(req_id):
    # Get details from redis
    j = retrieve_job(req_id)

    # TODO: avoid access to redirect to results
    # Check passphrase
    if 'req_id' not in session:
        # bother the user
        return redirect(url_for('access',
                        req_id=req_id))
    if 'req_id' in session and req_id != escape(session['req_id']):
        # clean the session, then bother the user
        session.pop('req_id', None)
        return redirect(url_for('access',
                        req_id=req_id))
    
    # Return the log, if present
    h2c = req_id[:2]
    if not os.path.exists(os.path.join(
                              app.config['UPLOAD_FOLDER'],
                              h2c, req_id)):
        flash('Could not retrieve the log: is your job older than one week?', 'danger')
        return render_template('index.html')
    if 'log.err' not in os.listdir(os.path.join(
                                      app.config['UPLOAD_FOLDER'],
                                      h2c, req_id)):
        flash('Could not retrieve the log.err file', 'danger')
        return render_template('error.html', req_id=req_id)

    path = os.path.join(app.config['UPLOAD_FOLDER'],
                        h2c, req_id, 'log.err')
    return Response(''.join(open(path).readlines()),
                    mimetype='text/plain')

@app.route('/excel/<req_id>')
def excel(req_id):
    # Get details from redis
    j = retrieve_job(req_id)

    # TODO: avoid access to redirect to results
    # Check passphrase
    if 'req_id' not in session:
        # bother the user
        return redirect(url_for('access',
                        req_id=req_id))
    if 'req_id' in session and req_id != escape(session['req_id']):
        # clean the session, then bother the user
        session.pop('req_id', None)
        return redirect(url_for('access',
                        req_id=req_id))
    
    # Return the log, if present
    h2c = req_id[:2]
    if not os.path.exists(os.path.join(
                              app.config['UPLOAD_FOLDER'],
                              h2c, req_id)):
        flash('Could not retrieve the Excel file: is your job older than one week?', 'danger')
        return render_template('index.html')
    if 'exportedModel.xlsx' not in os.listdir(os.path.join(
                                      app.config['UPLOAD_FOLDER'],
                                      h2c, req_id)):
        flash('Could not retrieve the Excel file', 'danger')
        return render_template('error.html', req_id=req_id)

    path = os.path.join(app.config['UPLOAD_FOLDER'],
                        h2c, req_id)
    return send_from_directory(path,
                               'exportedModel.xlsx',
                               as_attachment=True)

@app.route('/matlab/<req_id>')
def matlab(req_id):
    # Get details from redis
    j = retrieve_job(req_id)

    # TODO: avoid access to redirect to results
    # Check passphrase
    if 'req_id' not in session:
        # bother the user
        return redirect(url_for('access',
                        req_id=req_id))
    if 'req_id' in session and req_id != escape(session['req_id']):
        # clean the session, then bother the user
        session.pop('req_id', None)
        return redirect(url_for('access',
                        req_id=req_id))
    
    # Return the log, if present
    h2c = req_id[:2]
    if not os.path.exists(os.path.join(
                              app.config['UPLOAD_FOLDER'],
                              h2c, req_id)):
        flash('Could not retrieve the MATLAB file: is your job older than one week?', 'danger')
        return render_template('index.html')
    if 'exportedModel.mat' not in os.listdir(os.path.join(
                                      app.config['UPLOAD_FOLDER'],
                                      h2c, req_id)):
        flash('Could not retrieve the MATLAB file', 'danger')
        return render_template('error.html', req_id=req_id)

    path = os.path.join(app.config['UPLOAD_FOLDER'],
                        h2c, req_id)
    return send_from_directory(path,
                               'exportedModel.mat',
                               as_attachment=True)

@app.route('/results/<req_id>')
def results(req_id):
    # Here show the results or the wait page
    # Get the right job using the session or the hash key
    
    # Get details from redis
    j = retrieve_job(req_id)

    # Check passphrase
    if 'req_id' not in session:
        # bother the user
        return redirect(url_for('access',
                        req_id=req_id))
    if 'req_id' in session and req_id != escape(session['req_id']):
        # clean the session, then bother the user
        session.pop('req_id', None)
        return redirect(url_for('access',
                        req_id=req_id))

    h2c = req_id[:2]
    status = j['status']
    if status == 'Job done':
        # run results logics
        try:
            result = json.load(open(os.path.join(app.config['UPLOAD_FOLDER'],
                                                 h2c, req_id, 'result.json')))
        except Exception as e:
            app.logger.error('Internal server error: %s\nRequest ID: %s' % (e, req_id))
            flash(u'Internal server error: %s'%e, 'danger')
            return render_template('error.html', req_id=req_id)
        return render_template('result.html', req_id=req_id,
                                              data=result)
    elif status == 'Job failed':
        error_msg = j.get('error', '')
        app.logger.error('Internal server error: %s\nRequest ID: %s' % (error_msg,
                         req_id))
        flash(u'Internal server error: %s' % error_msg,
               'danger')
        return render_template('error.html', req_id=req_id)
    else:
        # If too much time has passed, it means that the job has either failed
        # or something like that
        cur_time = time.time()
        start_time = float(j['time'])
        delta_time = cur_time - start_time
        if (60 * 30) < delta_time < (60 * 60):
            flash(u'Your job exceeded 30 minutes, something might have gone wrong!' +
                  u'Will try 30 more minutes before giving up',
                  'danger')
        elif delta_time > (60 * 60):
            flash(u'Your job exceeded 60 minutes, something must have gone wrong!' +
                  u'If your reconstruction is very large, you might want to run Tn-Core locally',
                  'danger')
            return render_template('error.html', req_id=req_id)
        return render_template('waiting.html', status=status)

@app.route('/access/<req_id>', methods=['GET', 'POST'])
def access(req_id):
    # Here ask for a passphrase

    # If this is a POST request
    # Compare it and redirect accordingly
    
    # Get details from redis
    j = retrieve_job(req_id)

    # If no passphrase, no need to bother, just redirect
    if 'passphrase' not in j:
        session['req_id'] = req_id
        return redirect(url_for('results',
                        req_id=req_id))
    
    if request.method == 'POST':
        # compare passphrases, after hashing
        passphrase = request.form['passphrase']
        if passphrase:
            hpass = generate_hash(passphrase)
        else:
            flash(u'Error handling your passphrase', 'danger')
            return render_template('access.html', req_id=req_id)
        
        # Compare
        if hpass == j['passphrase']:
            # Correct!
            session['req_id'] = req_id
            return redirect(url_for('results',
                                    req_id=req_id))
        else:
            flash(u'Passphrase does not match', 'danger')
            session.pop('req_id', None)
            return render_template('access.html', req_id=req_id)

    # Redirect to password form
    flash('This job is protected by a passphrase', 'info')
    return render_template('access.html', req_id=req_id)
    
@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/stats/jobs')
def jobs():
    return Response(json.dumps([{'date':x[1],
                                 'jobs':x[0]} for x in cumulative_jobs()]),
                    mimetype='text/plain')

@app.route('/stats/ips')
def ips():
    return Response(json.dumps([{'date':x[1],
                                 'ips':x[0]} for x in unique_ips()]),
                    mimetype='text/plain')

@app.route('/stats/emails')
def emails():
    return Response(json.dumps([{'date':x[1],
                                 'emails':x[0]} for x in unique_emails()]),
                    mimetype='text/plain')

@app.route('/admin')
def admin():
    # Here admin section: upload a new binary/script
    # Clean manually the jobs
    flash('Not implemented yet', 'warning')
    return render_template('index.html')

if __name__ == '__main__':
    app.run()

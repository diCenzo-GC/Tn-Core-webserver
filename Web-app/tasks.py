#!/usr/bin/env python

import os
import shutil
import subprocess
import sys
import json

from Bio import SeqIO

from store import update_job

def run_cmd(cmd, ignore_error=False):
    """
    Run a command line command
    Returns True or False based on the exit code
    """

    proc = subprocess.Popen(cmd,shell=(sys.platform!="win32"),
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
    out = proc.communicate()
    return_code = proc.returncode

    t = open('log.txt', 'w')
    e = open('log.err', 'w')

    t.write('%s\n'%str(out[0]))
    if return_code != 0 and not ignore_error:
        e.write('Command (%s) failed w/ error %d\n'
                        %(cmd, return_code))
        e.write('%s\n'%str(out[1]))
        e.write('\n')

    e.write('%s\n'%str(out[1]))
    if return_code != 0 and not ignore_error:
        e.write('Command (%s) failed w/ error %d\n'
                        %(cmd, return_code))
        e.write('%s\n'%str(out[1]))
        e.write('\n')

    return bool(not return_code)

def run_tncore(req_id, wdir, model, excRxns, objRxn, tnseq, rnaseq, growthFrac, expressThresh):
    sdir = os.getcwd()
    
    update_job(req_id, 'status', 'Renaming the files')

    # Change to the working directory and copy tncore
    os.chdir(wdir)
    shutil.copy(os.path.join(sdir, 'tncore_webserver.m'),
                    os.path.join(wdir, 'tncore_webserver.m'))

    # Rename the files
    shutil.move(os.path.join(wdir, model),
                os.path.join(wdir, 'inputModel.xml'))
    shutil.move(os.path.join(wdir, excRxns),
                os.path.join(wdir, 'ExRxns.txt'))
    shutil.move(os.path.join(wdir, objRxn),
                os.path.join(wdir, 'ObjectiveRxn.txt'))
    shutil.move(os.path.join(wdir, tnseq),
                os.path.join(wdir, 'TnSeqData.txt'))
    if rnaseqName != 'empty':
        shutil.move(os.path.join(wdir, rnaseq),
                    os.path.join(wdir, 'RnaSeqData.txt'))

    update_job(req_id, 'status', 'Running Tn-Core')

    # Run Tn-Core
    if growthFrac != 'empty':
        if expressThresh != 'empty':
            cmd = 'matlab -nodesktop -nosplash -r "tncore_webserver(%s, %s)"' % (growthFrac, expressThresh)
        else:
            cmd = 'matlab -nodesktop -nosplash -r "tncore_webserver(%s)"' % (growthFrac)
    else:
        if expressThresh != 'empty':
            cmd = 'matlab -nodesktop -nosplash -r "tncore_webserver([], %s)"' % (expressThresh)
        else:
            cmd = 'matlab -nodesktop -nosplash -r tncore_webserver'

    run_cmd(cmd, ignore_error=False)

    update_job(req_id, 'status', 'Cleaning up')
    try:
        # Be kind, remove the original files...
        os.remove(os.path.join(wdir, 'inputModel.xml'))
        os.remove(os.path.join(wdir, 'ExRxns.txt'))
        os.remove(os.path.join(wdir, 'ObjectiveRxn.txt'))
        os.remove(os.path.join(wdir, 'TnSeqData.txt'))
        if rnaseq != 'empty':
            os.remove(os.path.join(wdir, 'RnaSeqData.txt'))

    except:pass
    
    # Return back to the original directory
    os.chdir(sdir)




if __name__ == "__main__":
    req_id = sys.argv[1]
    wdir = sys.argv[2]
    modelName = sys.argv[3]
    excRxnsName = sys.argv[4]
    objRxnName = sys.argv[5]
    tnseqName = sys.argv[6]
    rnaseqName = sys.argv[7]
    gFrac = sys.argv[8]
    eThresh = sys.argv[9]

    update_job(req_id, 'status', 'Job starting')
    try:
        result = run_tncore(req_id, wdir, modelName, excRxnsName, objRxnName, tnseqName, rnaseqName, gFrac, eThresh)
        json.dump(result, open(os.path.join(wdir, 'result.json'), 'w'))
        update_job(req_id, 'status', 'Job done')
    except Exception as e:
        update_job(req_id, 'status', 'Job failed')
        update_job(req_id, 'error', str(e))



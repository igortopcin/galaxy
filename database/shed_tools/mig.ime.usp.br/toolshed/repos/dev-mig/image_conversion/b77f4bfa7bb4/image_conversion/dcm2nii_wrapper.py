#!/usr/bin/env python
# Author: topcin@ime.usp.br

import sys
import os
import os.path
import subprocess
import optparse
import shutil
import glob
import tempfile

def _stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()

def _copy(source, destination):
    try:
        os.link(source, destination)
        print 'link src: %s; dest: %s' % (source, destination)
    except:
        shutil.copy(source, destination)
        print 'copy src: %s; dest: %s' % (source, destination)

def main():
    parser = optparse.OptionParser()

    parser.add_option('-i', '--input-dir', action="store", type="string", dest='input_dir', help='Directory that contains the DICOM files that will be converted to NIfTI')
    #parser.add_option('-e', '--output-bvec', action="store", type="string", dest='output_bvec', help='Path of the output bvec file')
    #parser.add_option('-a', '--output-bval', action="store", type="string", dest='output_bval', help='Path of the output bval file')
    #parser.add_option('-n', '--output-nii-gz', action="store", type="string", dest='output_nii_gz', help='Path of the output nii.gz file')
    parser.add_option('-b', '--output-dir', action="store", type="string", dest='output_dir', help='Path of the output .nii.gz, .bvec and .bval files')
    parser.add_option('-c', '--config', action="store", type="string", dest='config', help='Optional configuration file')

    (opt, args) = parser.parse_args()

    working_dir = os.getcwd()

    print '\nargs:\n%s' % '\n'.join(sys.argv[1:])
    print '\noptions (a):\n%s' % opt
    print '\nworking_dir: %s' % working_dir

    if not os.path.exists(opt.input_dir):
        _stop_err('No valid input directory was given')

    input_dir_files = os.listdir(opt.input_dir)
    if not input_dir_files:
        _stop_err('The given input directory is empty')

    # Example: dcm2nii -a n -b config/dcm2nii.ini -o /tmp 01/ST000000/SE000000/MR000000
    cmd = 'dcm2nii -a n -o %s' % working_dir
    if opt.config:
        cmd += ' -b %s' % opt.config
    cmd += ' %s/%s' % (opt.input_dir, input_dir_files[0])

    print 'running: %s' % cmd

    try:
        with tempfile.NamedTemporaryFile(prefix='log.dcm2nii.', suffix='.out', dir=working_dir, delete=False) as tmp_stdout,\
                tempfile.NamedTemporaryFile(prefix='log.dcm2nii.', suffix='.err', dir=working_dir, delete=False) as tmp_stderr:
            proc = subprocess.Popen(cmd, shell=True, cwd='.', stdout=tmp_stdout, stderr=tmp_stderr)
            returncode = proc.wait()

            tmp_stdout.seek(0)
            print tmp_stdout.read()

            if returncode:
                try:
                    tmp_stderr.seek(0)
                    raise Exception, tmp_stderr.read()
                except OverflowError:
                    pass
    except:
        _stop_err('Child process failed: %s' % cmd)

    print "Now we are moving files"

    for file in os.listdir(working_dir):
        print 'File: %s' % file;

    list_bvec = glob.glob('%s/*.bvec' % working_dir)
    list_bval = glob.glob('%s/*.bval' % working_dir)
    list_nii_gz = glob.glob('%s/*.nii.gz' % working_dir)

    print 'bvec: %s' % list_bvec
    print 'bval: %s' % list_bval
    print 'nii.gz: %s' % list_nii_gz

    output_bvec = os.path.join(opt.output_dir, 'dataset.bvec')
    output_bval = os.path.join(opt.output_dir, 'dataset.bval')
    output_nii_gz = os.path.join(opt.output_dir, 'dataset.nii.gz')

    if not os.path.exists(opt.output_dir):
        os.makedirs(opt.output_dir)

    if list_bvec: _copy(list_bvec[0], output_bvec)
    if list_bval: _copy(list_bval[0], output_bval)
    if list_nii_gz: _copy(list_nii_gz[0], output_nii_gz)

if __name__ == '__main__': main()
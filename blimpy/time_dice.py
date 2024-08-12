#!/usr/bin/env python
"""
    Script to dice data to course channel level. From BL FIL of HDF5 files, and outputs HDF5 with '_diced' appended to the file name.

    ..author: Brendan Watters, based heavily on dice.py by Greg Hellbourg (gregory.hellbourg@berkeley.edu)

    March 2018
"""


from .waterfall import Waterfall
import argparse
import math
import sys
from .utils import change_the_ext

#------
# Logging set up
import logging
logger = logging.getLogger(__name__)

level_log = logging.INFO

if level_log == logging.INFO:
    stream = sys.stdout
    format = '%(name)-15s %(levelname)-8s %(message)s'
else:
    stream =  sys.stderr
    format = '%%(relativeCreated)5d (name)-15s %(levelname)-8s %(message)s'

logging.basicConfig(format=format,stream=stream,level = level_log)
#------

def cmd_tool(args=None):
    """ Dices (extracts time range) hdf5 or fil files to new file.

    optional arguments:
      -h, --help            show this help message and exit
      -f IN_FNAME, --input_filename IN_FNAME
                            Name of file to write from (HDF5 or FIL)
      -b T_START            Start time in s
      -e T_STOP             Stop time in s
      -x OUT_FORMAT, --output_file OUT_FORMAT
                            Output file format [.h5 or .fil].
      -o OUT_FNAME, --output_filename OUT_FNAME
                            Ouput file name to write (to HDF5 or FIL).
      -l MAX_LOAD           Maximum data limit to load.
    """

    parser = argparse.ArgumentParser(description='Dices (extracts time range)  hdf5 or fil files and writes to hdf5 or fil.')
    parser.add_argument('-f', '--input_filename', action='store', default=None, dest='in_fname', type=str, help='Name of file to write from (HDF5 or FIL)')
    parser.add_argument('-b', action='store', default=None, dest='t_start', type=float, help='Start time in s')
    parser.add_argument('-e', action='store', default=None, dest='t_stop', type=float, help='Stop time in s')
    parser.add_argument('-x', '--output_file', action='store', default=None, dest='out_format', type=str, help='Output file format [.h5 or .fil].')
    parser.add_argument('-o', '--output_filename', action='store', default=None, dest='out_fname', type=str, help='Ouput file name to write (to HDF5 or FIL).')
    parser.add_argument('-l', action='store', default=None, dest='max_load', type=float,help='Maximum data limit to load.')

    if args is None:
        args = sys.argv[1:]

        if len(sys.argv) == 1:
            logger.error('Indicate file name and start and stop times')
            sys.exit()

    args = parser.parse_args(args)

    if args.in_fname is None:
            logger.error('Need to indicate input file name')
            sys.exit()

    if args.out_fname is None:
        if (args.out_format is None) or (args.out_format == 'h5'):
            if args.in_fname[len(args.in_fname)-4:] == '.fil':
                args.out_fname = args.in_fname
                args.out_fname = change_the_ext(args.out_fname, 'fil','_diced.h5')
            elif args.in_fname[len(args.in_fname)-3:] == '.h5':
                args.out_fname = args.in_fname
                args.out_fname = change_the_ext(args.out_fname,'.h5','_diced.h5')
            else:
                logger.error('Input file not recognized')
                sys.exit()
        elif args.out_format == 'fil':
            if args.in_fname[len(args.in_fname)-4:] == '.fil':
                args.out_fname = args.in_fname
                args.out_fname = change_the_ext(args.out_fname, 'fil','_diced.fil')
            elif args.in_fname[len(args.in_fname)-3:] == '.h5':
                args.out_fname = args.in_fname
                args.out_fname = change_the_ext(args.out_fname,'.h5','_diced.fil')
            else:
                logger.error('input file not recognized.')
                sys.exit()

        else:
            logger.error('Must indicate either output file name or valid output file extension.')
            sys.exit()

    elif (args.out_fname[len(args.out_fname)-4:] == '.fil') and (args.out_format == 'h5'):
        logger.error('Output file extension does not match output file name')
        sys.exit()

    elif (args.out_fname[len(args.out_fname)-3:] == '.h5') and (args.out_format == 'fil'):
        logger.error('Output file extension does not match output file name.')
        sys.exit()

    if (args.out_fname[len(args.out_fname)-3:] != '.h5') and (args.out_fname[len(args.out_fname)-4:] != '.fil'):
        logger.error('Indicate output file name with extension, or simply output file extension.')
        sys.exit()

    if args.t_start == None and args.t_stop == None:
        logger.error('Please give either start and/or end time. Otherwise use fil2h5 or h52fil functions.')
        sys.exit()

    #Read start tiem and time resolution from data set
    file_big = Waterfall(args.in_fname, max_load = args.max_load)
    t_start_file_mjd = file_big.header['tstart']
    t_start_file = 0
    t_end_file_mjd = file_big.header['tstart'] + (file_big.header['tstamp'] * file_big.header['nsamples']) / (24 * 60**2)
    t_end_file = file_big.header['tstamp'] * file_big.header['nsamples']
    #f_min_file = file_big.header['fch1']
    #f_max_file = file_big.header['fch1'] + file_big.header['nchans'] * file_big.header['foff']

    if args.t_start == None:
        logger.warning('Start time not given, setting to ' + str(t_start_file) + ' s to match file.')

    if args.t_stop == None:
        logger.warning('End time not given, setting to ' + str(t_end_file) + ' s to match file.')


    if t_end_file < t_start_file:
            t_end_file,t_start_file = t_start_file,t_end_file

    LengthTimeFile = t_end_file-t_start_file
    stdDF = LengthTimeFile / float(file_big.header['nsamples'])

    if args.t_stop < args.t_start:
            args.t_stop,args.t_start = args.t_start,args.t_stop

    if args.t_start < t_end_file and args.t_start > t_start_file and args.t_stop > t_end_file:
            args.t_stop = t_end_file
            logger.warning('End time set to ' + str(t_end_file) + ' s to match file.')

    if args.t_stop < t_end_file and args.t_stop > t_start_file and args.t_start < t_start_file:
            args.t_start = t_start_file
            logger.warning('Start time set to ' + str(t_start_file) + ' s to match file.')

    if args.t_start < t_start_file and args.t_stop > t_end_file:
            args.t_start = t_start_file
            args.t_stop = t_end_file
            logger.warning('Start time set to ' + str(t_start_file) + ' s and end time set to ' + str(t_end_file) + ' s to match file.')
            # print '\nindicated frequencies include file frequency span - no need to dice\n'
            # sys.exit()

    if min(args.t_start,args.t_stop) < t_start_file or max(args.t_start,args.t_stop) > t_end_file:
            logger.error('Time selection to extract must be within ' + str(t_start_file) + ' s and ' + str(t_end_file) + ' s.')
            sys.exit()

    # calculate real sample start and end times
    t_start_real = math.floor((min(args.t_start,args.t_stop) - t_start_file)/stdDF)*stdDF + t_start_file
    t_stop_real = t_end_file - math.floor((t_end_file - max(args.t_start,args.t_stop))/stdDF)*stdDF

    # print "true start time is " + str(t_start_real)
    # print "true stop time is " + str(t_stop_real)

    logger.info('Writing to ' + args.out_fname)
    logger.info('Extacting from ' + str(t_start_real) + ' MHz to ' + str(t_stop_real) + ' MHz.')

    # create waterfall object
    file_small = Waterfall(args.in_fname, t_start = t_start_real, t_stop = t_stop_real, max_load = args.max_load)

    # write waterfall object
    if args.out_fname[len(args.out_fname)-4:] == '.fil':
        file_small.write_to_fil(args.out_fname)
    elif args.out_fname[len(args.out_fname)-3:] == '.h5':
        file_small.write_to_hdf5(args.out_fname)
    else:
        logger.error('Error in output file creation : verify output file name and extension.')
        sys.exit()


if __name__ == "__main__":
    cmd_tool()

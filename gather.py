#!/usr/bin/python3
import argparse
import errno
import os
from pathlib import Path
import sys
import numpy as np
import subprocess
from tqdm import tqdm
from colorama import Fore
from multiprocessing import Pool

"""
gather_fits.py: This program collects data from AmpTools fits and stores them in a single location.
    This is useful if you need to collect additional fit data or the program run_amptools.py exited
    before it got to this step for some reason. Note that this code is run at the end of run_amptools.py.
    Run it without arguments for a more detailed description of its inputs.
    Author: Nathaniel Dene Hoffman - Carnegie Mellon University - GlueX Collaboration
    Creation Date: 13 July 2021
"""

def gather(output_dir, config_file):
    """Gathers cumulative results of fits, calculates intensities with get_fit_results, and outputs to a tab-separated file

    This method goes through all the bin directories, finds converged fits, and runs a C program that uses IUAmpTools/FitResults.h
    to collect the amplitude fit values and their errors, as well as the total likelihood. A particular bin and iteration
    converged fit represents one line in the final output file, which will be a tab-separated file with unordered rows.
    The first column is the bin number, the second is the iteration number, and the rest are paired columns of parameters
    and parameter errors. The input to the C program will be the fit file followed by a list of parameters.

    :param output_dir: directory which contains bin subdirectories
    :type output_dir: Path
    :param config_file: template of AmpTools configuration file
    :type config_file: Path

    :rtype: None
    :return: None
    """
    print("Gathering Results")
    with open(config_file, 'r') as config:
        config_lines = config.readlines() # read in the lines from the config template file
        headers = []
        for line in config_lines:
            if line.startswith("amplitude"): # find amplitude lines
                wave_name = line.split()[1].strip() # get the parameter name (KsKs::PositiveIm::S0+, for example)
                wave_parts = wave_name.split("::")
                if wave_parts[1].endswith("Re"):
                    headers.append(wave_parts[2])
                    headers.append(wave_parts[2] + "_err")
        headers.append("total_intensity")
        headers.append("total_intensity_err")
        headers.append("likelihood")
    with open(output_dir / "fit_results.txt", 'w') as out_file:
        header = "\t".join(headers)
        out_file.write(f"Bin\tIteration\tConvergence\t{header}\n") # print the header to the output file
        bin_dirs = [bindir for bindir in output_dir.glob("*") if bindir.is_dir()]
        bin_converged_total = np.zeros_like(bin_dirs)
        bin_total_iterations = np.zeros_like(bin_dirs)
        for bin_dir in tqdm(bin_dirs): # for each bin subdirectory
            bin_num_string = bin_dir.name
            iter_dirs = [iterdir for iterdir in bin_dir.glob("*") if iterdir.is_dir()] # for each iteration subdirectory
            for iteration_dir in iter_dirs:
                iteration_num_string = iteration_dir.name
                fit_files = [fit.resolve() for fit in iteration_dir.glob("*.fit")]
                latest_fit_file = max(fit_files, key=os.path.getctime)
                fit_results = iteration_dir / "fit_results.txt"
                bin_total_iterations[int(bin_num_string)] += 1
                if "CONVERGED" in latest_fit_file.name: # only collect converged fits
                    bin_converged_total[int(bin_num_string)] += 1
                with open(fit_results) as fit_reader:
                    out_file.write(fit_reader.read()) # write fit results to output file (in no particular row order)
        print("Convergence Results:")
        for i, bin_converged_num in enumerate(bin_converged_total):
            percent_converged = bin_converged_total[i] / bin_total_iterations[i]
            if percent_converged == 0:
                color = Fore.RED
            elif percent_converged <= 0.25:
                color = Fore.YELLOW
            elif percent_converged <=0.80:
                color = Fore.BLUE
            else:
                color = Fore.GREEN
            print(f"{color}Bin {i}: {bin_converged_total[i]}/{bin_total_iterations[i]}\t{Fore.WHITE}", end='')
        print()

"""
Script begins here:
"""
parser = argparse.ArgumentParser(description="Runs AmpTools fits on each mass bin")
parser.add_argument("-d", "--directory", required=True, help="the input directory (output of divide_data.py)")
parser.add_argument("-c", "--config", required=True, help="path to the AmpTools config template file")
if len(sys.argv) == 1: # if the user doesn't supply any arguments, print the help string and exit
    parser.print_help(sys.stderr)
    sys.exit(1)
args = parser.parse_args()

bin_directory = Path(args.directory).resolve()
if bin_directory.is_dir(): # check if directory with all the separated bins exists
    print(f"Input Directory: {bin_directory}")
else:
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), args.directory)

config_template = Path(args.config).resolve()
if config_template.is_file(): # check if config file exists
    print(f"Config Template: {config_template}")
else:
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), args.config)

gather(bin_directory, config_template)

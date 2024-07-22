#! python

import os
import re 
import sys
import argparse
import csv

# Script to help organise the processing of run folders with multiple sequencing types within them
    # First argument is the run folder name
    # Second argument is the run_info.csv 
    # optional argument is --dual
    # output directories/symlinks are created in current working directory

# More detail:
# This script takes a csv file 
    # Where the first/(& second) column is barcodes for single index/dual index runs
    # The remaining columns are used as input to describe the run
        # Current suggestion for Houseley group is: (Barcode), Barcode Owner,Run Type,Genome,Trael Indexes
        # But this can be flexible - more/fewer options in any order
    # The only assumptions are
        # the first line is a header line and is ignored
        # The first column / 2 columns are barcodes (depending on if --dual flag is run)
            # default behaviour is for single index, --dual specifies dual index

# The contents of the run description columns are joined to give an informative directory name
    # These directories are created within the current working directory
    # For this run folder create symlinks to the fastq files
        # Fastq files whose barcodes match the run descriptions are stored in those sub-directories

def main():

    # read in options from the command line
    options = parse_arguments()

    run_folder = options.run_folder
    info_file = options.run_info_file
    dual_barcode = options.dual

    if not options.run_info_file.endswith(".csv"):
        parser.error("The run info file must be a CSV file.")

    #set working directory (place directory structure will be made and symlinks will be stored)
    working_dir = os.getcwd()
    
    #set the path to the seqfac fastq files
    seqfac_path="/bi/seqfac/seqfac/"+run_folder+"/Unaligned/Project_External/Sample_lane1/"
    
    # create the directory structure in the current working directory
    run_dict = read_run_info(info_file,dual_barcode)

    #print(run_dict)
    
    # create links to fastq files within the appropriate sub-directories 
    make_multi_run_structure(run_dict,working_dir,seqfac_path)


def make_multi_run_structure(run_dict, working_dir,seqfac_path):
    for run_type, barcodes in run_dict.items():
        dir_path = os.path.join(working_dir, run_type)
        make_dir(dir_path)
        make_links(seqfac_path, working_dir, run_type,barcodes)

def make_links(seqfac_path, dest_dir, run_type,barcodes):
    
    #the barcodes to search for (ignore the first value of the list as this is the run_info for the filename)
    patterns = [re.compile(barcode) for barcode in barcodes[1:]]

    # for the fastq files in the seqfac run folder look for a barcode match and create link in subdirectory
    for root,dirs,files in os.walk(seqfac_path):
        for file in files:
            if not file.endswith(".fastq.gz"):
                continue
            file_path = os.path.join(root, file)
            
            if any(pattern.search(file) for pattern in patterns):
                ending = r"(_L\d{3}_R\d\.fastq\.gz)$"
                # create the link name from the first entry in barcodes which is the reduced run_info
                link_name = re.sub(ending, f"_{barcodes[0]}\\1", file)
                link_path = os.path.join(dest_dir, run_type,link_name)
                if not os.path.exists(link_path):
                    os.symlink(file_path, link_path)
                else:
                    print(f"The link already exists: {link_path}")
        
def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def read_run_info(file,dual_barcode):
    
    run_dict = {}
    

    with open(file, mode='r', newline='') as infile:
        reader = csv.reader(infile)
        next(reader)    
        
        for row in reader:
            #remove empty cells & then also check for commas or spaces within cells
            line = [format_cell(cell) for cell in row if format_cell(cell)]

            # check if the barcode is dual indexed if so join these together
            if dual_barcode:
                run_info = '_'.join(line[2:])
                # create a shorter version of the info, to help with file issues (not tested)
                run_info_filename = ''.join(line[2:3] + line[4:])
                barcode = '_'.join(line[:2])
            else:
                run_info = '_'.join(line[1:])
                # create a shorter version of the info, to help with file issues
                run_info_filename = '_'.join(line[1:2] + line[3:])
                barcode = line[0]

            if run_info in run_dict:
                run_dict[run_info].append(barcode)
            else:
                run_dict[run_info] = [run_info_filename, barcode]

    return(run_dict)

    
def format_cell(cell):
# function to format the contents of a cell to fix any issues that might mess with naming
    cell = cell.strip()

    if ',' in cell:
        items = cell.split(',')
        items = [item.strip() for item in items]  # Remove leading/trailing spaces
        cell = ''.join(items)

    if " " in cell:
        cell = cell.replace(" ", "_")

    return cell

def parse_arguments():

    parser = argparse.ArgumentParser(description="Create a Directory Structure for Multi-sequencing runs & link to fastq files")

    parser.add_argument("run_folder", help="Name of the run folder")
    parser.add_argument("run_info_file", help="Path to the run info CSV file")
    parser.add_argument("--dual", action="store_true", help="Flag to indicate dual barcodes")

    return parser.parse_args()
      
if __name__ == "__main__":
    main()
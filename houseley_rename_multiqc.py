#! python

import os
import re 
import sys
import argparse
import csv

# Script to generate rename commands for multiQC reports, based on names pulled from run_info_file.csv - see houseley_group_setup_multirun_structure.py for more on this

def main():
    # read in options from the command line
    options = parse_arguments()

    info_file = options.run_info_file

    if not options.run_info_file.endswith(".csv"):
        parser.error("The run info file must be a CSV file.")

    #set working directory (place directory structure will be made and symlinks will be stored)
    working_dir = os.getcwd()
    
    # create the directory structure in the current working directory
    run_list = read_run_info(info_file)

    # write rename commands
    write_multiqc_rename(run_list)
    
def write_multiqc_rename(run_list):

    with open("rename_multiqc.sh","wt",encoding="utf8") as out:

        for dir in run_list:
            print(f"rename multiqc_report.html {dir}_L001_multiqc_report.html {dir}/multiqc_report.html", file=out)


def read_run_info(file):
    
    run_list = []
    
    with open(file, mode='r', newline='') as infile:
        reader = csv.reader(infile)
        next(reader)    
        
        for row in reader:
            #remove empty cells & then also check for commas or spaces within cells
            line = [format_cell(cell) for cell in row if format_cell(cell)]
            
            if check_if_dual(line[2]):
                dual_barcode = True
            else:
                dual_barcode = False

            # check if the barcode is dual indexed if so join these together
            if dual_barcode:
                dir_name = '_'.join(line[3:])
                barcode = '_'.join(line[1:3])
            else:
                dir_name = '_'.join(line[2:])
                barcode = line[1]
                
            if dir_name not in run_list:
                run_list.append(dir_name)

    return(run_list)

def check_if_dual(second_entry):
    pattern = r'^[CATG]*$'
    
    # Check if the string matches the pattern
    if re.fullmatch(pattern, second_entry):
        return True
    else:
        return False

def format_cell(cell):
# function to format the contents of a cell to fix any issues that might mess with naming
    cell = cell.strip()

    if ',' in cell:
        items = cell.split(',')
        items = [item.strip() for item in items]  # Remove leading/trailing spaces
        cell = '-'.join(items)

    #add a check to remove spaces from cells
    cell = cell.replace(" ", "_")

    #add a check to remove brackets from cells
    cell = cell.replace('(', '').replace(')', '')

    return cell

def parse_arguments():

    parser = argparse.ArgumentParser(description="Create a bash script with rename commands for multiQC reports from Houseley multi-runs")
    parser.add_argument("run_info_file", help="Path to the run info CSV file")

    return parser.parse_args()
      
if __name__ == "__main__":
    main()
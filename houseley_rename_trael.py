#! python

import os
import re 
import sys
import argparse
import csv

# Script to generate rename commands for all trael indexes that need sample names added - based on information in mapping details csv see houseley_group_setup_multirun_structure.py for more on this

def main():

    # read in options from the command line
    options = parse_arguments()

    info_file = options.run_info_file

    if not options.run_info_file.endswith(".csv"):
        parser.error("The run info file must be a CSV file.")

    #set working directory (place directory structure will be made and symlinks will be stored)
    working_dir = os.getcwd()
    
    # create the directory structure in the current working directory
    run_dict = read_run_info(info_file)

    # write rename commands
    write_trael_rename(run_dict)
    
def write_trael_rename(run_dict):

    with open("rename_trael.sh","wt",encoding="utf8") as out:



        for key, value in run_dict.items():
            for index, name in value.items():
                print(f"rename index{index} index{index}_{name} {key}/lane*index{index}*", file=out)


def read_run_info(file):
    
    run_dict = {}
    
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
                
            if "TrAEL" in dir_name and dir_name not in run_dict:
                if dual_barcode:
                    index_names = {key.strip(): value.strip() for key, value in zip(line[6].split("-"), line[7].split("-"))}
                    run_dict[dir_name] = index_names
                else:
                    index_names = {key.strip(): value.strip() for key, value in zip(line[5].split("-"), line[6].split("-"))}
                    run_dict[dir_name] = index_names

    return(run_dict)

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

    parser = argparse.ArgumentParser(description="Create a bash script with rename commands for trael files from Houseley multi-runs")
    parser.add_argument("run_info_file", help="Path to the run info CSV file")

    return parser.parse_args()
      
if __name__ == "__main__":
    main()
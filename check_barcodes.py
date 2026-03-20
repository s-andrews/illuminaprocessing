#!/bin/python3

import subprocess
import os
import mysql.connector
import argparse
from argparse import RawTextHelpFormatter

transtable = str.maketrans("GATC","CTAG")

# can be run from anywhere on the pipeline server
# ~/illuminaprocessing/check_barcodes.py [run_folder] --lane [1/2] > barcode.log

# TODO: Add a note to the log/flag somewhere if seqs have been reverse complemented

#n_fastq_lines = 40000000 # 10 million sequences

parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, description = '''Checks the first 10 million barcodes and runs an R script to create a barcode plot.''')
parser.add_argument('run_folder', type=str, default="", help='run folder name')
parser.add_argument('--lane', type=str, default="1", help='lane number, must be 1 or 2. Default 1')
parser.add_argument('--n_lines', type=int, default="40000000", help='Number of lines of index file to check. Default 40000000 (10 million reads)')
parser.add_argument('--i1_revcomp', default=False, action='store_true', help='Reverse complement the I1 sequence')
parser.add_argument('--i2_revcomp', default=False, action='store_true', help='Reverse complement the I2 sequence')
parser.add_argument('--switch_i1_i2', default=False, action='store_true', help='Swap all I1 seqs for I2 seqs')
parser.add_argument('--barcode_lengthI1', type=int, default=0, help='If barcode length differs from actual length of sequences in the index file(s).')
parser.add_argument('--barcode_lengthI2', type=int, default=0, help='If barcode length differs from actual length of sequences in the index file(s).')
parser.add_argument('--no_sierra_bc', default=False, action='store_true', help='''Do not pull barcodes from Sierra. 
    If this flag is used, a file named expected_barcodes.txt should be present in /Unaligned/Project_External/Sample_laneX in the format bc1,bc2,name''')

args=parser.parse_args()

run_folder = args.run_folder
lane_no = args.lane
no_Sierra_bc = args.no_sierra_bc
I1_revcomp = args.i1_revcomp
I2_revcomp = args.i2_revcomp
n_fastq_lines = int(args.n_lines)
switch_i1_i2 = args.switch_i1_i2
bc_length_i1 = int(args.barcode_lengthI1)
bc_length_i2 = int(args.barcode_lengthI2)

n_seqs = int(n_fastq_lines/4)

#print("First flush... ", flush = True)
#print(f"\n Not flushing... Checking first {n_seqs} reads for expected_barcodes for run folder {run_folder} ")
print(f"\nChecking first {n_seqs} index reads for expected_barcodes for run folder {run_folder} ", flush = True)

def main():

    # quick barcode check
    if no_Sierra_bc:
        exp_bc_file = f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane{lane_no}/expected_barcodes.txt"
        try:
            with open(exp_bc_file, 'r') as bc:
                bc_count = len(bc.readlines())
                print('Total lines:', bc_count)

        except Exception as err:
            print(f"\n !! Couldn't find expected_barcodes.txt file for run folder {run_folder} !!")
            print(err)        
    
    else:
        bc_count = get_expected_barcodes(run_folder, lane_no, switch_i1_i2)

    n_bars_to_check = str(bc_count+10)

    get_barcodes_I1(run_folder, lane_no, I1_revcomp, bc_length_i1)

    I2_file = f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane{lane_no}/lane{lane_no}_NoIndex_L00{lane_no}_I2.fastq.gz"
    if os.path.exists(I2_file):
        dual_coded = True
        get_barcodes_I2(run_folder, lane_no, I2_revcomp, bc_length_i2)
        sort_top_barcodes(run_folder, n_bars_to_check, dual_coded)
    else:
        print("Single indexed library")
        dual_coded = False
        sort_top_barcodes(run_folder, n_bars_to_check, dual_coded)

    try:
        R_cmd = f"Rscript /home/sbsuser/illuminaprocessing/barcode_ggplot.R {run_folder} {n_seqs} {lane_no}"
        print(f"\n Running plotting script with following command: {R_cmd}", flush = True)
        subprocess.run(R_cmd, shell=True, executable="/bin/bash")

    except Exception as err:
        print(f"\n !! Couldn't run barcode plot script barcode_ggplot.R on {run_folder} !!")
        print(err)

    print("\nAll done. \nCheck barcode plot before running the barcode splitting script.\n")

 

#---------------------
# quick barcode check
#---------------------
def get_barcodes_I1(run_folder, lane_no, revcomp, bc_length_i1):

    try:
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane{lane_no}/")

        bc_check_cmd = f"zcat lane{lane_no}_NoIndex_L00{lane_no}_I1.fastq.gz | head -n {n_fastq_lines} | awk 'NR % 4 == 2'"

        if bc_length_i1 > 0:
            print(f"Shortening I1 sequences to {bc_length_i1} bases", flush = True)
            bc_check_cmd = f"{bc_check_cmd} | cut -c 1-{bc_length_i1}"

        if revcomp:
            #bc_check_cmd = f"zcat lane{lane_no}_NoIndex_L00{lane_no}_I1.fastq.gz | head -n {n_fastq_lines} | awk 'NR % 4 == 2' | tr 'ATCG' 'TAGC' | rev > i1_head.txt"
            bc_check_cmd = f"{bc_check_cmd} | tr 'ATCG' 'TAGC' | rev" 
        #else:
        #    bc_check_cmd = f"zcat lane{lane_no}_NoIndex_L00{lane_no}_I1.fastq.gz | head -n {n_fastq_lines} | awk 'NR % 4 == 2' > i1_head.txt"

        bc_check_cmd = f"{bc_check_cmd} > i1_head.txt"

        try:
            subprocess.run(bc_check_cmd, shell=True, executable="/bin/bash")
            
        except Exception as err:
            print("\n !! Couldn't run barcode checking command !!")
            print(err)
            
    except Exception as err:
            print("\n !! Couldn't run barcode checking command !!")
            print(err)


#---------------------
# quick barcode check
#---------------------
def get_barcodes_I2(run_folder, lane_no, revcomp, bc_length_i2):

    try:
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane{lane_no}/")

        bc_check_cmd = f"zcat lane{lane_no}_NoIndex_L00{lane_no}_I2.fastq.gz | head -n {n_fastq_lines} | awk 'NR % 4 == 2'"

        if bc_length_i2 > 0:
            print(f"Shortening I2 sequences to {bc_length_i2} bases", flush = True)
            bc_check_cmd = f"{bc_check_cmd} | cut -c 1-{bc_length_i2}"

        if revcomp:
            bc_check_cmd = f"{bc_check_cmd} | tr 'ATCG' 'TAGC' | rev" 

        bc_check_cmd = f"{bc_check_cmd} > i2_head.txt"
        
        #if revcomp:
        #    bc_check_cmd = f"zcat lane{lane_no}_NoIndex_L00{lane_no}_I2.fastq.gz | head -n {n_fastq_lines}  | awk 'NR % 4 == 2' | tr 'ATCG' 'TAGC' | rev > i2_head.txt"    
        #else:
        #    bc_check_cmd = f"zcat lane{lane_no}_NoIndex_L00{lane_no}_I2.fastq.gz | head -n {n_fastq_lines}  | awk 'NR % 4 == 2' > i2_head.txt"    

        try:
            subprocess.run(bc_check_cmd, shell=True, executable="/bin/bash")
            
        except Exception as err:
            print("\n !! Couldn't run barcode checking command !!")
            print(err)
            
    except Exception as err:
        print("\n !! Couldn't run barcode checking command !!")
        print(err)


#---------------------
# sort top barcodes
#---------------------
def sort_top_barcodes(run_folder, n_bars_to_check, dual_coded):

    try:
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane{lane_no}/")

        if dual_coded:
            bc_sort_cmd = f"paste -d '_' i1_head.txt i2_head.txt | sort | uniq -c | sort -k 1 -n -r | head -n {n_bars_to_check} | sed 's/^\s*//' > found_barcodes.txt"
        else:
            bc_sort_cmd = f"sort i1_head.txt | uniq -c | sort -k 1 -n -r | head -n {n_bars_to_check} | sed 's/^\s*//' > found_barcodes.txt"

        try:
            subprocess.run(bc_sort_cmd, shell=True, executable="/bin/bash")
            
        except Exception as err:
            print("\n !! Couldn't run barcode sorting command !!")
            print(err)
            
    except Exception as err:
        print("\n !! Couldn't run barcode sorting command !!")
        print(err)

# This writes out the expected barcodes to a text file and returns the number of expected barcodes.
# The text file is used in the R script.
def get_expected_barcodes(run_folder, lane_no, switch_i1_i2):

    try:
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane{lane_no}/")

        cnx = mysql.connector.connect(user='sierrauser', password='', host='bilin2.babraham.ac.uk', database='sierra')
        cursor = cnx.cursor()

        query = (
            f"select barcode.5_prime_barcode,barcode.3_prime_barcode,barcode.name from run,flowcell,lane,barcode "
            f"WHERE run.run_folder_name = '{run_folder}' and run.flowcell_id=flowcell.id AND run.flowcell_id=lane.flowcell_id "
            f"AND lane.lane_number={lane_no} AND lane.sample_id = barcode.sample_id"
        )

        cursor.execute(query)
        barcode1_count=0

        expected_barcodes = open("expected_barcodes.txt", "w")

        for (row) in cursor:
            print(row)

            if switch_i1_i2:
                expected_barcodes.write(f"{row[1]},{row[0]},{row[2]}\n")

            else: 
                expected_barcodes.write(f"{row[0]},{row[1]},{row[2]}\n")
            
            barcode1_count+=1

        expected_barcodes.close()
        cnx.close()

        return(barcode1_count)
        
    except Exception as err:
        print("\n !! Couldn't get expected barcodes !!")
        print(err)



if __name__ == "__main__":
    main()

#!/bin/python3

import subprocess
import os
import mysql.connector
import argparse
from argparse import RawTextHelpFormatter

# currently needs to be run from /data/AV240405
# we might move to running it from /data when we make it compatible with MiSeq as well.
# nohup ~/illuminaprocessing/process_aviti.py [run_folder] > xx.log &

# barcode checking only works for lane1 at the moment

n_fastq_lines = 4000000 # 1 million sequences

parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, description = '''For initial processing of AVITI data - this runs bases2fastq, 
copies fastq files to /primary, checks the first million barcodes and runs an R script to create a barcode plot.''')
parser.add_argument('run_folder', type=str, default="", help='run folder name')
parser.add_argument('--ignore_R2', default=False, action='store_true', help='To only use R1 cycles. Default [False]')
parser.add_argument('--split_lanes', default=False, action='store_true', help='If lane1 and lane2 need to be kept separate. Cannot currently be used with --ignore_R2. Default [False]')

args=parser.parse_args()

run_folder = args.run_folder
ignore_R2 = args.ignore_R2
split_lanes = args.split_lanes

def main():

    run_bases2fastq(run_folder)

    # rename fastq files to be Sierra compatible
    rename_fastqs(run_folder)

    # create directry structure on /primary
    create_dirs_primary(run_folder)

    # copy fastq files to /primary
    cp_to_primary(run_folder)
    print(f"fastq files have been copied to /primary/{run_folder}....")

    # quick barcode check
    barcode1_count = get_expected_barcodes(run_folder)
    n_bars_to_check = str(barcode1_count+10)

    get_barcodes_I1(run_folder)

    I2_file = f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane1/lane1_NoIndex_L001_I2.fastq.gz"
    if os.path.exists(I2_file):
        dual_coded = True
        get_barcodes_I2(run_folder)
        sort_top_barcodes(run_folder, n_bars_to_check, dual_coded)
    else:
        print("Single indexed library")
        dual_coded = False
        sort_top_barcodes(run_folder, n_bars_to_check, dual_coded)

    try:
        R_cmd = f"Rscript /home/sbsuser/illuminaprocessing/barcode_ggplot.R {run_folder}"
        subprocess.run(R_cmd, shell=True, executable="/bin/bash")

    except Exception as err:
        print(f"\n !! Couldn't run barcode plot script barcode_ggplot.R on {run_folder} !!")
        print(err)

    print("\nAll done. \nCheck barcode plot before running the barcode splitting script.\n")


#--------------------------------
# run_bases2fastq for AVITI data
#--------------------------------

def run_bases2fastq(run_folder):

    try:
        if os.path.exists(run_folder):
            if os.path.exists(f"{run_folder}/RunUploaded.json"):
                # currently running this from within the AV240405 folder
                print(f"running bases2fastq on run_folder = {run_folder} .........")
            else:
                print(f"\n !! Couldn't find RunUploaded.json in {run_folder}. !! \n    Exiting...\n")    
                exit()
        else:
            print(f"\n !! Couldn't find run folder {run_folder}. Valid run folder required !! \n    Exiting...\n")
            exit()

        if split_lanes:
            bases2fastq_cmd = f"bases2fastq -p 16 --split-lanes --run-manifest ~/illuminaprocessing/aviti_run_manifest.csv {run_folder} {run_folder}/Unaligned"
        elif ignore_R2:
            # do we really need --r2-cycles and a custom manifest?
            bases2fastq_cmd = f"bases2fastq -p 16 --r2-cycles 0 --run-manifest ~/illuminaprocessing/aviti_run_manifest_exclude_R2.csv {run_folder} {run_folder}/Unaligned"
        else: 
            bases2fastq_cmd = f"bases2fastq -p 16 --run-manifest ~/illuminaprocessing/aviti_run_manifest.csv {run_folder} {run_folder}/Unaligned"
        
        print(bases2fastq_cmd)
        subprocess.run(bases2fastq_cmd, shell=True, executable="/bin/bash")
        
    except Exception as err:
        print(f"\n !! Couldn't run bases2fastq on {run_folder} !!")
        print(err)


#--------------------------------------------
# rename fastq files to be Sierra compatible
#--------------------------------------------
def rename_fastqs(run_folder):
    try:
        os.chdir(run_folder) 

        if split_lanes:
            rename_cmd1 = "rename DefaultSample_ lane1_NoIndex_ Unaligned/Samples/DefaultProject/DefaultSample/*L001*fastq.gz"        
            subprocess.run(rename_cmd1, shell=True, executable="/bin/bash")
            rename_cmd2 = "rename DefaultSample_ lane2_NoIndex_ Unaligned/Samples/DefaultProject/DefaultSample/*L002*fastq.gz"
            subprocess.run(rename_cmd2, shell=True, executable="/bin/bash")
            rename_cmd3 = "rename _001.fastq .fastq Unaligned/Samples/DefaultProject/DefaultSample/*fastq.gz"	
            subprocess.run(rename_cmd3, shell=True, executable="/bin/bash")
        else:
            rename_cmd = "rename DefaultSample_ lane1_NoIndex_L001_ Unaligned/Samples/DefaultProject/DefaultSample/*fastq.gz"
            subprocess.run(rename_cmd, shell=True, executable="/bin/bash")

    except Exception as err:
        print(f"\n !! Couldn't move to {run_folder}. Valid run_folder required !!")
        print(err)


#----------------------------------------
# create directory structure on /primary
#----------------------------------------
def create_dirs_primary(run_folder):

    try:
        os.chdir("/primary")
        if os.path.exists(run_folder):
            print(f"\n !! run folder {run_folder} already exists in /primary, exiting... !!")
            exit()
        else: 
            mkdir_cmd = f"mkdir {run_folder}"
            subprocess.run(mkdir_cmd, shell=True, executable="/bin/bash")
            os.chdir(run_folder)

            if split_lanes:
                subprocess.call("/home/sbsuser/illuminaprocessing/create_external_run_folder_structure_2_lanes.sh")
            else:
                subprocess.call("/home/sbsuser/illuminaprocessing/create_external_run_folder_structure_1_lane.sh")

    except Exception as err:
        print("\n !! Couldn't create file structure on /primary !!")
        print(err)
        exit()

   
#------------------------------
# copy fastq files to /primary
#------------------------------
def cp_to_primary(run_folder):

    try:
        os.chdir(f"/primary/{run_folder}")
        cp_cmd = f"cp /data/AV240405/{run_folder}/Unaligned/Samples/DefaultProject/DefaultSample/*L001*fastq.gz Unaligned/Project_External/Sample_lane1/ > copy.log"
        print(f"\nCopying fastq files from {run_folder} to /primary. This may take a while.........\n") 
        subprocess.run(cp_cmd, shell=True, executable="/bin/bash")

        if split_lanes:
            cp_cmd2 = f"cp /data/AV240405/{run_folder}/Unaligned/Samples/DefaultProject/DefaultSample/*L002*fastq.gz Unaligned/Project_External/Sample_lane2/ >> copy.log"
            subprocess.run(cp_cmd2, shell=True, executable="/bin/bash")

    except Exception as err:
        print(f"\n !! Couldn't copy fastqs from /data to /primary{run_folder} !!")
        print(err)
        exit()


#---------------------
# quick barcode check
#---------------------
def get_barcodes_I1(run_folder):

    try:
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane1/")
        bc_check_cmd = f"zcat lane1_NoIndex_L001_I1.fastq.gz | head -n {n_fastq_lines} | awk 'NR % 4 == 2' > i1_head.txt"

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
def get_barcodes_I2(run_folder):

    try:
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane1/")
        bc_check_cmd = f"zcat lane1_NoIndex_L001_I2.fastq.gz | head -n {n_fastq_lines}  | awk 'NR % 4 == 2' > i2_head.txt"    

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
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane1/")

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
def get_expected_barcodes(run_folder):

    try:
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane1/")

        cnx = mysql.connector.connect(user='sierrauser', password='', host='bilin2.babraham.ac.uk', database='sierra')
        cursor = cnx.cursor()

        # lane_number will always be 1 for aviti and miseq
        query = (f"select barcode.5_prime_barcode,barcode.3_prime_barcode,barcode.name from run,flowcell,lane,barcode WHERE run.run_folder_name = '{run_folder}' and run.flowcell_id=flowcell.id AND run.flowcell_id=lane.flowcell_id AND lane.lane_number=1 AND lane.sample_id = barcode.sample_id")

        cursor.execute(query)
        barcode1_count=0

        expected_barcodes = open("expected_barcodes.txt", "w")

        for (row) in cursor:
            print(row)
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

#!/bin/python3

import subprocess, sys, os
import mysql.connector

# currently needs to be run from /data/AV240405
# Usually, we only get one lane of data from each run folder on the AVITI, but you can get 2.
 
# This then means the data needs to be processed slightly differently. We need L001 and L002.
# I've commented out the barcode checking part for now.
# nohup ~/illuminaprocessing/process_aviti.py [run_folder] > xx.log &


def main():

    run_folder = sys.argv[1]

    run_bases2fastq(run_folder)

    # rename fastq files to be Sierra compatible
    rename_fastqs(run_folder)

    # create directry structure on /primary
    create_dirs_primary(run_folder)

    # copy fastq files to /primary
    cp_to_primary(run_folder)
    print(f"fastq files have been copied to /primary/{run_folder}....")

    # quick barcode check
#    barcode1_count = get_expected_barcodes(run_folder)
#    n_bars_to_check = str(barcode1_count+2)

#    get_barcodes_I1(run_folder, n_bars_to_check)

#    I2_file = f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane1/lane1_NoIndex_L001_I2.fastq.gz"
#    if os.path.exists(I2_file):
#        get_barcodes_I2(run_folder, n_bars_to_check)
#    else:
#        print("Single indexed library")

#    print(f"\nAll done. \nExpected barcodes have been written out to a file - check these before running the barcode splitting script.\n")

    print(f"\nAll done.")

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

        bases2fastq_cmd = f"bases2fastq -p 16 --split-lanes --run-manifest ~/illuminaprocessing/aviti_run_manifest.csv {run_folder} {run_folder}/Unaligned"
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
        rename_cmd1 = "rename DefaultSample_ lane1_NoIndex_ Unaligned/Samples/DefaultProject/DefaultSample/*L001*fastq.gz"
        rename_cmd2 = "rename DefaultSample_ lane2_NoIndex_ Unaligned/Samples/DefaultProject/DefaultSample/*L002*fastq.gz"
        subprocess.run(rename_cmd1, shell=True, executable="/bin/bash")
        subprocess.run(rename_cmd2, shell=True, executable="/bin/bash")

        rename_cmd3 = "rename _001.fastq .fastq Unaligned/Samples/DefaultProject/DefaultSample/*fastq.gz"	
        subprocess.run(rename_cmd3, shell=True, executable="/bin/bash")

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
            subprocess.call("/home/sbsuser/illuminaprocessing/create_external_run_folder_structure_2_lanes.sh")

    except Exception as err:
        print(f"\n !! Couldn't create file structure on /primary !!")
        print(err)
        exit()

   
#------------------------------
# copy fastq files to /primary
#------------------------------
def cp_to_primary(run_folder):

    try:
        os.chdir(f"/primary/{run_folder}")
        cp_cmd1 = f"cp /data/AV240405/{run_folder}/Unaligned/Samples/DefaultProject/DefaultSample/*L001*fastq.gz Unaligned/Project_External/Sample_lane1/ > copy.log"
        print(f"\nCopying fastq files from {run_folder} to /primary. This may take a while.........\n") 
        cp_cmd2 = f"cp /data/AV240405/{run_folder}/Unaligned/Samples/DefaultProject/DefaultSample/*L002*fastq.gz Unaligned/Project_External/Sample_lane2/ >> copy.log"
        subprocess.run(cp_cmd1, shell=True, executable="/bin/bash")
        subprocess.run(cp_cmd2, shell=True, executable="/bin/bash")
    except Exception as err:
        print(f"\n !! Couldn't copy fastqs from /data to /primary{run_folder} !!")
        print(err)
        exit()


#---------------------
# quick barcode check
#---------------------
def get_barcodes_I1(run_folder, n_bars_to_check):

    try:
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane1/")

        bc_check_cmd = f"zcat lane1_NoIndex_L001_I1.fastq.gz | head -n 400000 | awk 'NR % 4 == 2' | sort | uniq -c | sort -k 1 -n -r | head -n {n_bars_to_check} | awk '{{$1=$1;print}}' | tr ' ' '\t' > found_barcodes_L001_I1.txt"

        try:
            subprocess.run(bc_check_cmd, shell=True, executable="/bin/bash")
            
        except Exception as err:
            print(f"\n !! Couldn't run barcode checking command !!")
            print(err)
            
    except Exception as err:
            print(f"\n !! Couldn't run barcode checking command !!")
            print(err)


#---------------------
# quick barcode check
#---------------------
def get_barcodes_I2(run_folder, n_bars_to_check):

    try:
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane1/")
        bc_check_cmd = f"zcat lane1_NoIndex_L001_I2.fastq.gz | head -n 100000 | awk 'NR % 4 == 2' | sort | uniq -c | sort -k 1 -n -r | head -n {n_bars_to_check} | awk '{{$1=$1;print}}' | tr ' ' '\t' > found_barcodes_L001_I2.txt"

        try:
            subprocess.run(bc_check_cmd, shell=True, executable="/bin/bash")
            
        except Exception as err:
            print(f"\n !! Couldn't run barcode checking command !!")
            print(err)
            
    except Exception as err:
        print(f"\n !! Couldn't run barcode checking command !!")
        print(err)


# This writes out the expected barcodes to a text file and returns the number of expected barcodes.
# We only really need the number of expected barcodes for now while we're just doing a quick check.
def get_expected_barcodes(run_folder):

    try:
        os.chdir(f"/primary/{run_folder}/Unaligned/Project_External/Sample_lane1/")

        cnx = mysql.connector.connect(user='sierrauser', password='', host='bilin2.babraham.ac.uk', database='sierra')
        cursor = cnx.cursor()

        # lane_number will always be 1 for aviti and miseq
        query = (f"select barcode.5_prime_barcode,barcode.3_prime_barcode,barcode.name from run,flowcell,lane,barcode WHERE run.run_folder_name = '{run_folder}' and run.flowcell_id=flowcell.id AND run.flowcell_id=lane.flowcell_id AND lane.lane_number=1 AND lane.sample_id = barcode.sample_id")

        cursor.execute(query)
        barcode1_count=0

        expected_barcodes = open("expected_barcodes_L001_1.txt", "w")

        for (row) in cursor:
            print(row)
            expected_barcodes.write(f"{row[0]},{row[1]},{row[2]}\n")
            barcode1_count+=1

        expected_barcodes.close()
        cnx.close()

        return(barcode1_count)
        
    except Exception as err:
        print(f"\n !! Couldn't get expected barcodes !!")
        print(err)



if __name__ == "__main__":
    main()

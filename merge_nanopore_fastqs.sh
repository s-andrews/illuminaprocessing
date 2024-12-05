#!/bin/sh
# for merging all the fastq files for a barcode - assuming the files are named xxxxx_123.fastq.gz
# we can't just cat them in ls order as they don't order numerically - they're 0,1,10,11,12 etc

#==============================
# Run this from the location that we want the merged files to be written to
# The only argument to pass in is the folder name i.e. fastq_pass or fastq_fail
# The script will expect folders inside barcode01, barcode02 etc plus unclassified
#==============================

# add in _L001_

top_folder="$1"
if [ -d $top_folder ]
then 
    echo -e "Looking in folder $top_folder\n "
else
    echo -e "\n!! Couldn't find folder $top_folder, exiting...\n"
    exit 1
fi

log_file=${top_folder}_merge.log
barcode_folders=$top_folder/barcode*
#barcode_folders=$top_folder/*  # if we also want the unclassified

echo -e "Writing log to $log_file\n"

for barcode_folder in $barcode_folders
    do
        #echo -e "\nLooking in barcode folder $barcode_folder... "
        for i in $barcode_folder/*fastq.gz
            # extract the file numbers so that we can get the highest and lowest numbers
            do echo $i | sed -nE 's/.*_([0-9]+)\.fastq.gz/\1/p'; done | sort -nr > all_nos.txt
        last_no=$(head -n 1 all_nos.txt)
        first_no=$(tail -n 1 all_nos.txt)
        if [ $last_no -eq 0 ]
        then
            #echo -e "Only 1 fastq file found for $barcode_folder so we're just making a symlink"
            echo -e "Only 1 fastq file found for $barcode_folder so not merging these"
            #only_file=$(ls $barcode_folder/*fastq.gz)
            # remove the folder structure from the filename so we write into the directory the script is run from
            #base_for_symlink=${only_file##*/}
            
            #ln -s $only_file $base_for_symlink
        else
            # extract the file name so we can use it to create a new merged file name
            merged_long=$(ls ${barcode_folder}/*_${first_no}.fastq.gz | sed -nE 's/(.*)_[0-9]+\.fastq.gz/\1/p')
            # remove the folder structure from the filename so we write into the directory the script is run from
            base_merged=${merged_long##*/}            
            merged_file=${base_merged}_L001_merged.fastq.gz

            echo -e "Merging fastq files $first_no to $last_no from $barcode_folder and writing out to $merged_file"
            for j in $(seq $first_no $last_no) ; do cat ${barcode_folder}/*_${j}.fastq.gz >> $merged_file ; done
        fi
done

# we get a warning written out if there are missing files in the sequence but it still seems to work ok.

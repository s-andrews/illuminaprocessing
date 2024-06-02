#!/bin/bash

############## Read In options & Initial Checks ############## 
Help() { 
   echo -e "\nUsage: $0 [-h] [-u URL] [-m]"
   echo "This script is intended to handle the initial processing of Novogene data. It can either work from the link to the data, the zipped data, or the unzipped data."
   echo "If necessary, data will be downloaded / unzipped. Then the samples present will be checked (based on the directory names the fastq files are in) to see if any merges of fastq files are needed."
   echo "This script returns: a log file with details of the dataset processing (*_initial_processing_info.txt), and files with commands to cp or cat the fastq files (cp_commands.sh and/or merge_commands.sh)."
   echo "The script must be run from the directory you want to process the data in."
   echo
   echo "Options:"   
   echo "  h     Print this Help."
   echo "  u     Provide a URL for download (must start with https://)."
   echo "  m     Enable MD5 checksum verification."
   echo
}

# Default values
md5_check=false

while getopts "hu:m" flag; do
   case ${flag} in
      h) Help
         exit 0;;
      u)   
        if [[ $OPTARG =~ ^https:// ]]; then
            url=$OPTARG
        else
            echo "Error: URL provided did not start with https://"
            exit 1
        fi
        ;;
      m)
        md5_check=true
        ;;
      \?) echo "Error: Invalid option"
          exit 1;;
      :)
        echo "Invalid option: -$OPTARG requires an argument"
        exit 1;;  
   esac
done

shift $((OPTIND -1))


############## Set Other Variables ##############
dir_path=$(pwd -P)
dir_name=$(basename "${dir_path}")
processing_info_file="${dir_name}_initial_processing_info.txt"

run_type="Single End"
sample_names=()
file_dir_paths=()

###################################################################################################
########################################## Main ################################################### 
###################################################################################################

###################################################################################################
############################# Write out some general processing info ##############################

section_title=$(printf "#%.0s" $(seq 1 40))" General Info on Novogene Run Processing "$(printf "#%.0s" $(seq 1 40))
printf "%s\n" "$section_title" > "${processing_info_file}"

# What directory are we processing
printf "%s\t%s\n" "Processing:" "${dir_name}" >> "${processing_info_file}"

#### Download the Data if needed #####
section_title=$(printf "#%.0s" $(seq 1 40))" Checking for Download link "$(printf "#%.0s" $(seq 1 40))

printf "\n%s\n" "$section_title" >> "${processing_info_file}"

if [[ -n $url ]]; then
    echo "Downloading from URL: $url" >> "${processing_info_file}"
    
    if wget "$url"; then
        echo "Download successful." >> "${processing_info_file}"
    else
        echo "Failed to download the file." >> "${processing_info_file}"
        return 1
    fi
else
    echo "No download link provided" >> "${processing_info_file}"
fi

###################################################################################################
###################################### Unzip directories if needed ################################

section_title=$(printf "#%.0s" $(seq 1 40))" Checking for Zipped Directories "$(printf "#%.0s" $(seq 1 40))

printf "\n%s\n" "$section_title" >> "${processing_info_file}"

#look for tar files
zip_files=$(find "$dir_path" -type f -regex ".*X[0-9]+SC[0-9]+-Z[0-9]+-F[0-9]+\.tar")

if [[ -z "$zip_files" ]];then

    printf "%s\n" "No zip files found" >> "${processing_info_file}"

else
    while read -r file; do

        zip_dir=$(basename "$file")
        printf "%s\t%s\n" "Unzipping:" "${zip_dir}" >> "${processing_info_file}"

        if tar -xf "${file}"; then
            printf "%s\t%s\n" "Successfully unzipped:" "${zip_dir}" >> "${processing_info_file}"
        else
            printf "%s\t%s\n" "Failed to unzip:" "${zip_dir}" >> "${processing_info_file}"
            exit 1
        fi

    done <<< "$zip_files"
fi

##################################################################################################
####################################### Find Unique Sample Names #################################

# This expects a structure where all the fastq files belonging to a given sample are stored within
# a single directory with that unique samples name 
# This is the structure that we reliably get directly from Novogene,
# and also when data has been downloaded to an external disk.

while read -r file; do
    sample_name=$(basename "$(dirname "$file")")
    sample_names+=("$sample_name")

    file_dir_path=$(dirname "$file")
    file_dir_paths+=("$file_dir_path")

done < <(find "$dir_path" -type f -name "*.fq.gz")

#remove any duplicates sample names
mapfile -t unique_sample_names < <(printf "%s\n" "${sample_names[@]}" | sort -u)
mapfile -t unique_file_dir_paths < <(printf "%s\n" "${file_dir_paths[@]}" | sort -u)


###################################################################################################
###################################### Optional Perform MD5 Check #################################

# After unzipping, perform MD5 checksum verification if enabled
if [[ "$md5_check" == true ]]; then
    section_title=$(printf "#%.0s" $(seq 1 40))" MD5 Checksum Verification "$(printf "#%.0s" $(seq 1 40))
    printf "\n%s\n" "$section_title" >> "${processing_info_file}"

    MD5_names=()
    count_checksums=0
    all_found="yes"
    all_match="yes"

    # Then can use this to find all the md5 files within sample directories (because there is one in 01.RawData)
    for sample_dir in "${unique_sample_names[@]}"; do
        while read -r file; do
            MD5_names+=("$file")
        done < <(find "$dir_path" -type f -wholename "*${sample_dir}/MD5.txt")
    done

    # Now check each filename
    for MD5_file in "${MD5_names[@]}"; do
        while IFS= read -r line; do
            # Extract the checksum and filename
            checksum=$(echo "$line" | awk '{print $1}')
            filename=$(echo "$line" | awk '{print $2}')
            echo "$checksum"
            echo "$filename"
            # extract the dirname for the MD5 file - this should also be the same for the file
            MD5_path=$(dirname "$MD5_file")
            fq_file="${MD5_path}/${filename}"

            # check if file exists
            if [[ -f "$fq_file" ]]; then
                # Calculate the md5 checksum of the file
                calculated_checksum=$(md5sum "$fq_file" | awk '{print $1}')
                (( count_checksums+=1 ))
                # compare the checksums
                if [[ "$checksum" == "$calculated_checksum" ]]; then
                    echo "Checksum matches for file: $filename" >> "${processing_info_file}"
                else
                    echo "Checksum does NOT match for file: $filename" >> "${processing_info_file}"
                    all_match="no"
                fi
            else
                echo "File not found: $filename" >> "${processing_info_file}"
                all_found="no"
                all_match="no"
            fi

        done < "$MD5_file"
    done 

    #count_checksums=$(grep -cE "^[0-9a-fA-F]{32}\s+\S+" "${processing_info_file}")
    count_fq_files=${#sample_names[@]}

    printf "\n%s\n" "Summary of Checksums for ${dir_path}" >> "${processing_info_file}"

    if [ "$count_checksums" == "$count_fq_files" ]; then
        printf "\n%s\n%s\t%s\n" "Number of Checksums matches Number of .fq.gz Files" "Files: ${count_fq_files}" "Checksums: ${count_checksums}" >> "${processing_info_file}"
    else
        printf "\n%s\n%s\t%s\n" "Number of Checksums does not match Number of Files" "Files: ${count_fq_files}" "Checksums: ${count_checksums}" >> "${processing_info_file}"
    fi

    if [ "$all_found" == "yes" ]; then
        printf "\n%s\n" "All Checksum files were found" >> "${processing_info_file}"
    else
        printf "\n%s\n" "Not All Checksum files were found" >> "${processing_info_file}"
    fi

    if [ "$all_match" == "yes" ]; then
        printf "%s\n" "All Checksums matched" >> "${processing_info_file}"
    else
        printf "%s\n" "Not All Checksums matched" >> "${processing_info_file}"
    fi
fi

###################################################################################################
################################ Write out cp/cat commands ########################################
##### Write out commands for merging files with the same base sample names / copying commands #####

for sample in "${unique_sample_names[@]}";do

    ###### check whether the files are paired end, if so then write out commands for R2 files also ######
    mapfile -t run_end < <(find "${dir_path}" -type f -wholename "*${sample}/*.fq.gz" -printf "%f\n" | rev |cut -c 7 | sort -u)

    if [ ${#run_end[@]} == 2 ];then
        run_type="Paired End"
    fi
    
    ##### Write out the commands:
    
    ##### create an ouput name 
    out_filename="${sample}""_L001_R1.fastq.gz"

    ###### find all the files associated with the sample name 
    mapfile -t fastq_names < <( find "$dir_path" -type f -name "*${sample}*1.fq.gz")

    # Check if there is more than 1 file
    # if yes, provide a command to merge all the files (saved in merge_commands.sh)
    if  (( ${#fastq_names[@]} > 1 ))
    then
        #if the output file hasn't been made yet, make it
        if [[ ! -f "merge_commands.sh" ]]; then
                echo "#!/bin/bash" > merge_commands.sh
            fi
    # If more than 1 file then give instructions for merging
    read_1_command=$(printf "%s %s %s" "cat" "${fastq_names[*]}" "> ${dir_path}/${out_filename}")
    #echo "ssub -c 1 -m 5G --email -o ${out_filename} cat" "${fastq_names[@]}" >> merge_commands.sh
    echo "$read_1_command" >> merge_commands.sh
    
    # check from run-type variable provided if this is a paired end run, if so write out a R2 command also
        if [ "$run_type" == "Paired End" ]; then
            read_2_command="${read_1_command//1.fastq.gz/2.fastq.gz}"
            read_2_command="${read_2_command//1.fq.gz/2.fq.gz}"
            echo "$read_2_command" >> merge_commands.sh
        fi

    # if not, provide a command to cp the file (saved in cp_commands.sh)
    else
        #if the output file hasn't been made yet, make it
        if [[ ! -f "cp_commands.sh" ]]; then
            echo "#!/bin/bash" > cp_commands.sh
        fi
        #  again check from run-type variable provided if this is a paired end run, if so write out a R2 command also
        read_1_command=$(printf "%s %s %s" "cp" "${fastq_names[*]}" "${dir_path}/${out_filename}")
        echo "$read_1_command" >> cp_commands.sh

        if [ "$run_type" == "Paired End" ]; then
            read_2_command="${read_1_command//1.fastq.gz/2.fastq.gz}"
            read_2_command="${read_2_command//1.fq.gz/2.fq.gz}"
            echo "$read_2_command" >> cp_commands.sh
        fi

    fi   
done

##################################################################################
##### Write out some general processing info on the fq files & Samples found #####

section_title=$(printf "#%.0s" $(seq 1 40))" Details of Fq Files "$(printf "#%.0s" $(seq 1 40))

printf "\n%s\n" "$section_title" >> "${processing_info_file}"

# files are se/pe
printf "%s\t%s\n" "Run is:" "${run_type}" >> "${processing_info_file}"

# How many files are there
printf "%s\t%s\n" "Total No Files (*fq.gz):" "${#file_dir_paths[@]}" >> "${processing_info_file}"

# How many Unique Samples are there
printf "%s\t%s\n" "Total No. Unique Sample Names:" "${#unique_sample_names[@]}" >> "${processing_info_file}"

# Are there any Duplicated Sample Names
#normally would expect sample names to be unique, however might not be (had a case where same samples run on two flowcells, rather than lanes of same flowcell)
#Therefore flag a warning for the general file if there are sample names that are not unique in the directory (as with current approach all fastq files for that sample names will all be merged)

section_title=$(printf "#%.0s" $(seq 1 40))" Check Duplicated Sample Names "$(printf "#%.0s" $(seq 1 40))
printf "\n%s\n" "$section_title" >> "${processing_info_file}"

printf "\n%s\n" "fq files may be technically duplicated if run on multiple lanes" >> "${processing_info_file}"
printf "%s\n" "sample names (based on directory names) should be unique - unless told otherwise" >> "${processing_info_file}"
printf "%s\n" "any duplicate fq files associated with a sample name will be merged" >> "${processing_info_file}"

if [ ${#unique_sample_names[@]} == ${#unique_file_dir_paths[@]} ];then
    printf "\n%s\n" "There are no Duplicated Sample Names" >> "${processing_info_file}"
else
    printf "\n%s\n" "WARNING There are some Duplicated Sample Names" >> "${processing_info_file}"
fi

printf "%s\t%s\t%s\n" "Sample Names Found" "No. Directories" "No. fq.gz files" >> "${processing_info_file}"
    for sample in "${unique_sample_names[@]}"; do

        count_dir=$(grep -o "$sample" <<< ${unique_file_dir_paths[*]} | wc -l)
        count_file=$(grep -o "$sample" <<< ${file_dir_paths[*]} | wc -l)

        printf "%s\t%s\t%s\n" "${sample}" "${count_dir}" "${count_file}" >> "${processing_info_file}"
    done

printf "\n%s\n" "*Note if run is PE then both R1 & R2 are counted for fq files" >> "${processing_info_file}"

# Finally check the number of commands is equal to the number of unique sample names

section_title=$(printf "#%.0s" $(seq 1 40))" Check Commands "$(printf "#%.0s" $(seq 1 40))
printf "\n%s\n" "$section_title" >> "${processing_info_file}"

# First see if we have generated any commands for cat, then count how many if so
if [[ -f "merge_commands.sh" ]]; then 
    count_cat=$(wc -l < merge_commands.sh)
    count_cat=$(( count_cat -1))
    printf "\n%s\n" "merge_commands.sh contains commands to merge technical duplicates of fq files" >> "${processing_info_file}"
    printf "%s\t%s\n" "Merge command count:" "${count_cat}" >> "${processing_info_file}"
else
    printf "\n%s\n" "merge_commands.sh does not exits, there are no technical duplicates of fq files to merge" >> "${processing_info_file}"
    count_cat=0
fi

# Next see if we have generated any commands for cp, then count how many if so
if [[ -f "cp_commands.sh" ]]; then 
    count_cp=$(wc -l < cp_commands.sh)
    count_cp=$(( count_cp -1))
    printf "\n%s\n" "cp_commands.sh contains commands to cp unduplicated fq files" >> "${processing_info_file}"
    printf "%s\t%s\n" "Copy command count:" "${count_cp}" >> "${processing_info_file}"
else
    printf "\n%s\n" "cp_commands.sh does not exits, there are no files to be copied" >> "${processing_info_file}"
    count_cp=0
fi

# Now calculate how many commands we have vs how many we would expect
# Expect a command for each unique sample name, 2 if the data is paired end
expected_commands=${#unique_sample_names[@]}
if [ "$run_type" == "Paired End" ];then
expected_commands=$(( expected_commands * 2))
fi

if [ $(( count_cat + count_cp )) == "$expected_commands" ]; then
    printf "\n%s\n" "There are the right number of commands generated for the number of unique samples" >> "${processing_info_file}"
else
    printf "\n%s\n" "SOMETHING HAS GONE WRONG the number of commands generated does not equal number of unique samples" >> "${processing_info_file}"
fi

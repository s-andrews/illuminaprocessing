#!/usr/bin/env python3

from pathlib import Path
import argparse
import datetime

# This script is used to clean up data from sequencing run folders which is no
# longer required. We initially generate a lot of data from folders which are
# intermediate files from data processing.  After some time these files can 
# be removed because they are no longer likely to be used directly and they 
# could be regenerated if they were ever needed in future.  By doing this we
# can dramatically reduce the total amount of data we store.

options = None
delfh = None
stats = {
    "QC":[0,0],
    "LostReads": [0,0],
    "CellRangerTar": [0,0],
    "BismarkCallFiles": [0,0],
    "BismarkDedup": [0,0],
    "Unassigned": [0,0],
    "Unsplit": [0,0],
    "Trimmed": [0,0],
    "ONTRaw": [0,0]
}

def main():

    global options
    options = get_options()


    if options.delfile:
        global delfh
        delfh = open(options.delfile,"wt", encoding="utf8")

    folders = list_folders("/primary")

    print(f"Found {len(folders)} folders to process")

    for i,folder in enumerate(folders):
        print("Processing",folder.name,(i+1),"out of",len(folders), flush=True)
        process_folder(folder)

    print_stats()

    if delfh:
        delfh.close()


def print_stats():

    total_size = 0
    total_files = 0

    for stat in stats:
        amount = stats[stat][1]
        total_size += amount
        total_files += stats[stat][0]
        
        amount_string = make_file_size(amount)

        stats[stat].append(amount_string)


    print("Total Savings\n=============\n\n")

    print(f"{'File Type':<18} {'File Num':<10} {'File Size':>14}")
    print(f"{'-'*15:<18} {'-'*10:<10} {'-'*10:>14}")

    for stat in sorted(stats.keys(), key=lambda x: stats[x][1], reverse=True):
        print(f"{stat:<18} {stats[stat][0]:<10,} {stats[stat][2]:>14}")

    print("\n")
    print(f"{'='*15:<18} {'='*10:<10} {'='*10:>14}")
    print("\n")
    print(f"{'TOTAL':<18} {total_files:<10,} {make_file_size(total_size):>14}")

def make_file_size(amount):
    unit = "B"

    if amount > 1024:
        amount /= 1024
        unit="kB"

    if amount > 1024:
        amount /= 1024
        unit="MB"
    
    if amount > 1024:
        amount /= 1024
        unit="GB"

    if amount > 500:
        amount /= 1024
        unit="TB"

    amount_string = round(amount,1)
    if unit!="TB":
        amount_string = round(amount,0)


    amount_string = str(amount_string)
    amount_string += " "
    amount_string += unit

    return amount_string

def process_sample_files(files):

    # There are a number of different types of file we can potentially delete
    #
    # 1. Trimmed data where the untrimmed exists
    # 2. Unsplit data (NoCode) where the split data exists
    # 3. Split data with no associated barcode (NoIndex)
    # 4. Mapped data as long as the split data exists
    # 5. Bismark bams where a deduplicated version exists
    # 6. Bismark methylation call files (txt.gz)
    # 7. Bismark report files as long as multiqc exists.
    # 8. Individual CpG reports for bismark
    # 9. Cellranger tar files as long as the fastq and matrix files exist
    # 10. Lostreads files
    # 11. FastQC zip files
    # 12. FastQC reports if multiqc exists
    # 13. FastQ Screen reports if multiqc exists
    # 14. Fast5 or Pod5 tar files from nanopore runs

    # If we have decided not to clean a folder then there will be a DoNotClean.flag file
    # at the top of the folder

    # Let's see if we have a multiqc report
    has_multiqc = False

    for file in files:
        if file.endswith(".html") and "multiqc" in file:
            has_multiqc = True
            break


    # Let's see if we have split data.  These will be fastq.gz files without 
    # _NoCode_ or _NoIndex_ in their names

    has_split_data = False
    for file in files:
        if file.endswith(".fastq.gz") and not ("_NoCode_" in file or "_NoIndex_" in file or "lostreads" in file): 
            has_split_data = True
            break

    # Now we can go through the files trying to find if we can get rid of them.

    for file in files:

        stop_further = False
        
        stop_further = check_trimmed(file,files)
        if stop_further:
            continue

        if has_split_data:
            stop_further = check_unsplit(file,files)
            if stop_further:
                continue

            stop_further = check_unassigned(file,files)
            if stop_further:
                continue

            stop_further = check_cellranger_tar(file,files)
            if stop_further:
                continue

            stop_further = check_lostreads(file,files)
            if stop_further:
                continue

        if has_multiqc:
            stop_further = check_unwanted_qc(file,files)
            if stop_further:
                continue

        stop_further = check_bismark_dedup(file,files)
        if stop_further:
            continue
        
        stop_further = check_bismark_callfiles(file,files)
        if stop_further:
            continue

        stop_further = check_raw_ont_files(file,files)
        if stop_further:
            continue


def check_raw_ont_files(file,files):
    if file.endswith(".tar") or file.endswith("tar.gz") :
        if "fast5" in file or "pod5" in file:
            # We're OK to delete it
            print(files[file], file=delfh)
            stats["ONTRaw"][0] += 1
            stats["ONTRaw"][1] += files[file].stat().st_size
            return True

    return False



def check_lostreads(file,files):
    if file.endswith(".fastq.gz") and "lostreads" in file:
        # We're OK to delete it
        print(files[file], file=delfh)
        stats["LostReads"][0] += 1
        stats["LostReads"][1] += files[file].stat().st_size
        return True

    return False


def check_cellranger_tar(file,files):
    if file.endswith("cellranger.tar") or file.endswith("cellranger.tar.gz"):
        # We're OK to delete it
        print(files[file], file=delfh)
        stats["CellRangerTar"][0] += 1
        stats["CellRangerTar"][1] += files[file].stat().st_size
        return True

    return False



def check_bismark_callfiles(file,files):
    if file.endswith(".txt.gz") and "bismark" in file:
        # We're OK to delete it
        print(files[file], file=delfh)
        stats["BismarkCallFiles"][0] += 1
        stats["BismarkCallFiles"][1] += files[file].stat().st_size
        return True

    return False

def check_bismark_dedup(file,files):
    if file.endswith("deduplicated.bam") and "bismark" in file:
        parent_file = file.replace(".deduplicated.bam",".bam")
        if parent_file in files:
            # We're OK to delete it
            print(files[file], file=delfh)
            stats["BismarkDedup"][0] += 1
            stats["BismarkDedup"][1] += files[file].stat().st_size
        return True

    return False


def check_unwanted_qc(file,files):

    suffixes = [
        "_screen.html",
        "_splitting_report.txt",
        "fastqc.zip",
        "_fastqc.html",
        "bisulfite_orientation.png",
        "_screen.png",
        "_screen.txt",
        ".deduplication_report.txt",
        ".M-bias.txt",
        "_trimming_report.txt"
    ]

    for suffix in suffixes:
        if file.endswith(suffix):
            print(files[file], file=delfh)
            stats["QC"][0] += 1
            stats["QC"][1] += files[file].stat().st_size
            return True
        
    return False



def check_unassigned(file,files):
    if "_NoCode_" in file and file.endswith(".fastq.gz"):
        print(files[file], file=delfh)
        stats["Unassigned"][0] += 1
        stats["Unassigned"][1] += files[file].stat().st_size
        return True

    return False

def check_unsplit(file,files):
    if "_NoIndex_" in file and file.endswith(".fastq.gz"):
        print(files[file], file=delfh)
        stats["Unsplit"][0] += 1
        stats["Unsplit"][1] += files[file].stat().st_size
        return True

    return False

def check_trimmed(file, files):
    if file.endswith(".fq.gz") :
        # It's a trimmed file.  Can we find the corresponding untrimmed.
        if "_val_" in file:
            # It's paried end
            untrimmed = file[:-12]+".fastq.gz"

            if untrimmed in files:
                # We're ok to delete it
                print(files[file], file=delfh)
                stats["Trimmed"][0] += 1
                stats["Trimmed"][1] += files[file].stat().st_size
            return True

        elif "_trimmed.fq.gz" in file:
            # It's a single end file
            untrimmed = file[:-14]+".fastq.gz"

            if untrimmed in files:
                # We're ok to delete it
                print(files[file], file=delfh)
                stats["Trimmed"][0] += 1
                stats["Trimmed"][1] += files[file].stat().st_size
            return True

    return False


def process_folder(folder):

    # At this stage we're going to see if we're processing this folder.
    # If we are then we'll collect all of the files associated with a 
    # particular sample from both the Aligned and Unaligned folder and
    # will parse these to see which we can potentially remove.

    if (folder/"DoNotClean.flag").exists():
        return

    # Get the project name
    project = list((folder/"Unaligned").glob("Project*"))[0].name

    # Get the samples
    samples = []
    for sample in (folder/"Unaligned"/project).glob("Sample*"):
        samples.append(sample.name)


    # Get all files and split them by sample

    sample_files = {}

    for sample in samples:
        sample_files[sample] = {}

    for file in folder.rglob(f"*"):
        pathstring = str(file)
        if file.is_dir():
            continue

        for sample in samples:
            if sample in pathstring:
                if file.name in sample_files[sample]:
                    print("Duplicate",file)

                sample_files[sample][file.name] = file
                break


    for sample in samples:
        process_sample_files(sample_files[sample])






def list_folders(basefolder):

    folders_to_process = []

    for item in Path(basefolder).iterdir():

        if not item.is_dir():
            continue

        # if not item.name == "210430_NB501547_0472_AHGLGNBGXH":
        #     continue

        folder = item.name

        folder_year = folder.split("_")[0]

        if not folder_year.isnumeric():
            continue

        if len(folder_year) == 8:
            folder_year = int(folder_year[0:4])
        
        elif len(folder_year) == 6:
            folder_year = int("20"+folder_year[0:2])

        if options.min_year and folder_year < options.min_year:
            continue

        if options.max_year and folder_year > options.max_year:
            continue

        folders_to_process.append(item)


    return folders_to_process

def get_options():
    parser = argparse.ArgumentParser("Sequencing clean up script")

    parser.add_argument("--min_year", type=int, help="Only run folders older than or equal to this will be processed")
    parser.add_argument("--max_year", type=int, help="Only run folders younger than or equal to this will be processed")

    parser.add_argument("--delfile", type=str, default="/dev/null", help="Filename to write deletion commands to to execute cleanup")

    options =  parser.parse_args()

    max_possible_year = datetime.datetime.now().year - 2

    if options.min_year and options.min_year > max_possible_year:
        raise Exception(f"Can't set min_year above {max_possible_year}")

    if options.max_year and options.max_year > max_possible_year:
        raise Exception(f"Can't set max_year above {max_possible_year}")


    return options


if __name__ == "__main__":
    main()
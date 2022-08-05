# This script takes the raw output of a 10X cellranger run and
# turns it into a set of files which we can synchronise with 
# sierra.
# 
# The files we specifically extract are:
# 1. cloupe.cloupe
# 2. filtered_feature_bc_matrix.h5
# 3. web_summary.html
# 4. molecule_info.h5
#
# We then tar up the whole of the output folder to a single file
# so that everything else is accessible if it's needed.

import sys
from pathlib import Path
from shutil import copy
import re
import subprocess

def main():
    if len(sys.argv) < 2:
        raise Exception(f"No folder to process specified")

    folder = Path(sys.argv[1])

    if not folder.exists():
        raise Exception(f"Folder {folder} doesn't exist - exiting")
        
    folders10x = find_10x_folders(folder)

    print(f"Found {len(folders10x)} 10X output folders", file=sys.stderr)

    for f in folders10x:
        print(f"Processing {f.name}", file=sys.stderr)
        process_folder(f)


def process_folder(folder):
    
    # We need to know the lane number for this sample
    base_name = folder.name
    g = next(folder.parent.glob(base_name+"*.fastq.gz")).name
    lane = re.search("(_L00\d_)",g).groups()[0]
    # cloupe.cloupe
    cloupe_from = folder / "outs/cloupe.cloupe"
    cloupe_to = folder.parent / (base_name+lane+"cloupe.cloupe")
    print(f"Copying {cloupe_from.name} to {cloupe_to.name}", file=sys.stderr)
    copy(cloupe_from, cloupe_to)

    # filtered_feature_bc_matrix.h5
    fmatrix_from = folder / "outs/filtered_feature_bc_matrix.h5"
    fmatrix_to = folder.parent / (base_name+lane+"filtered_feature_bc_matrix.h5")
    print(f"Copying {fmatrix_from.name} to {fmatrix_to.name}", file=sys.stderr)
    copy(fmatrix_from, fmatrix_to)

    # molecule_info.h5
    minfo_from = folder / "outs/molecule_info.h5"
    minfo_to = folder.parent / (base_name+lane+"molecule_info.h5")
    print(f"Copying {minfo_from.name} to {minfo_to.name}", file=sys.stderr)
    copy(minfo_from, minfo_to)


    # web_summary.html
    summary_from = folder / "outs/web_summary.html"
    summary_to = folder.parent / (base_name+lane+"web_summary.html")
    print(f"Copying {summary_from.name} to {summary_to.name}", file=sys.stderr)
    copy(summary_from, summary_to)

    # We then put the whole of the directory into a tar file. It's quicker to
    # do this as an external command
    tar_file = base_name + lane+"cellranger.tar"
    print(f"Putting all 10x output into  {tar_file}", file=sys.stderr)
    tar_command = f"tar -cf {tar_file} {folder.name}"
    subprocess.run(tar_command, check=True, shell=True, cwd=folder.parent)



def find_10x_folders(folder):

    found_folders = []
    
    for f in folder.iterdir():
        # We're looking for output folders
        if not f.is_dir():
            continue

        # If this is a 10x output folder then it should contain
        # a folder called 'outs'
        outs = f / "outs/"

        if outs.exists() and outs.is_dir():
            found_folders.append(f)
        
        
    return found_folders



if __name__ == "__main__": 
    main()
# This script takes the output of a 10X cellranger multi run and
# turns it into a set of files which we can synchronise with 
# sierra.
# This script should be able to handle all the possible mixes of library outputs we might get from different multi-runs
# 
# For the different possible library types the files we specifically extract (if they are present) are:
#
# For the GEX (count):
# 1. cloupe.cloupe
# 2. filtered_feature_bc_matrix.h5
# 3. molecule_info.h5
#
# For the VDJ (any/all of vdj_t/vdj_b/vdj_t_gd):
# 1. vloupe.vloupe
# 2. filtered_contig_annotations.csv
#
# For the antigen_analysis:
# 1. antigen_specificity_scores.csv
# 2. per_barcode.csv
#
# For all
# web_summary.html
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

    #can use the same approach to find 10X folders as the outs directory is the top directory present within the output folder    
    folders10x = find_10x_folders(folder)

    print(f"Found {len(folders10x)} 10X output folders", file=sys.stderr)

    for f in folders10x:
        print(f"Processing {f.name}", file=sys.stderr)
        process_folder(f)


def process_folder(folder):
    
    # First find the lane number for this sample
    base_name = folder.name
    g = next(folder.parent.glob("*"+base_name+"*.fastq.gz")).name
    lane = re.search("(_L00\d_)",g).groups()[0]
    multi_out_path = folder / "outs/per_sample_outs" / base_name

    # Now look for output to rename 
    #  There can be any combination of GEX, VDJ and antigen_analysis output with cell ranger multi
        # The files we want to return are slightly different for each
        # Each will be characterised by directory name
    
    #For the GEX output this will be contained in the count folder
    gex_out_path = multi_out_path / "count"
    #First check if this exists
    if gex_out_path.is_dir():
        print("Found GEX output folder", file=sys.stderr)
        rename_gex_out(gex_out_path,folder,base_name,lane)
    else:
        print("No GEX folder found", file=sys.stderr)

    #For the antigen_analysis output this will be contained in the antigen_analysis folder
    #First check if this exists    
    antigen_out_path = multi_out_path / "antigen_analysis"
    if antigen_out_path.is_dir():
        print("Found antigen_analysis output folder", file=sys.stderr)
        rename_antigen_out(antigen_out_path,folder,base_name,lane)
    else:
        print("No antigen_analysis folder found", file=sys.stderr)
    
    #Finally VDJ analysis
    #There are 3 valid possible folder types and there can be more than 1 associated with a sample
        # Valid options are: vdj_b. vdj_t, vdj_t_gd
    #First see if any of these are present
    found_vdj_folders = find_vdj_folders(multi_out_path)

    if not found_vdj_folders:
        print("No vdj folders found", file=sys.stderr)
    else:
        print(f"Found vdj folders: {found_vdj_folders}", file=sys.stderr)
        for d in found_vdj_folders:
            vdj_out_path = multi_out_path / d
            rename_vdj_out(vdj_out_path,folder,base_name,lane)

    # Last file to copy back separately is the web summary which is stored in the directory above the GEX, VDJ, antigen_analysis
    summary_from = multi_out_path / "web_summary.html"
    summary_to = folder.parent / (base_name+lane+"web_summary.html")
    print(f"Copying {summary_from.name} to {summary_to.name}", file=sys.stderr)
    copy(summary_from, summary_to)

    # We then put the whole of the directory into a tar file. It's quicker to do this as an external command
    tar_file = base_name + lane+"cellranger.tar"
    print(f"Putting all 10x output into {tar_file}", file=sys.stderr)
    tar_command = f"tar -cf {tar_file} {folder.name}"
    subprocess.run(tar_command, check=True, shell=True, cwd=folder.parent)

def rename_vdj_out(vdj_out_path,folder,base_name,lane):

    #get the vloupe.vloupe file
    vloupe_from = vdj_out_path / "vloupe.vloupe"
    vloupe_to = folder.parent / (base_name+lane+vdj_out_path.name+"_vloupe.vloupe")
    print(f"Copying {vloupe_from.name} to {vloupe_to.name}", file=sys.stderr)
    copy(vloupe_from, vloupe_to)

    #get the filtered_contig_annotations.csv file
    contig_from = vdj_out_path / "filtered_contig_annotations.csv"
    contig_to = folder.parent / (base_name+lane+vdj_out_path.name+"_filtered_contig_annotations.csv")
    print(f"Copying {contig_from.name} to {contig_to.name}", file=sys.stderr)
    copy(contig_from, contig_to)

def find_vdj_folders(folder):

    found_vdj_folders = []

    for f in folder.iterdir():
    # We're looking for output folders
        if not f.is_dir():
            continue
    #check if the name matches to one of 3 valid options for VDJ: vdj_b. vdj_t, vdj_t_gd
        if f.name in ["vdj_b","vdj_t","vdj_t_gd"]:
            found_vdj_folders.append(f.name)

    return(found_vdj_folders)

def rename_antigen_out(antigen_out_path,folder,base_name,lane):
    
    #get the antigen specificity scores
    scores_from = antigen_out_path / "antigen_specificity_scores.csv"
    scores_to = folder.parent / (base_name+lane+"antigen_specificity_scores.csv")
    print(f"Copying {scores_from.name} to {scores_to.name}", file=sys.stderr)
    copy(scores_from, scores_to)

    #get the per barcode
    barcodes_from = antigen_out_path / "per_barcode.csv"
    barcodes_to = folder.parent / (base_name+lane+"antigen_specificity_scores.csv")
    print(f"Copying {barcodes_from.name} to {barcodes_to.name}", file=sys.stderr)
    copy(barcodes_from, barcodes_to)

def rename_gex_out(gex_out_path,folder,base_name,lane):

    # get the cloupe.cloupe
    # looks as though this now starts sample_cloupe.cloupe
    cloupe_from = gex_out_path / "sample_cloupe.cloupe"
    cloupe_to = folder.parent / (base_name+lane+"cloupe.cloupe")
    print(f"Copying {cloupe_from.name} to {cloupe_to.name}", file=sys.stderr)
    copy(cloupe_from, cloupe_to)

    # filtered_feature_bc_matrix.h5
    fmatrix_from = gex_out_path / "sample_filtered_feature_bc_matrix.h5"
    fmatrix_to = folder.parent / (base_name+lane+"filtered_feature_bc_matrix.h5")
    print(f"Copying {fmatrix_from.name} to {fmatrix_to.name}", file=sys.stderr)
    copy(fmatrix_from, fmatrix_to)

    # molecule_info.h5
    minfo_from = gex_out_path / "sample_molecule_info.h5"
    minfo_to = folder.parent / (base_name+lane+"molecule_info.h5")
    print(f"Copying {minfo_from.name} to {minfo_to.name}", file=sys.stderr)
    copy(minfo_from, minfo_to)

def find_10x_folders(folder):

    found_folders = []
    
    for f in folder.iterdir():
        # We're looking for output folders
        if not f.is_dir():
            continue

        # If this is a 10x cell ranger multi output folder then it should contain
        # a nested folder structure : "outs/per_sample_outs"
        outs = f / "outs/per_sample_outs"

        if outs.exists() and outs.is_dir():
            found_folders.append(f)
    
    return found_folders


if __name__ == "__main__": 
    main()
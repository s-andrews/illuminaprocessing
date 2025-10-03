library(dplyr)
library(ggplot2)

# Usage:  Rscript ~/illuminaprocessing/barcode_ggplot.R [runfolder]
# It shouldn't matter where the script is run from (as long as it's run on the pipeline server)

cmd_args <- commandArgs(trailingOnly = TRUE)
#print(cmd_args)
run_folder <- cmd_args[1]
print(paste0("run folder is ", run_folder))

n_seqs_checked <- 1000000

barcode_folder <- paste0("/primary/", run_folder, "/Unaligned/Project_External/Sample_lane1/")

phiX_bc1 <- c("ATGTCGCT", "GCACATAG", "TGTGTCGA", "CACAGATC")
phiX_bc1_6 <- c("ATGTCG", "GCACAT", "TGTGTC", "CACAGA")
phiX_dual8 <- c("ATGTCGCT_CTAGCTCG", "GCACATAG_GACTACTA", "TGTGTCGA_TGTCTGAC", "CACAGATC_ACGAGAGT")
phiX_dual6 <- c("ATGTCG_CTAGCT", "GCACAT_GACTAC", "TGTGTC_TGTCTG", "CACAGA_ACGAGA")
phiX_dual6_8 <- c("ATGTCG_CTAGCTCG", "GCACAT_GACTACTA", "TGTGTC_TGTCTGAC", "CACAGA_ACGAGAGT")

exp_file <- paste0(barcode_folder, "expected_barcodes.txt")
found_file <- paste0(barcode_folder, "found_barcodes.txt")

exp <- readr::read_csv(file=exp_file, col_names = c("bc1", "bc2", "name"))
found <- readr::read_delim(found_file, col_names = c("count", "bc")) |>
  dplyr::mutate(percentage = 100*(count/n_seqs_checked))

if(all(is.na(exp$bc2))) {
  dual_coded <- FALSE
} else if (any(is.na(exp$bc2))) {
  # this should never happen
  msg <- "Some (but not all) of the expected 2nd barcodes are showing as NA - check the sample sheet in Sierra"
  stop(msg)
} else {
  dual_coded <- TRUE
}

if (dual_coded){
  exp <- exp |>
    tidyr::unite(col = "bc", sep = "_", bc1, bc2)
} else {
  exp <- exp |>
    dplyr::rename("bc" = bc1)
}

all <- exp |>
  full_join(found) |>
  arrange(desc(percentage)) |>
  mutate(status = if_else(is.na(name), "unexpected", "present")) |>
  mutate(status = case_when(
    status == "present" ~ "present",
    bc %in% phiX_dual8 ~ "PhiX",
    bc %in% phiX_dual6 ~ "PhiX",
    bc %in% phiX_dual6_8 ~ "PhiX",
    bc %in% phiX_bc1 ~ "PhiX",
    bc %in% phiX_bc1_6 ~ "PhiX",
    .default = "unexpected"
  )) |> 
  mutate(status = if_else(is.na(percentage), "missing", status)) |>
  mutate(status = factor(status, levels = c("present", "PhiX", "unexpected", "missing"))) |>
  mutate(percentage = tidyr::replace_na(percentage, 0)) |>
  mutate(bc = reorder(bc, percentage)) |>
  tidyr::unite(col = "barlabel", bc, name, sep = "\n", remove = FALSE, na.rm = TRUE) |>
  mutate(barlabel = reorder(barlabel, percentage))

# write out data before filtering in case extra barcodes are useful
textout <- paste0(barcode_folder, "barcode_L001_plot_data.txt")
outdata <- dplyr::select(all, -barlabel)
readr::write_tsv(outdata, file = textout)  

# filter so that we don't have 10 extra barcodes on the plot if they're not helpful
lowest_present <- all |>
  filter(status == "present") |>
  pull(percentage) |>
  min()
  
all_filt <- all |>
  filter(!(status == "unexpected" & percentage < lowest_present))

bar_colours <- c(present = "#0aa192", PhiX = "#a655fb", unexpected = "#f57600", missing = "grey")
bar_outer <- c(present = "#0aa192", PhiX = "#a655fb", unexpected = "#f57600", missing = "#e6308a")

outfile <- paste0(barcode_folder, "barcode_L001_plot.png")

percentage_of_all_data <- round(sum(all_filt$percentage), digits = 0)
plot_title <- paste0("Barcodes shown explain ", percentage_of_all_data, "% of the first million sequences")

p <- all_filt |>
  ggplot(aes(x = barlabel, y = percentage, fill = status, colour = status)) +
  geom_col(width = 0.9) +
  scale_fill_manual(values = bar_colours) +
  scale_colour_manual(values = bar_outer) +
  scale_y_continuous(expand = c(0.01, 0)) +
  xlab("") +
  ylab("Percentage of reads") +
  coord_flip() +
  theme_bw() +
  ggtitle(plot_title) +
  theme(
    plot.title = element_text(family = "sans", size = 14, hjust = 0.5, margin = margin(20,0,30,0)),
    axis.text.y = element_text(size=8)
  )

ggsave(outfile, plot = p, units = "px", width = 2000, height=100+(100*nrow(all)))

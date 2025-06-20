library(dplyr)
library(ggplot2)

cmd_args <- commandArgs(trailingOnly = TRUE)
#print(cmd_args)
run_folder <- cmd_args[1]
print(paste0("run folder is ", run_folder))

n_seqs_checked <- 100000

barcode_folder <- paste0("/primary/", run_folder, "/Unaligned/Project_External/Sample_lane1/")

exp_file <- paste0(barcode_folder, "expected_barcodes.txt")
found_file <- paste0(barcode_folder, "found_L001_barcodes.txt")

exp <- readr::read_delim(file=exp_file, col_names = c("bc1", "bc2", "name"))
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

percentage_of_all_data <- round(sum(found$percentage), digits = 0)

all <- exp |>
  full_join(found) |>
  arrange(desc(percentage)) |>
  mutate(status = if_else(is.na(name), "unexpected", "present")) |>
  mutate(status = if_else(is.na(percentage), "missing", status)) |>
  mutate(percentage = tidyr::replace_na(percentage, 0)) |>
  mutate(bc = reorder(bc, percentage)) |>
  tidyr::unite(col = "barlabel", bc, name, sep = "\n", remove = FALSE, na.rm = TRUE) |>
  mutate(barlabel = reorder(barlabel, percentage))
  
bar_colours <- c(present = "seagreen", unexpected = "orangered", missing = "grey")
outfile <- "barcode_L001_plot.png"
plot_title <- paste0("Barcodes shown explain ", percentage_of_all_data, "% of the data")

p <- all |>
  ggplot(aes(x = barlabel, y = percentage, fill = status)) +
  geom_col(width = 0.9) +
  scale_fill_manual(values = bar_colours) +
  theme(axis.text.y = element_text(size=7)) +
  scale_y_continuous(expand = c(0.01, 0)) +
  xlab("") +
  ylab("Percentage of reads") +
  coord_flip() +
  theme_bw() +
  ggtitle(plot_title) +
  theme(plot.title = element_text(family = "sans", size = 16, hjust = 0.5, margin = margin(20,0,30,0)))

ggsave(outfile, plot = p, units = "px", width = 2000, height=100+(100*nrow(all)))

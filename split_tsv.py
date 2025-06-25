import pandas as pd


input_tsv = "data/example.tsv"
num_parts = 2

tsv = pd.read_csv(input_tsv, sep="\t")

part_size = len(tsv) // num_parts
for i in range(num_parts):
    part = tsv.iloc[i::num_parts]
    part.to_csv(input_tsv.replace(".tsv", f"_part{i+1}.tsv"), sep="\t", index=False)


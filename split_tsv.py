import pandas as pd
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Split a TSV file into multiple parts')
    parser.add_argument('input_file', help='Input TSV file path')
    parser.add_argument('num_parts', type=int, help='Number of parts to split into')

    return parser.parse_args()

def main():
    args = parse_arguments()
    input_tsv = args.input_file
    num_parts = args.num_parts

    # Read the TSV file
    tsv = pd.read_csv(input_tsv, sep="\t")

    # Split into parts
    for i in range(num_parts):
        part = tsv.iloc[i::num_parts]
        output_file = input_tsv.replace(".tsv", f"_part{i+1}.tsv")
        part.to_csv(output_file, sep="\t", index=False)
        print(f"Created: {output_file} ({len(part)} rows)")

if __name__ == "__main__":
    main()
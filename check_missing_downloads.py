#!/usr/bin/env python3
"""
檢查哪些IPR accession還沒有下載
"""

import os
import pandas as pd
import argparse
from pathlib import Path

def get_downloaded_accessions(json_dir):
    """
    從JSON目錄中獲取已下載的accession列表
    
    Args:
        json_dir (str): 包含JSON文件的目錄路徑
        
    Returns:
        set: 已下載的accession集合
    """
    downloaded = set()
    json_dir = Path(json_dir)
    
    if not json_dir.exists():
        print(f"# Directory not found: {json_dir}")
        return downloaded
    
    # 查找所有taxonomy相關的JSON文件
    json_files = list(json_dir.glob("*_taxonomy*.json"))

    for json_file in json_files:
        # 從文件名提取IPR accession
        # 支持多種格式:
        # IPR000001_taxonomy.json -> IPR000001
        # IPR000001_taxonomy_by_cellorg.json -> IPR000001
        filename = json_file.stem
        if '_taxonomy' in filename:
            # 提取IPR編號（在第一個_taxonomy之前的部分）
            accession = filename.split('_taxonomy')[0]
            downloaded.add(accession)
    
    return downloaded

def get_required_accessions(tsv_file):
    """
    從TSV文件中獲取需要下載的accession列表
    
    Args:
        tsv_file (str): TSV文件路徑
        
    Returns:
        set: 需要下載的accession集合
    """
    try:
        df = pd.read_csv(tsv_file, sep="\t")
        
        # Check if Accession column exists
        if 'Accession' not in df.columns:
            print(f"# 'Accession' column not found in TSV file")
            print(f"# Available columns: {list(df.columns)}")
            return set()

        required = set(df['Accession'].astype(str))
        return required

    except Exception as e:
        print(f"# Failed to read TSV file: {e}")
        return set()

def main():
    parser = argparse.ArgumentParser(
        description='Check which IPR accessions are missing from downloads',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Check missing downloads
  python check_missing_downloads.py database/interpro_type_domain/ data/accessions.tsv

  # Output missing accessions to file
  python check_missing_downloads.py database/interpro_type_domain/ data/accessions.tsv --output missing.txt
        '''
    )

    parser.add_argument(
        'json_dir',
        help='Directory path containing downloaded JSON files'
    )

    parser.add_argument(
        'tsv_file',
        help='TSV file path containing all required accessions'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output missing accessions list to file (optional)'
    )
    
    args = parser.parse_args()

    print("# Checking download status...")

    # Get downloaded accessions
    downloaded = get_downloaded_accessions(args.json_dir)
    print(f"# Downloaded files: {len(downloaded)}")

    # Get required accessions
    required = get_required_accessions(args.tsv_file)
    print(f"# Total required: {len(required)}")
    
    # 計算缺失的accession
    missing = required - downloaded
    completed = required & downloaded
    
    print("\n" + "="*60)
    print("# Download Status Summary")
    print("="*60)
    print(f"# Completed: {len(completed)} / {len(required)} ({len(completed)/len(required)*100:.1f}%)")
    print(f"# Missing: {len(missing)} / {len(required)} ({len(missing)/len(required)*100:.1f}%)")

    if missing:
        print(f"\n# Missing accessions ({len(missing)} items):")
        missing_list = sorted(list(missing))

        # Show first 10 missing accessions
        for i, acc in enumerate(missing_list[:10]):
            print(f"   {i+1:3d}. {acc}")

        if len(missing_list) > 10:
            print(f"   ... and {len(missing_list) - 10} more")

        # Save missing accessions to file if specified
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    for acc in missing_list:
                        f.write(f"{acc}\n")
                print(f"\n# Missing accessions saved to: {args.output}")
            except Exception as e:
                print(f"\n# Failed to save file: {e}")
    else:
        print("\n# All accessions have been downloaded!")

    # Check for extra downloads (in JSON directory but not in TSV)
    extra = downloaded - required
    if extra:
        print(f"\n# Found extra download files ({len(extra)} items):")
        extra_list = sorted(list(extra))
        for i, acc in enumerate(extra_list[:5]):
            print(f"   {i+1}. {acc}")
        if len(extra_list) > 5:
            print(f"   ... and {len(extra_list) - 5} more")

if __name__ == "__main__":
    main()

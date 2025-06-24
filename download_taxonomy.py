import pandas as pd
import requests
import json
import os
import time
import sys
import argparse

def parse_arguments():
    """
    解析命令行参数

    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='Download taxonomy information from InterPro API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Download single IPR entry
  python download_taxonomy.py IPR000001

  # Download from TSV file
  python download_taxonomy.py input.tsv

  # Custom output directory
  python download_taxonomy.py IPR000001 --output-dir ./custom_output

  # Adjust retry settings
  python download_taxonomy.py input.tsv --max-retries 5 --retry-delay 15
        '''
    )

    # 必需参数
    parser.add_argument(
        'input',
        help='TSV file path containing IPR accessions or single IPR number (e.g., IPR000001)'
    )

    # 可选参数
    parser.add_argument(
        '--output-dir', '-o',
        default='./database/interpro_taxonomy',
        help='Output directory for downloaded JSON files (default: ./database/interpro_taxonomy)'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum number of retry attempts (default: 3)'
    )

    parser.add_argument(
        '--sleep-between-requests',
        type=float,
        default=1.0,
        help='Sleep time between requests in seconds (default: 1.0)'
    )

    parser.add_argument(
        '--retry-delay',
        type=int,
        default=10,
        help='Delay between retries in seconds (default: 10)'
    )

    parser.add_argument(
        '--timeout-delay',
        type=int,
        default=61,
        help='Delay for timeout errors in seconds (default: 61)'
    )

    parser.add_argument(
        '--request-timeout',
        type=int,
        default=1000,
        help='HTTP request timeout in seconds (default: 1000)'
    )

    parser.add_argument(
        '--force-redownload', '-f',
        action='store_true',
        help='Force redownload even if file already exists'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()

# 解析命令行参数
args = parse_arguments()

# 配置参数
INPUT_ARG = args.input
SAVE_DIR = args.output_dir
MAX_RETRIES = args.max_retries
SLEEP_BETWEEN_REQUESTS = args.sleep_between_requests
RETRY_DELAY = args.retry_delay
TIMEOUT_DELAY = args.timeout_delay
REQUEST_TIMEOUT = args.request_timeout
FORCE_REDOWNLOAD = args.force_redownload
VERBOSE = args.verbose
BASE_URL = "https://www.ebi.ac.uk/interpro/api"

# 确保保存目录存在
os.makedirs(SAVE_DIR, exist_ok=True)

# 重试机制封装函数
def safe_request(url):
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response
            elif response.status_code == 408:
                if VERBOSE:
                    print(f"# Timeout (408). Retrying after {TIMEOUT_DELAY}s... ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(TIMEOUT_DELAY)
            else:
                if VERBOSE:
                    print(f"# HTTP error {response.status_code}. Retrying in {RETRY_DELAY}s... ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            if VERBOSE:
                print(f"#[FAILED] Request failed: {e}. Retrying in {RETRY_DELAY}s... ({attempt + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
    print(f"#[FAILED] Failed after {MAX_RETRIES} attempts: {url}")
    return None

# 判断输入是 TSV 文件还是 IPR 编号
if INPUT_ARG.endswith('.tsv') or INPUT_ARG.endswith('.txt') or os.path.isfile(INPUT_ARG):
    # 输入是文件路径
    print(f"# Reading IPR accessions from file: {INPUT_ARG}")
    try:
        df = pd.read_csv(INPUT_ARG, sep="\t")
        ipr_accessions = df['Accession'].tolist()
        print(f"# Found {len(ipr_accessions)} IPR accessions in file")
    except Exception as e:
        print(f"#[FAILED] Error reading file {INPUT_ARG}: {e}")
        sys.exit(1)
else:
    # 输入是单个 IPR 编号
    print(f"# Processing single IPR accession: {INPUT_ARG}")
    ipr_accessions = [INPUT_ARG]

# 显示配置信息
if VERBOSE:
    print(f"# Configuration:")
    print(f"#   Output directory: {SAVE_DIR}")
    print(f"#   Max retries: {MAX_RETRIES}")
    print(f"#   Sleep between requests: {SLEEP_BETWEEN_REQUESTS}s")
    print(f"#   Force redownload: {FORCE_REDOWNLOAD}")

# 遍历每个 accession 下载数据
for i, ipr_accession in enumerate(ipr_accessions, 1):
    output_path = f"{SAVE_DIR}/{ipr_accession}_taxonomy_by_cellorg.json"

    if os.path.exists(output_path) and not FORCE_REDOWNLOAD:
        if VERBOSE:
            print(f"# [{i}/{len(ipr_accessions)}] Already downloaded: {ipr_accession}")
        continue

    print(f"# [{i}/{len(ipr_accessions)}] Downloading taxonomy for {ipr_accession}...")
    #target_url = f"{BASE_URL}/taxonomy/uniprot/entry/interpro/{ipr_accession}/"
    target_url = f"{BASE_URL}/taxonomy/uniprot/131567?filter_by_entry={ipr_accession}"

    response = safe_request(target_url)
    if response:
        try:
            data = response.json()
            with open(output_path, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 显示下载统计
            result_count = len(data.get('results', []))
            total_count = data.get('count', 0)
            print(f"# Saved: {output_path}")
            if VERBOSE:
                print(f"#   Downloaded {result_count} nodes (Total available: {total_count})")

        except Exception as e:
            print(f"#[FAILED] JSON decode failed for {ipr_accession}: {e}")
    else:
        print(f"#[FAILED] Skipped {ipr_accession} due to repeated failures.")

    # 间隔一会防止频繁请求
    if SLEEP_BETWEEN_REQUESTS > 0:
        time.sleep(SLEEP_BETWEEN_REQUESTS)

print(f"# Completed processing {len(ipr_accessions)} IPR accessions")

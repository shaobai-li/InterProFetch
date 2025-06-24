import pandas as pd
import requests
import json
import os
import time

# 配置参数
DIR_PATH = "./"

import sys

if len(sys.argv) < 2:
    print("Please provide either a TSV file path or an IPR number as the first argument")
    sys.exit(1)

INPUT_ARG = sys.argv[1]
SAVE_DIR = f"{DIR_PATH}/database/interpro_type_domain"
BASE_URL = "https://www.ebi.ac.uk/interpro/api"
MAX_RETRIES = 3
SLEEP_BETWEEN_REQUESTS = 1  # 防止访问过于频繁
RETRY_DELAY = 10  # 其他错误时重试等待时间
TIMEOUT_DELAY = 61  # API超时时等待时间（官方建议）

# 确保保存目录存在
os.makedirs(SAVE_DIR, exist_ok=True)

# 重试机制封装函数
def safe_request(url):
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=100)
            if response.status_code == 200:
                return response
            elif response.status_code == 408:
                print(f"# Timeout (408). Retrying after {TIMEOUT_DELAY}s... ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(TIMEOUT_DELAY)
            else:
                print(f"# HTTP error {response.status_code}. Retrying in {RETRY_DELAY}s... ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            print(f"#[FAILED] Request failed: {e}. Retrying in {RETRY_DELAY}s... ({attempt + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
    print(f"#[FAILED] Failed after {MAX_RETRIES} attempts: {url}")
    return None

# 判断输入是 TSV 文件还是 IPR 编号
if INPUT_ARG.endswith('.tsv') or INPUT_ARG.endswith('.txt') or os.path.isfile(INPUT_ARG):
    # 输入是文件路径
    print(f"# Reading IPR accessions from file: {INPUT_ARG}")
    df = pd.read_csv(INPUT_ARG, sep="\t")
    ipr_accessions = df['Accession'].tolist()
else:
    # 输入是单个 IPR 编号
    print(f"# Processing single IPR accession: {INPUT_ARG}")
    ipr_accessions = [INPUT_ARG]

# 遍历每个 accession 下载数据
for ipr_accession in ipr_accessions:
    output_path = f"{SAVE_DIR}/{ipr_accession}_taxonomy.json"

    if os.path.exists(output_path):
        #print(f"# Already downloaded: {ipr_accession}")
        continue

    print(f"# Downloading taxonomy for {ipr_accession}...")
    target_url = f"{BASE_URL}/taxonomy/uniprot/entry/interpro/{ipr_accession}/"

    response = safe_request(target_url)
    if response:
        try:
            data = response.json()
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"# Saved: {output_path}")
        except Exception as e:
            print(f"#[FAILED] JSON decode failed for {ipr_accession}: {e}")
    else:
        print(f"#[FAILED] Skipped {ipr_accession} due to repeated failures.")

    # 间隔一会防止频繁请求
    time.sleep(SLEEP_BETWEEN_REQUESTS)

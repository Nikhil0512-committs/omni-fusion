import os
import subprocess
import pandas as pd
import numpy as np
import wfdb

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running '{cmd}': {result.stderr}")
    return result

def verify_checksums(directory):
    checksum_files = []
    for root, dirs, files in os.walk(directory):
        if 'SHA256SUMS.txt' in files:
            checksum_files.append(os.path.join(root, 'SHA256SUMS.txt'))
    
    if not checksum_files:
        print(f"No SHA256SUMS.txt found in {directory}")
        return False
    
    checksum_file = checksum_files[0]
    base_dir = os.path.dirname(checksum_file)
    print(f"Verifying checksums using {checksum_file}...")
    
    cmd = f"cd '{base_dir}' && shasum -a 256 -c SHA256SUMS.txt"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    success_count = result.stdout.count("OK")
    failure_count = result.stdout.count("FAILED")
    print(f"Checksum verification: {success_count} OK, {failure_count} FAILED")
    
    if failure_count > 0:
        return False
    return True

def count_files(directory):
    count = sum(len(files) for _, _, files in os.walk(directory))
    print(f"Total files in {directory}: {count}")
    return count

if __name__ == '__main__':
    # 1. Acquire and Verify PTB-XL
    print("Setting up PTB-XL...")
    dest_dir = "data/raw/ptbxl"
    os.makedirs(dest_dir, exist_ok=True)
    zip_path = os.path.join(dest_dir, "ptbxl.zip")

    if not os.path.exists(zip_path):
        url = "https://physionet.org/static/published-projects/ptb-xl/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3.zip"
        run_cmd(f"curl -L -s -o '{zip_path}' '{url}'")

    extracted_dir = os.path.join(dest_dir, "ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3")
    if not os.path.exists(extracted_dir):
        print("Unzipping PTB-XL...")
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)

    count_files(extracted_dir)
    verify_checksums(extracted_dir)

    # 2. Acquire and Verify MIMIC-IV Clinical Demo
    print("Setting up MIMIC-IV Clinical Demo...")
    dest_dir_mimic = "data/raw/mimic_iv_demo"
    os.makedirs(dest_dir_mimic, exist_ok=True)
    zip_path_mimic = os.path.join(dest_dir_mimic, "mimic.zip")

    if not os.path.exists(zip_path_mimic):
        url = "https://physionet.org/static/published-projects/mimic-iv-demo/mimic-iv-clinical-database-demo-2.2.zip"
        run_cmd(f"curl -L -s -o '{zip_path_mimic}' '{url}'")

    extracted_dir_mimic = os.path.join(dest_dir_mimic, "mimic-iv-clinical-database-demo-2.2")
    if not os.path.exists(extracted_dir_mimic):
        print("Unzipping MIMIC-IV Demo...")
        import zipfile
        with zipfile.ZipFile(zip_path_mimic, 'r') as zip_ref:
            zip_ref.extractall(dest_dir_mimic)
        
    count_files(extracted_dir_mimic)
    verify_checksums(extracted_dir_mimic)

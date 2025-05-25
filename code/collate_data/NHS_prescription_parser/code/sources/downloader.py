import json 
import os
import re
from datetime import datetime, timedelta
import requests
import zipfile
import gzip
import shutil


class Downloader():
    def __init__(self,sourcesFile = "serialized_file_paths.json" , download_dir = '../prescriptionfiles/'):
        with open(sourcesFile, 'r') as f:
            self.sources = json.load(f)
        self.year_source = {}
        self.download_dir = download_dir
        self.cache = {}
        for key, value in self.sources.items():
            year = key.split(".")[0]
            self.year_source[year] = value

    def takestock_(self):
        if not os.path.exists(self.download_dir):
            raise ValueError("download directory does not exist")
        for file in os.listdir(self.download_dir):
            if file.endswith('.gz') or file.endswith('.ZIP'):
                key = file.split(".")[0]
                self.cache[key] = self.download_dir + file

    def is_date_format_(self, input_string):
        # check if the input string matches the format YYYYMM
        pattern = re.compile(r'^(19|20)\d\d(0[1-9]|1[0-2])$')
        return bool(pattern.match(input_string))
    
    def generate_dates(self , start, end):
        start_date = datetime.strptime(start, "%Y%m")
        end_date = datetime.strptime(end, "%Y%m")
        
        current_date = start_date
        dates = []
        
        while current_date <= end_date:
            dates.append(current_date.strftime("%Y%m"))
            # Increase by one month
            current_date += timedelta(days=31)
            current_date = current_date.replace(day=1)
        
        return dates
    
    def download_file(self, url):
        target_folder = self.download_dir
        # Send a GET request to the URL
        response = requests.get(url, stream=True)
        
        # Check that the request was successful
        if response.status_code == 200:
            # Extract the filename from the URL
            filename = url.split("/")[-1].split("?")[0]
            print(f"Downloading {url}")
            
            # Create the full path for the downloaded file
            file_path = os.path.join(target_folder, filename)
            
            # Open the file and write the contents of the response to it
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024): 
                    if chunk: 
                        file.write(chunk)
                        
            print(f"Downloaded file to {file_path}")
            return file_path
        else:
            print(f"Failed to download file from {url}")
            return None

    def extract_and_process_zip(self, zip_path, yyyymm):
        """
        Extract ZIP file and convert to gzipped format expected by the system.
        
        Args:
            zip_path: Path to the downloaded ZIP file
            yyyymm: Year and month (YYYYMM) of the data
        
        Returns:
            Path to the processed .gz file
        """
        print(f"Processing ZIP file: {zip_path}")
        
        # Create temporary directory for extraction
        temp_dir = os.path.join(self.download_dir, f"temp_{yyyymm}")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        try:
            # Extract ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the extracted CSV file
            csv_files = [f for f in os.listdir(temp_dir) if f.endswith('.csv')]
            if not csv_files:
                print("No CSV files found in the extracted archive")
                return None
            
            csv_file = os.path.join(temp_dir, csv_files[0])
            print(f"Found CSV file: {csv_file}")
            
            # Create output filename
            output_filename = f"{yyyymm}.gz"
            output_path = os.path.join(self.download_dir, output_filename)
            
            # Compress CSV to gzip format
            with open(csv_file, 'rb') as f_in:
                with gzip.open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            print(f"Processed EPD file saved to: {output_path}")
            
            # Clean up
            shutil.rmtree(temp_dir)
            os.remove(zip_path)  # Remove original ZIP file
            
            return output_path
        
        except Exception as e:
            print(f"Error processing ZIP file: {e}")
            # Clean up on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return None

    def download_and_process_file(self, url, yyyymm):
        """
        Download and process a file, handling both .gz and .ZIP formats.
        
        Args:
            url: URL to download from
            yyyymm: Year and month (YYYYMM) of the data
        
        Returns:
            Path to the processed file
        """
        # Download the file
        file_path = self.download_file(url)
        if not file_path:
            return None
        
        # If it's a ZIP file, extract and process it
        if file_path.endswith('.ZIP') or file_path.endswith('.zip'):
            return self.extract_and_process_zip(file_path, yyyymm)
        else:
            # For .gz files, return as-is
            return file_path

    def download_range(self , startYYYYMM , endYYYYMM):
        self.takestock_()
        if (not self.is_date_format_(startYYYYMM)) or (not self.is_date_format_(endYYYYMM)):
            raise ValueError("invalid start and end date formats. Dates must be YYYYMM")
        if (startYYYYMM not in self.year_source) or (endYYYYMM not in self.year_source):
            available_dates = sorted(self.year_source.keys())
            raise ValueError(f"dates out of range. Available dates: {available_dates[0]} to {available_dates[-1]}")
        
        dates = self.generate_dates(startYYYYMM , endYYYYMM)
        downloads = []
        
        for date in dates:
            # Check if we already have the processed .gz file
            gz_file_path = os.path.join(self.download_dir, f"{date}.gz")
            if os.path.exists(gz_file_path):
                print(f"File {date}.gz already exists")
                downloads.append(gz_file_path)
                continue
            
            if date in self.cache:
                print(f"File {date} already downloaded")
                downloads.append(self.cache[date])
                continue
            
            # Try to download from available sources
            file_downloaded = False
            
            # First try .gz format
            if date in self.year_source:
                url = self.year_source[date]
                file = self.download_and_process_file(url, date)
                if file:
                    downloads.append(file)
                    file_downloaded = True
            
            # If .gz not available, try .ZIP format
            if not file_downloaded:
                zip_key = f"{date}.ZIP"
                if zip_key in self.sources:
                    url = self.sources[zip_key]
                    file = self.download_and_process_file(url, date)
                    if file:
                        downloads.append(file)
                        file_downloaded = True
            
            if not file_downloaded:
                print(f"Warning: Could not download file for {date}")
        
        print("Finished download process")
        return downloads





if __name__ == '__main__': 
    obj = Downloader()
    
    # Test with a range that includes both old and new formats
    obj.download_range("202101","202103")
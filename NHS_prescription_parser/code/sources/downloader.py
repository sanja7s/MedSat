import json 
import os
import re
from datetime import datetime, timedelta
import requests


class Downloader():
    def __init__(self,sourcesFile = "serialized_file_paths.json" , download_dir = '../prescriptionfiles/'):
        self.sources = json.load(open(sourcesFile,'r'))
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
            if file.endswith('.gz'):
                key = file.split(".")[0]
                self.cache[key] = self.download_dir + file

    def is_date_format_(self, input_string):
        # check if the input string matches the format YYYYMM
        pattern = re.compile('^(19|20)\d\d(0[1-9]|1[0-2])$')
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

    def download_range(self , startYYYYMM , endYYYYMM):
        self.takestock_()
        if (not self.is_date_format_(startYYYYMM)) or (not self.is_date_format_(endYYYYMM)):
            raise ValueError("invalid start and end date formats. Dates must be YYYYMM")
        if (startYYYYMM not in self.year_source) or (endYYYYMM not in self.year_source):
            raise ValueError("dates out of range. we only have between 201401 and 202102")
        dates = self.generate_dates(startYYYYMM , endYYYYMM)
        downloads = []
        for date in dates : 
            url = self.year_source[date]
            if date in self.cache:
                print("File already downloaded")
                filename = url.split("/")[-1].split("?")[0]
                downloads.append(os.path.join(self.download_dir, filename))
                continue
            file = self.download_file(url)
            if file:
                downloads.append(file)
        print("Finished download process")
        return downloads





if __name__ == '__main__': 
    obj = Downloader()
    
    obj.download_range("202001","202005")
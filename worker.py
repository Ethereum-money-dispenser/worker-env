# Managing fuzzers
import sqlite3
import os
import sys
import threading
import subprocess
import json
import requests
from bs4 import BeautifulSoup
from bs4 import Tag
# from downloader import Downloader
from subprocess import CompletedProcess
from sqlite3 import Connection, Cursor
from requests import Response

from typing import Dict, List

class Fuzzer():
    def __init__(self, id: str) -> None:
        self.id = id
        self.etherscan_api_key: str = "9NFWVRRXYWJI1BUU3H8Y9IZTZKXGF4TUK3"
        self.bscscan_api_key: str = "[Bscscan API key]"
        self.arbiscan_api_key: str = "[Arbiscan API key]"
        self.url_sending: str = "http://64.110.110.12:5000/users-sending"
        self.url_receiving: str = "http://64.110.110.12:5000/users-receiving"
        # self.url_sending: str = "http://127.0.0.1:5000/users-sending"
        # self.url_receiving: str = "http://127.0.0.1:5000/users-receiving"
        self.etherscan_api_link: str = "https://api.etherscan.io/api"
        self.bscscan_api_link: str = "https://api.bscscan.com/api"
        self.arbiscan_api_link: str = "https://api.arbiscan.io/api"

    def load_dataset(self) -> List[Dict[str, str]]:
        '''
        Load the dataset from server
        '''
        
        headers: Dict = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'http://127.0.0.1:5000',
            'Pragma': 'no-cache',
            'Referer': 'http://127.0.0.1:5000/users-receiving',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        
        data: Dict = {
            'userid': self.id,
        }

        res: Response = requests.post(self.url_receiving, data=data, headers=headers)
        soup: BeautifulSoup = BeautifulSoup(res.text, 'html.parser')
        
        table: Tag = soup.find('table', attrs={'id':'dataTable'})
        tbody: Tag = table.find('tbody')
        
        addresses: List = []
        for row in tbody.find_all('tr'):
            cols = row.find_all('td')
            network: str = cols[1].text
            address: str = cols[2].text
            
            addresses.append({
                "network": network, 
                "address": address
            })
            
        return addresses
    
    def get_information_from_address(self, data: Dict[str, str]) -> Dict[str, str]:
        # get contract abi, source code, bytecode from address and save to the file
        get_abi_query: str = f"&action=getabi&address={data['address']}"
        get_sourcecode_query: str = f"&action=getsourcecode&address={data['address']}&apikey={self.etherscan_api_key}"
        
        if data['network'] == "etherscan.io":
            get_abi: str = self.etherscan_api_link + get_abi_query
            get_sourcecode: str = self.etherscan_api_link + get_sourcecode_query
        elif data['network'] == "bscscan.com":
            get_abi: str = self.bscscan_api_link + get_abi_query
            get_sourcecode: str = self.bscscan_api_link + get_sourcecode_query
        elif data['network'] == "arbiscan.io":
            get_abi: str = self.arbiscan_api_link + get_abi_query
            get_sourcecode: str = self.arbiscan_api_link + get_sourcecode_query
        
        abi_params: Dict = {
            "module": "contract",
            "action": "getabi",
            "address": data['address'],
            "apikey": self.etherscan_api_key
        }
        abi_response: Response = requests.get(self.etherscan_api_link, params=abi_params)
        abi_result: Dict = abi_response.json()

        abi: str = abi_result["result"]
        abi_json = json.loads(abi)
        
        byte_params: Dict = {
            "module": "proxy",
            "action": "eth_getCode",
            "address": data['address'],
            "apikey": self.etherscan_api_key
        }
        
        byte_response: Response = requests.get(self.etherscan_api_link, params=byte_params)
        byte_result: Dict = byte_response.json()
        bytecode: str = byte_result["result"][2:]
        
        return {"abi": abi_json, "bytecode": bytecode}

    def save_information_to_file(self, address: str, network: str, information: Dict[str, str]) -> None:
        # Make information directory
        information_dir_name: str = "information"
        if not os.path.exists(information_dir_name):
            os.mkdir(information_dir_name)
            
        # Make address directory
        contract_dir_name: str = os.path.join(information_dir_name, address)
        if not os.path.exists(contract_dir_name):
            os.mkdir(contract_dir_name)
            
        # Save abi, bytecode to file
        abi_file_path: str = os.path.join(contract_dir_name, "abi.json")
        bytecode_file_path: str = os.path.join(contract_dir_name, "bytecode.bin")
        
        with open(abi_file_path, "w") as abi_file:
            json.dump(information["abi"], abi_file, indent=4)
            
        with open(bytecode_file_path, "w") as bytecode_file:
            bytecode_file.write(information["bytecode"])
    
    def manage_fuzzer(self):
        pass
        
    def run_command(self, command: str, timeout: int = 60):
        process: CompletedProcess = subprocess.run(command.split(), capture_output=True, text=True, timeout=timeout, cwd="/home/dev/Smartian")

class IR_fuzzer(Fuzzer):
    def __init__(self) -> None:
        super().__init__()
        
    def manage_fuzzer(self):
        super().manage_fuzzer()
        
        for address in self.addresses:
            os.system(f"python3 downloader.py -d {address['address']} -f .")

class Smartian_fuzzer(Fuzzer):
    def __init__(self, id: str) -> None:
        super().__init__(id)
        pass

    def manage_fuzzer(self, timelimit: int = 60):
        super().manage_fuzzer()
        
        # Make output directory if not exists
        output_dir: str = "output"
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
            
        # Check if there is information directory
        information_dir: str = "information"
        if not os.path.exists(information_dir):
            print("There is no information directory")
            return
        
        # loop in directory
        for contract_dir in os.listdir(information_dir):
            contract_dir_path: str = os.path.join(information_dir, contract_dir)
            
            # read abi, bytecode
            abi_file_path: str = os.path.join(contract_dir_path, "abi.json")
            bytecode_file_path: str = os.path.join(contract_dir_path, "bytecode.bin")

            command: str = f"dotnet build/Smartian.dll fuzz -p {bytecode_file_path} -a {abi_file_path} -t {timelimit} -o {output_dir}"

            self.run_command(command, timelimit)

class ity_fuzzer(Fuzzer):
    def __init__(self, id: str) -> None:
        super().__init__(id)
        pass
        
    def manage_fuzzer(self, data: Dict[str, str], timelimit: int = 60) -> None:
        super().manage_fuzzer()
        
        command: str = f"ityfuzz evm -t {data['address']} -c ETH"
        if data['network'] == "etherscan.io": 
            command += f" --onchain-etherscan-api-key {self.etherscan_api_key}"
            
        self.run_command(command, timelimit)

# example
id: str = "capstone" + sys.argv[1]

# smartian = Smartian_fuzzer(id)
ity = ity_fuzzer(id)

dataset = ity.load_dataset()

for data in dataset:
    # target_dict: Dict[str, str] = smartian.get_information_from_address(data)
    # smartian.save_information_to_file(data['address'], data['network'], target_dict)
    
    # fuzz manage
    # Smartian
    # smartian.manage_fuzzer(60)
    
    # ityfuzzer
    ity.manage_fuzzer(data, 3600)

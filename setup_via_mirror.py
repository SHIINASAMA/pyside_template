import os
import sys

# check using python virtual environment
if sys.prefix == sys.base_prefix:
    print(f'sys.prefix is {sys.prefix}.')
    print(f'sys.base_prefix is {sys.base_prefix}.')
    print('Please run this script from a python virtual environment.')
    exit(1)

os.system('pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple')
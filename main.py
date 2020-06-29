from base_parser import BaseParser
from memory_parser import MemoryParser
from file_list import filename_list

base = BaseParser()
# base.read_cosrad_table("_cosrad/82_2020-3-3_23i16i27.xls")

BRIEF_DATA = "brief_data.txt"


def create_dir(path_dir):
    import os
    if os.path.isdir(path_dir) is False:
        os.mkdir(path_dir)


memory = MemoryParser(BRIEF_DATA, False)

for file, cosrad in filename_list:
    print("{0:s} is being processed".format(file))
    memory.error_parse(file, cosrad)

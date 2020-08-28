from base_parser import BaseParser


class MemoryParser(BaseParser):
    def __init__(self, brief_data_file="brief_data.txt", remove_death_time=False):
        BaseParser.__init__(self, brief_data_file, remove_death_time)
        self.STM_BUFFER_FILL = "FFDA0F00"
        self.STM_MACHINE = "FFDA0F01"
        self.STM_TIMEOUT_SPI = "FFDA0F02"
        self.STM_EVENT_REG = "FFDA0E00"
        self.STM_SH_UNRESET = "FFDA0A00"

        self.SH_START = "F0DA0000"
        self.SH_MEM = ["F0DA1000", "F0DA1001", "F0DA1002", "F0DA1003",
                       "F0DA1004", "F0DA1005", "F0DA1006", "F0DA1007",
                       "F0DA1008"]
        self.MODULE_NAME_LIST = ["DICE",
                                 "DICE_cutWell",
                                 "DICE_band",
                                 "DICE_band_cutWell",
                                 "DFF (with Hamming)",
                                 "Hamming code",
                                 "DICE_band_cutWell (CKLNQD1)",
                                 "DICE_band_cutWell (CGDICE)",
                                 "DFF (without DICE)"]

        self.SYMBOL0 = "5"
        self.SYMBOL1 = "A"
        self.REFERENCE0 = self.SYMBOL0 * 8
        self.REFERENCE1 = self.SYMBOL1 * 8

        self.THRESHOLD = 64
        self.RANGE_GROUP = 64

        self.brief_file = brief_data_file
        self.errors_dict = {module: [0, []] for module in self.SH_MEM}
        self.multiple_errors_dict = {module: [0, []] for module in self.SH_MEM}
        self.module_name = {module: name for module, name in zip(self.SH_MEM, self.MODULE_NAME_LIST)}

    def reset_error_dict(self):
        self.errors_dict = {module: [0, []] for module in self.SH_MEM}
        self.multiple_errors_dict = {module: [0, []] for module in self.SH_MEM}

    def div_into_groups(self, massive):
        import math
        div_massive = []
        group = []
        group_address = int(massive[0][2], 16)
        for i, frame in enumerate(massive):
            address = int(frame[2], 16)
            if math.fabs(address - group_address) > self.RANGE_GROUP:
                if len(group) > 1:
                    div_massive.append(group)
                group = [frame]
            else:
                group.append(frame)
            group_address = address
        if len(group) > 1:
            div_massive.append(group)
        return div_massive

    def find_error(self, massive, cosrad):
        import operator

        self.reset_error_dict()
        self.div_line(massive)
        f_number_errors = False
        f_errors = False
        number_errors = 0
        count_errors = 0
        opcode = ""
        address = ""
        package_errors = []
        number_package_errors = 0
        for date, time, fact in self.div_data:
            if fact == self.STM_BUFFER_FILL or fact == self.STM_MACHINE or fact == self.STM_TIMEOUT_SPI \
                    or fact == self.STM_EVENT_REG or fact == self.STM_SH_UNRESET or fact == self.SH_START:
                f_number_errors = False
                f_errors = False
                number_errors = 0
                count_errors = 0

            elif fact in self.SH_MEM:
                opcode = fact
                f_number_errors = True

            elif f_number_errors is True:
                f_number_errors = False
                if int(fact, 16) > 0:
                    f_errors = True
                    number_errors = int(fact, 16) if int(fact, 16) < self.THRESHOLD else self.THRESHOLD
                    count_errors = 0

            elif f_errors is True:
                if count_errors < number_errors * 2:
                    if fact != self.REFERENCE0 and fact != self.REFERENCE1 and count_errors % 2 == 1:
                        number_5 = fact.count(self.SYMBOL0)
                        number_a = fact.count(self.SYMBOL1)
                        if address != "00001200" and address != "00001210":
                            pattern = self.REFERENCE0 if number_5 > number_a else self.REFERENCE1
                        else:
                            pattern = "00000000"
                        error_xor = "{0:032b}".format(operator.xor(int(fact, 16), int(pattern, 16)))
                        package_errors.append([date, time, address, error_xor])
                        number_package_errors += sum([int(i) for i in error_xor])
                    elif count_errors % 2 == 0:
                        address = fact
                    count_errors += 1

                if count_errors == number_errors * 2:
                    f_errors = False
                    if len(package_errors) > 0:
                        self.errors_dict[opcode][0] += number_package_errors
                        self.errors_dict[opcode][1].append(package_errors)
                        mult_errors_list = self.div_into_groups(package_errors)
                        if len(mult_errors_list) > 1:
                            # self.multiple_errors_dict[opcode][0] += number_package_errors
                            self.multiple_errors_dict[opcode][1].append(mult_errors_list)
                    number_package_errors = 0
                    package_errors = []

    @staticmethod
    def create_dir(path_dir):
        import os
        if os.path.isdir(path_dir) is False:
            os.mkdir(path_dir)

    @staticmethod
    def gen_filename(filename):
        import os
        return os.path.split(os.path.splitext(filename)[0])[1] + ".txt"

    def print_errors(self, filename_out, errors_dict):
        import json
        for module_opcode, error_pack in errors_dict.items():
            module_name = self.module_name[module_opcode]
            error_list = error_pack[1]
            error_file = f"{module_name}/{filename_out}"
            self.create_dir(module_name)
            with open(error_file, 'w') as f:
                json.dump(error_list, f, indent=2)

    def print_brief_errors(self, filename_out, errors_dict):
        with open(self.brief_file, 'a') as f:
            brief_data_list = [f"{filename_out}\n  Errors\n"]
            for module_opcode, error_pack in errors_dict.items():
                module_name = self.module_name[module_opcode]
                number_errors = error_pack[0]
                brief_data_list.append("    {0:<27s}: {1:d}\n".format(module_name, number_errors))
            brief_data_list.append("\n")
            f.writelines(brief_data_list)

    def error_parse(self, filename, cosrad):
        import os
        with open(filename, 'r') as f:
            line_list = f.readlines()

        self.find_error(line_list, cosrad)
        self.print_errors(self.gen_filename(filename), self.errors_dict)
        self.print_errors("multiple_" + self.gen_filename(filename), self.multiple_errors_dict)
        self.print_brief_errors(filename, self.errors_dict)
        # multiple_error_name_split = os.path.split(filename)
        # multiple_error_name = multiple_error_name_split[0] + "/multiple_" + multiple_error_name_split[1]
        # self.print_brief_errors(multiple_error_name, self.multiple_errors_dict)


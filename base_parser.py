class BaseParser:
    def __init__(self, brief_data_file="brief_data.txt", remove_death_time=False):
        with open(brief_data_file, 'w'):
            pass

        self.FLUX_THRESHOLD = 1.0
        self.remove_death_time = remove_death_time

        self.cosrad_table = []
        self.div_data = []

    def read_cosrad_table(self, filename):
        with open(filename, 'r') as f:
            f.readline()
            table = []
            for line in f.readlines():
                table.append(line[:-1].split('\t'))

        for row in table:
            datetime_now = row[1]
            flux = float(row[2])
            full_date_list = datetime_now.split()  # datetime_now in format "YYYY-MM-DD HH:MM:SS"
            date_list = full_date_list[0].split('-')
            date = "{0:s}.{1:s}.{2:s}".format(date_list[2], date_list[1], date_list[0])
            time = "{0:s}.000000".format(full_date_list[1])
            self.cosrad_table.append([date, time, flux])

    def div_line(self, massive):
        self.div_data = []
        for line in massive:
            self.div_data.append(line[:-1].split())

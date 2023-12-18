class Stations():
    def __init__(self):
        bbc_1 = _Station( "bbc_1", "bbc_1.m3u8", "https://sounds.files.bbci.co.uk/3.5.0/networks/bbc_radio_one/colour_default.svg")
        bbc_2 = _Station( "bbc_2", "bbc_2.m3u8", "https://sounds.files.bbci.co.uk/3.1.5/networks/bbc_radio_two/colour_default.svg")
        bbc_3 = _Station( "bbc_3", "bbc_3.m3u8", "https://sounds.files.bbci.co.uk/3.5.0/networks/bbc_radio_three/colour_default.svg")
        bbc_4 = _Station( "bbc_4", "bbc_4.m3u8", "https://sounds.files.bbci.co.uk/3.1.5/networks/bbc_radio_four/colour_default.svg")
        bbc_6 = _Station( "bbc_6", "bbc_6.m3u8", "https://sounds.files.bbci.co.uk/3.1.5/networks/bbc_6music/colour_default.svg")


        self.station_dictionary = {
                            bbc_1.name: bbc_1, 
                            bbc_2.name: bbc_2, 
                            bbc_3.name: bbc_3, 
                            bbc_4.name: bbc_4, 
                            bbc_6.name: bbc_6
                            }


    def station_names(self):
        return list(self.station_dictionary.keys())


    def station_for_display(self, station_name):
        return (self.station_dictionary[station_name].path_icon, station_name)


class _Station():
    def __init__(self, name, path_m3u8, path_icon ) -> None:
        self.name = name
        self.path_m3u8 = path_m3u8
        self.path_icon = path_icon

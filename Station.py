class Stations():
    def __init__(self):
        bbc_4 = _Station( "bbc_4.m3u8", "https://sounds.files.bbci.co.uk/3.1.5/networks/bbc_radio_four/colour_default.svg")
        bbc_6_Music = _Station( "bbc_6.m3u8", "https://sounds.files.bbci.co.uk/3.1.5/networks/bbc_6music/colour_default.svg")
        
        self.Station_list = {
                            "bbc_4": bbc_4, 
                            "bbc_6": bbc_6_Music
                            }    

class _Station():
    def __init__(self, path_m3u8, path_icon ) -> None:
        self.path_m3u8 = path_m3u8
        self.path_icon = path_icon
    
    def path_icon(self):
        print(f"### Icon Path: {self.path_icon}")
        return self.path_icon 
    
    def path_m3u8(self):
        return self.path_m3u8 

# def get_station_list():
#     bbc_4 = Station( "bbc_4.m3u8", "https://sounds.files.bbci.co.uk/3.1.5/networks/bbc_radio_four/colour_default.svg")
#     bbc_6_Music = Station( "bbc_6.m3u8", "https://sounds.files.bbci.co.uk/3.1.5/networks/bbc_6music/colour_default.svg")
    
#     Station_list = {"bbc_4": bbc_4, 
#                     "bbc_6": bbc_6_Music
#                     }
    
#     return Station_list



        
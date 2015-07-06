from collections import defaultdict
import json

class Anycast():
    

    def __init__(self, file_input):
        self.anycast_dic=defaultdict(list)
        anycast_data=open(file_input,'r')
        for line in anycast_data.readlines():
            if not line.startswith( '#' ):
                hostname,latitude,longitude,radius,iata_code,latitude_city,longitude_city,city,IP24,IP32,country=line.strip().split("\t")
                self.anycast_dic[IP24.split("/")[0]].append([city,country,latitude_city,longitude_city])

    def detection(self,ip24):

        if ip24 in self.anycast_dic:
            return True
        else:
             return False

    def enumeration(self,ip24):

        if self.detection(ip24) :
            return len(self.anycast_dic[ip24])
        else:
             return False

    def geolocation(self,ip24):

        if self.enumeration(ip24)>0:
            labels=["city","country","latitude_city","longitude_city"]
            json_data=[]
            for instance in self.anycast_dic[ip24]:
                geolocation = {}
                i=0
                for item in instance:  
                    geolocation[labels[i]] = item
                    json_data.append(geolocation)
                    i+=1
                return json.dumps(json_data)
        else:
             return False


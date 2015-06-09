# Quik and dirty code to transform rrd files name to some understandable name 
#               Author: Ali Safari Khatouni
#

graphite_delimiter = "."
profile_prefix = "profile"
ip_prefix = "ip"
bitrate_prefix = "bitrate"
packet_len_prefix = "packet_length"
protocol_prefix = "protocol"
tcp_prefix = "tcp"
port_destination_prefix = "port_dst"
port_destination_syn_segment_prefix = "port_syndst"
rtt_prefix = "rtt"
connection_len_prefix = "cl_b_s"
s2c = "s2c" 
c2s = "c2s"
total_time_prefix = "tot_time"
tcp_option_prefix = "opts"
MPTCP = "MPTCP"
SACK = "SACK"
WS = "WS"
TS = "TS"
throughput_prefix = "thru"
anomalies_prefix = "anomalies"
udp_prefix = "udp"
flow_prefix = "flow"
connection_len_udp_prefix = "cl_p"
chat_prefix = "chat_flow_num"
rtcp_prefix = "rtcp"
mm_flow_bitrate_prefix = "mm_bt"
mm_flow_length_byte_prefix = "mm_cl_b"
mm_flow_length_packet_prefix = "mm_cl_p"
flow_bitrate_prefix = "bt"
duplicate_prefix = "dup"
flow_length_byte_prefix = "cl_b"
flow_length_packet_prefix = "cl_p"
fraction_lost_prefix = "f_lost"
lost_prefix = "lost"
rtp_prefix = "rtp"
payload_type_prefix = "mm_rtp_pt"
stream_prefix = "mm" 
ipg_prefix = "avg_ipg"
jitter_prefix = "avg_jitter"
connection_len_long_flow_prefix = "cl_b"
connection_short_packet_prefix = "cl_p_s"
short_lifetime_prefix = "tot_time_s"
number_out_of_sequence_prefix = "n_oos"
duplicate_packet_prefix = "p_dup"
probability_out_of_sequence_prefix = "p_oos"
type_prefix = "type"
uni_multicast_prefix = "uni_multi"
http_prefix = "http_bitrate"
http_flow_number_prefix = "L7_HTTP_num"
tcp_flow_number_prefix = "L7_TCP_num"
udp_flow_number_prefix = "L7_UDP_num"
layer_4_prefix = "L4_flow_number"
tcp_bitrate_prefix = "tcp_bitrate"
udp_bitrate_prefix = "udp_bitrate"
web_bitrate_prefix = "web_bitrate"
web_flow_prefix = "L7_WEB_num"
video_rate_prefix = "video_rate"
video_flow_prefix = "L7_VIDEO_num"
interrupt_prefix = "interrupted"


def rrd_file_classification (filename):
    readable_name = ""

    filename = filename.replace(".rrd", "")
    filename = filename.replace(".","_")

    fields = filename.split("_")

    if (rtcp_prefix in fields[0]):
        readable_name =  rtcp_classifier(filename)


    elif (rtp_prefix in filename):
        readable_name = rtp_prefix + graphite_delimiter

        if (payload_type_prefix in filename):
            readable_name += "Payload type" + graphite_delimiter
            readable_name += in_out_local(filename)
            readable_name += rtp_index_decoder (extract_index(filename))

    elif(stream_prefix in fields[0]):
        readable_name = stream_classifier(filename)


    elif (profile_prefix in fields[0] ):
        readable_name = profile_prefix + graphite_delimiter
        readable_name += profile_name_extract(filename)

    elif (ip_prefix in fields[0]):
        readable_name = ip_prefix + graphite_delimiter
        readable_name += ip_name_extract(filename)

 
    elif (chat_prefix in filename):
        readable_name = chat_prefix + graphite_delimiter
        readable_name += chat_index_decoder (extract_index(filename))

    elif (http_prefix in filename):
        readable_name = http_prefix + graphite_delimiter
        readable_name += in_out_local(filename)
        readable_name += http_index_decoder (extract_index(filename))

    elif (http_flow_number_prefix in filename):
        readable_name = "number of tracked http flows" + graphite_delimiter
        readable_name += in_out_local(filename)
        readable_name += http_index_decoder (extract_index(filename))

    elif (tcp_flow_number_prefix in filename):
        readable_name = "number of tracked tcp flows" + graphite_delimiter
        readable_name += in_out_local(filename)
        readable_name += application_index_decoder (extract_index(filename))

    elif (layer_4_prefix in filename):
        readable_name = "number of tracked tcp_udp flows" + graphite_delimiter
        if (extract_index(filename) == "0"):
            readable_name += "TCP" 

        elif (extract_index(filename) == "1"):
            readable_name += "UDP" 

    elif (tcp_bitrate_prefix in filename):
        readable_name = "TCP bitrate bit sec" + graphite_delimiter
        readable_name += in_out_local(filename)
        readable_name += application_index_decoder (extract_index(filename))


    elif (udp_bitrate_prefix in filename):
        readable_name = "UDP bitrate bit sec" + graphite_delimiter
        readable_name += in_out_local(filename)
        readable_name += application_index_decoder (extract_index(filename))

    elif (udp_flow_number_prefix in filename):
        readable_name = "number of tracked udp flows" + graphite_delimiter
        readable_name += in_out_local(filename)
        readable_name += application_index_decoder (extract_index(filename))


    elif (web_bitrate_prefix in filename):
        readable_name = "WEB bitrate bit sec" + graphite_delimiter
        readable_name += in_out_local(filename)
        readable_name += http_index_decoder (extract_index(filename))

    elif (web_flow_prefix in filename):
        readable_name = "HTTP flow number" + graphite_delimiter
        readable_name += in_out_local(filename)
        readable_name += http_index_decoder (extract_index(filename))


    elif (video_rate_prefix in filename):
        readable_name = "video over http bitrate" + graphite_delimiter
        readable_name += in_out_local(filename)
        readable_name += video_index_decoder (extract_index(filename))

    elif (video_flow_prefix in filename):
        readable_name = "video over http number of flow" + graphite_delimiter
        readable_name += in_out_local(filename)
        readable_name += video_index_decoder (extract_index(filename))


    elif (tcp_prefix in fields[0]):
        readable_name = tcp_classifier(filename)


    elif (udp_prefix in fields[0] and (("port" in filename) or (connection_len_udp_prefix in filename))):
        readable_name = udp_prefix + graphite_delimiter

        if ("port" in filename):
            readable_name += udp_port_extract(filename)

        elif(connection_len_udp_prefix in filename):
            readable_name += in_out_local(filename)
            readable_name += tcp_connection_length_extract(filename)

    else:
        print ("UNKNOWN FIX ME" + str(filename))


    readable_name = readable_name.replace(" ", "_")
    return readable_name


def tcp_classifier (filename):

    readable_name = ""

    fields = filename.split("_")

    if (tcp_prefix in fields[0]):
        readable_name = tcp_prefix + graphite_delimiter
        if ("port" in filename):
            readable_name += tcp_port_extract(filename)

        elif (rtt_prefix in filename):
            readable_name += tcp_rtt_extract(filename)

        elif(connection_len_prefix in filename):
            readable_name += tcp_connection_length_extract(filename)

        elif(total_time_prefix in filename):
            readable_name += tcp_total_time_extract(filename)

        elif(tcp_option_prefix in filename):
            readable_name += tcp_option_extract(filename)

        elif(throughput_prefix in filename):
            readable_name += tcp_throughput_extract(filename)

        elif(anomalies_prefix in filename):
            readable_name += tcp_anomalies_extract(filename)

        elif(interrupt_prefix in filename):
            readable_name += interrupt_prefix + graphite_delimiter
            readable_name += extract_index(filename)

    return readable_name


def stream_classifier(filename):

    readable_name = ""

    fields = filename.split("_")

    if(stream_prefix in fields[0]):
        readable_name = "Stream" + graphite_delimiter
        if (ipg_prefix in filename):
            readable_name += "average IPG" + graphite_delimiter

        elif(jitter_prefix in filename):
            readable_name += "average jitter" + graphite_delimiter

        elif(bitrate_prefix in filename):
            readable_name += "average bitrate" + graphite_delimiter

        elif(connection_len_prefix in filename):
            readable_name += "short flow length(bytes)" + graphite_delimiter

        elif(connection_len_long_flow_prefix in filename):
            readable_name += "long flow length(bytes)" + graphite_delimiter 

        elif(connection_short_packet_prefix in filename):
            readable_name += "short flow length(packets)" + graphite_delimiter

        elif( connection_len_udp_prefix in filename):
            readable_name += "long flow length(packets)" + graphite_delimiter 

        elif(short_lifetime_prefix in filename):
            readable_name += "short flow lifetime" + graphite_delimiter

        elif( total_time_prefix in filename):
            readable_name += "long flow lifetime" + graphite_delimiter 

        elif( number_out_of_sequence_prefix in filename):
            readable_name += "num out of sequence" + graphite_delimiter 

        elif( duplicate_packet_prefix in filename):
            readable_name += "duplicate packet" + graphite_delimiter 

        elif( probability_out_of_sequence_prefix in filename):
            readable_name += "probability out of sequence" + graphite_delimiter 




        readable_name += in_out_local(filename)
        readable_name += measure_type(filename)

        if(type_prefix in filename):
            readable_name += "type" + graphite_delimiter 
            readable_name += stream_index_decoder (extract_index(filename))

        if(uni_multicast_prefix in filename):
            readable_name += "unicast_multicast" + graphite_delimiter
            readable_name += in_out_local(filename)
            readable_name += multicast_index_decoder (extract_index(filename))

    return readable_name




def rtcp_classifier(filename):

    readable_name = ""

    fields = filename.split("_")

    if (rtcp_prefix in fields[0]):
        readable_name = rtcp_prefix + graphite_delimiter

        if (mm_flow_bitrate_prefix in filename):
            readable_name += "mm flow bitrate" + graphite_delimiter

        elif (mm_flow_length_byte_prefix in filename):
            readable_name += "mm flow length (bytes)" + graphite_delimiter

        elif (mm_flow_length_packet_prefix in filename):
            readable_name += "mm flow length (packets)" + graphite_delimiter

        elif (flow_bitrate_prefix in filename):
            readable_name += "flow bitrate" + graphite_delimiter

        elif (duplicate_prefix in filename):
            readable_name += "duplicate packet" + graphite_delimiter

        elif (flow_length_byte_prefix in filename):
            readable_name += "flow length (bytes)" + graphite_delimiter

        elif (flow_length_packet_prefix in filename):
            readable_name += "flow length (packets)" + graphite_delimiter

        elif (fraction_lost_prefix in filename):
            readable_name += "fraction of lost packets" + graphite_delimiter

        elif (lost_prefix in filename):
            readable_name += "lost packets" + graphite_delimiter

        elif (rtt_prefix in filename):
            readable_name += "Round trip times" + graphite_delimiter

        readable_name += in_out_local(filename)
        readable_name += measure_type(filename)

        return readable_name




def profile_name_extract (filename):
    output = ""
    if ("cpu" in filename):
        output += "CPU_LOAD_Percentage" + graphite_delimiter
        if ("idx0" in filename):
            output += "Maximum_Overall_CPU"
        elif ("idx1" in filename):
            output += "Average_User_CPU"
        elif ("idx2" in filename):
            output += "Average_System_CPU"
        else:
            output += str(filename)

    if ("trash" in filename):
        output += "Number_of_Ignored_Packets"+ graphite_delimiter+ "Ignored_TCP_Packets"

    if ("tcpdata" in filename):
        output += "Overall_TCP_volume" + graphite_delimiter
        if ("idx0" in filename):
            output += "Received_TCP_Mbytes"
        elif ("idx1" in filename):
            output += "Missed_TCP_Mbytes"
        else:
            output += str(filename)


    if ("flows" in filename):
        output += "Active_or_Missed_TCP_or_UDP_flows" + graphite_delimiter
        if ("idx0" in filename):
            output += "Missed UDP Flows"
        elif ("idx1" in filename):
            output += "Active UDP Flows"
        elif ("idx2" in filename):
            output += "Missed TCP Flows"
        elif ("idx3" in filename):
            output += "Active TCP Flows"
        else:
            output += str(filename)

    return output


def ip_name_extract (filename):

    output = ""
    fields = filename.split("_")
    field = fields[1]
    prc_field = fields[-1]

    if ("bitrate" in field):
        output +=  bitrate_prefix + graphite_delimiter
        output += in_out_local(filename) 

        if ("idx0" in filename):
          output += "TCP"
        elif ("idx1" in filename):
            output += "UDP"
        elif ("idx2" in filename):
           output += "ICMP"
        else:
            output += str(filename)


    if ("len" in field):
        output +=  packet_len_prefix + graphite_delimiter
        output += in_out_local(filename) 
        
        if ("avg" in prc_field):
            output += "Average"
        elif("prc" in prc_field):
            output += "quantile_"
            output += extract_prc(filename)
        elif("idx" in prc_field):
            output += "specific_value" + graphite_delimiter 
            output += extract_index(filename)
        else:
            output += str(filename)

    if ("protocol" in field):
        output +=  protocol_prefix + graphite_delimiter
        output += in_out_local(filename)
        if("idx" in filename):
            output += index_decoder_ip( extract_index(filename) )
        else:
            output += str(filename)
    return output






def in_out_local(filename):

    fields = filename.split("_")

    if ("in" in fields[-2]):
        output = "in" + graphite_delimiter
    elif("out" in fields[-2]):
        output = "out" + graphite_delimiter
    elif("loc" in fields[-2]):
        output = "local" + graphite_delimiter
    else:
        output = "Unkown_in_out_loc" + graphite_delimiter

    return output

def extract_prc(filename):

    fields = filename.split('_')
    field = fields[-1]

    if "prc" in field:
        quantile = field.replace("prc","")
        quantile = quantile.replace("oth","oth")
        return quantile

def extract_index(filename):

    fields = filename.split('_')
    field = fields[-1]

    if "idx" in field:
        quantile = field.replace("idx","")
        quantile = quantile.replace("oth","oth")
        return quantile


def index_decoder_ip(index):
    output = ""
    if(index == "17"):
        output = "UDP"
    elif(index == "6"):
        output = "TCP"
    elif(index == "1"):
        output = "ICMP"
    else:
        output = "OTHERS"
    return output

def port_decoder_tcp(index):
    output = ""
    if(index == "8080"):
        output = "Squid"
    elif(index == "6881"):
        output = "BitTorrent"
    elif(index == "6699"):
        output = "WinMX"
    elif(index == "4662"):
        output = "eDonkey-DATA"
    elif(index == "4661"):
        output = "eDonkey-Lookup"
    elif(index == "3389"):
        output = "RDP"
    elif(index == "1433"):
        output = "Ms-SQL"
    elif(index == "1214"):
        output = "KaZaa"
    elif(index == "445"):
        output = "Microsoft-ds"
    elif(index == "443"):
        output = "HTTPS"
    elif(index == "143"):
        output = "IMAP"
    elif(index == "119"):
        output = "NNTP"
    elif(index == "110"):
        output = "POP3"
    elif(index == "80"):
        output = "HTTP"
    elif(index == "25"):
        output = "SMTP"
    elif(index == "23"):
        output = "telnet"
    elif(index == "22"):
        output = "SSH"
    elif(index == "21"):
        output = "FTP"
    elif(index == "20"):
        output = "FTP-DATA"
    else:
        output = "OTHERS"
    return output



def tcp_port_extract(filename):
    output = ""

    if (port_destination_prefix in filename):
        output += port_destination_prefix + graphite_delimiter
        output += in_out_local(filename)

    if (port_destination_syn_segment_prefix in filename):
        output += port_destination_syn_segment_prefix + graphite_delimiter
        output += in_out_local(filename)


    if ("idx" in filename):
        output += port_decoder_tcp( extract_index(filename) )

    return output


def tcp_rtt_extract(filename):
    output = ""


    if (rtt_prefix in filename):
        output += rtt_prefix + graphite_delimiter
        output += in_out_local(filename)
        output += measure_type(filename)

    return output

def measure_type(filename):

    output = ""
    fields = filename.split("_")
    field = fields[-1]

    if ("max" in field):
        output += "Maximum" 

    elif ("stdev" in field):
        output += "Stdev"

    elif ("min" in field):
        output += "Minimum"

    elif ("prc" in field):
        output += "quantile_"  
        output += extract_prc(filename)

    elif ("avg" in field):
       output += "Average" 

    else:
        output += "Unknown_filename"


    return output

def tcp_connection_length_extract(filename):
    output = "flow_length" + graphite_delimiter

    if (c2s in filename):
        output += c2s + graphite_delimiter
    elif(s2c in filename):
        output += s2c + graphite_delimiter
    else:
        output += ""

    output += measure_type(filename)

    return output

def tcp_total_time_extract(filename):

    output = "flow_lifetime" + graphite_delimiter
    output += measure_type(filename)

    return output



def tcp_option_extract(filename):

    output = "OPTION" + graphite_delimiter

    if (MPTCP in filename):
        output = MPTCP + graphite_delimiter

    elif(SACK in filename):
        output = SACK + graphite_delimiter        

    elif(WS in filename):
        output = "WindowScale" + graphite_delimiter        

    else:
        output = "TimeStamp" + graphite_delimiter        


    output += tcp_option_index_extract(extract_index(filename))

    return output

def tcp_option_index_extract(filename):
    output = ""

    if(filename == "1"):
        output = "OK"

    elif(filename == "2"):
        output = "Client_Offer"

    elif(filename == "3"):
        output = "Server_Offer"

    else:
        output = "NO"

    return output


def tcp_throughput_extract(filename):

    output = "Throughput" + graphite_delimiter
    if ("lf" in filename ):
        output += "Large_flows" + graphite_delimiter

    if (c2s in filename):
        output += c2s + graphite_delimiter
    else:
        output += s2c + graphite_delimiter


    output += measure_type(filename)

    return output


def tcp_anomalies_extract(filename):

    output = anomalies_prefix + graphite_delimiter
    output += in_out_local(filename) 

    output += tcp_anomalies_decoder(extract_index(filename))

    return output 

def tcp_anomalies_decoder(filename):
    output = ""

    if(filename == "0"):
        output = "In_sequence"

    elif(filename == "1"):
        output = "Rter_by_RTO"

    elif(filename == "2"):
        output = "Retr_by_Fast_Retransmit"

    elif(filename == "3"):
        output = "Network_Reordering"

    elif(filename == "4"):
        output = "Network_Duplicate"

    elif(filename == "5"):
        output = "Flow_Control_(Window_Probing)"

    elif(filename == "6"):
        output = "Unnecessary_Retr_by_RTO"

    elif(filename == "6"):
        output = "Unnecessary_Retr_by_Fast_Retransmit"

    elif(filename == "63"):
        output = "Unknown"

    else:
        output = "Unknown2"


    return output




def udp_port_extract(filename):
    output = ""

    if (port_destination_prefix in filename):
        output += port_destination_prefix + graphite_delimiter
        output += in_out_local(filename)

    if (flow_prefix in filename):
        output += flow_prefix + graphite_delimiter
        output += in_out_local(filename)


    if ("idx" in filename):
        output += port_decoder_udp( extract_index(filename) )

    return output


def port_decoder_udp(index):
    output = ""
    if(index == "6346"):
        output = "Gnutella-svc"

    elif(index == "4672"):
        output = "eDonkey"

    elif(index == "137"):
        output = "NETBIOS"

    elif(index == "123"):
        output = "NTP"

    elif(index == "69"):
        output = "TFTP"

    elif(index == "68"):
        output = "BOOTPC"

    elif(index == "67"):
        output = "Ms-BOOTPS"

    elif(index == "53"):
        output = "DNS"

    else:
        output = "OTHERS"

    return output


def chat_index_decoder(filename):
    output = ""

    if(filename == "0"):
        output = "MSN chat session number"

    elif(filename == "1"):
        output = "MSN presence session number"

    elif(filename == "2"):
        output = "Jabber chat session number"

    elif(filename == "3"):
        output = "Jabber presence session number"

    elif(filename == "4"):
        output = "YAHOO chat session number"

    elif(filename == "5"):
        output = "YAHOO presence session number"

    else:
        output = "Unknown2"


    return output

def rtp_index_decoder(filename):
    output = ""

    if(filename == "0"):
        output = "ITU G.711 u-law"

    elif(filename == "8"):
        output = "ITU G.711 a-law"

    elif(filename == "14"):
        output = "MPA"

    elif(filename == "31"):
        output = "H261"

    elif(filename == "32"):
        output = "MPV"

    elif(filename == "33"):
        output = "MP2T"

    elif(filename == "96"):
        output = "dynamic video"

    elif(filename == "97"):
        output = "dynamic video"

    elif(filename == "oth"):
        output = "Others"

    else:
        output = "Unknown2"


    return output



def stream_index_decoder(filename):
    output = ""

    if(filename == "4"):
        output = "RTP over UDP"

    elif(filename == "6"):
        output = "RTP over RTSP"

    elif(filename == "7"):
        output = "RTP over HTTP or RTSP"

    elif(filename == "8"):
        output = "ICY"

    else:
        output = "Unknown"


    return output



def multicast_index_decoder(filename):
    output = ""

    if(filename == "0"):
        output = "unicast"

    elif(filename == "1"):
        output = "multicast"

    else:
        output = "Unknown"


    return output


def http_index_decoder(filename):
    output = ""

    if(filename == "0"):
        output = "GET"

    elif(filename == "1"):
        output = "POST"

    elif(filename == "2"):
        output = "MSN"

    elif(filename == "3"):
        output = "RTMPT"

    elif(filename == "4"):
        output = "YouTube"

    elif(filename == "5"):
        output = "Video Content"

    elif(filename == "6"):
        output = "Vimeo"

    elif(filename == "7"):
        output = "Wikipedia"

    elif(filename == "8"):
        output = "RapidShare"

    elif(filename == "9"):
        output = "Netload"

    elif(filename == "10"):
        output = "Facebook"

    elif(filename == "11"):
        output = "Web Ads"

    elif(filename == "12"):
        output = "Flickr"

    elif(filename == "13"):
        output = "Google Maps"

    elif(filename == "15"):
        output = "YouTube Site"

    elif(filename == "16"):
        output = "Social"

    elif(filename == "17"):
        output = "Other Video"

    elif(filename == "18"):
        output = "Mediafire"

    elif(filename == "19"):
        output = "Hotfile_com"

    elif(filename == "20"):
        output = "Storage_to"


    else:
        output = "Unknown"
    return output


def application_index_decoder(filename):
    output = ""

    if(filename == "0"):
        output = "HTTP"

    elif(filename == "1"):
        output = "RTP"

    elif(filename == "2"):
        output = "RTCP"

    elif(filename == "3"):
        output = "ICY"

    elif(filename == "4"):
        output = "RTSP"

    elif(filename == "5"):
        output = "Skype E2E"

    elif(filename == "6"):
        output = "Skype E20"

    elif(filename == "7"):
        output = "Skype TCP"

    elif(filename == "8"):
        output = "Messenger"

    elif(filename == "9"):
        output = "Jabber or GTalk"

    elif(filename == "10"):
        output = "Yahoo! Msg"

    elif(filename == "11"):
        output = "Emule-ED2K"

    elif(filename == "12"):
        output = "Emule-KAD"

    elif(filename == "13"):
        output = "Emule-KADu"

    elif(filename == "14"):
        output = "GNUtella"

    elif(filename == "15"):
        output = "Bittorrent"

    elif(filename == "16"):
        output = "Kazaa"

    elif(filename == "17"):
        output = "DirectConnect"

    elif(filename == "19"):
        output = "Soulseek"

    elif(filename == "25"):
        output = "SMTP"

    elif(filename == "26"):
        output = "POP3"

    elif(filename == "27"):
        output = "IMAP"

    elif(filename == "28"):
        output = "ED2K Obfuscated"

    elif(filename == "29"):
        output = "PPLive"

    elif(filename == "30"):
        output = "Sopcast"

    elif(filename == "31"):
        output = "TVAnts"

    elif(filename == "32"):
        output = "Skype SIG"

    elif(filename == "33"):
        output = "SSL TLS"

    elif(filename == "34"):
        output = "KAD Obfuscated"

    elif(filename == "36"):
        output = "DNS"

    elif(filename == "37"):
        output = "SSH"

    elif(filename == "38"):
        output = "RTMP"

    elif(filename == "39"):
        output = "BT-MSE PE"

    elif(filename == "40"):
        output = "MPEG2 VOD"

    elif(filename == "41"):
        output = "PPStream"

    elif(filename == "42"):
        output = "Teredo"

    elif(filename == "43"):
        output = "SIP"

    elif(filename == "49"):
        output = "Unclassified"

    elif(filename == "oth"):
        output = "Others"


    else:
        output = "unknown"


    return output


def video_index_decoder(filename):
    output = ""

    if(filename == "1"):
        output = "FLV"

    elif(filename == "2"):
        output = "MP4"

    elif(filename == "3"):
        output = "AVI"

    elif(filename == "4"):
        output = "WMV"

    elif(filename == "5"):
        output = "MPEG"

    elif(filename == "6"):
        output = "WEBM"

    elif(filename == "7"):
        output = "3GPP"

    elif(filename == "8"):
        output = "OGG"

    elif(filename == "9"):
        output = "QuickTime"

    elif(filename == "10"):
        output = "ASF"

    elif(filename == "11"):
        output = "Unknown"

    elif(filename == "12"):
        output = "HLS"

    elif(filename == "13"):
        output = "NFF (Sky-On_Demand)"

    else:
        output = "Unknown"
    return output
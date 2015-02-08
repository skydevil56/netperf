#!/usr/bin/env python
import dpkt
# packets size
count_1_75 = 0
count_76_150 = 0
count_151_225 = 0
count_226_300 = 0
count_301_375 = 0
count_376_450 = 0
count_451_525 = 0
count_526_600 = 0
count_601_675 = 0
count_676_750 = 0
count_751_825 = 0
count_826_900 = 0
count_901_975 = 0
count_976_1050 = 0
count_1051_1125 = 0
count_1126_1200 = 0
count_1201_1275 = 0
count_1276_1350 = 0
count_1351_1425 = 0
count_1426_1500 = 0
# total IP packets counter
count_ip_pkts = 0
# counter for L4 protocols
count_tcp_pkt = 0
count_udp_pkt = 0
# counter for others L4 protocols
count_others_l4_pkt = 0

f = open('/root/test.pcap')
pcap = dpkt.pcap.Reader(f)
for ts, pkt in pcap:
    eth = dpkt.ethernet.Ethernet(pkt)
    ip = eth.data
    # check what L3 proto is IP
    if eth.type == dpkt.ethernet.ETH_TYPE_IP:
        # total IP pckets
        count_ip_pkts += 1
        # total TCP and UDP packets
        if ip.p == dpkt.ip.IP_PROTO_TCP:
            count_tcp_pkt += 1
        elif ip.p == dpkt.ip.IP_PROTO_UDP:
            count_udp_pkt += 1
        else:
            count_others_l4_pkt += 1
        # get IP length
        len = eth.ip.len
        if 1 <= len <= 75:
            count_1_75 += 1
        if 76 <= len <= 150:
            count_76_150 += 1
        if 151 <= len <= 225:
            count_151_225 += 1
        if 226 <= len <= 300:
            count_226_300 += 1
        if 301 <= len <= 375:
            count_301_375 += 1
        if 376 <= len <= 450:
            count_376_450 += 1
        if 451 <= len <= 525:
            count_451_525 += 1
        if 526 <= len <= 600:
            count_526_600 += 1
        if 601 <= len <= 675:
            count_601_675 += 1
        if 676 <= len <= 750:
            count_676_750 += 1
        if 751 <= len <= 825:
            count_751_825 += 1
        if 826 <= len <= 900:
            count_826_900 += 1
        if 901 <= len <= 975:
            count_901_975 += 1
        if 976 <= len <= 1050:
            count_976_1050 += 1
        if 1051 <= len <= 1125:
            count_1051_1125 += 1
        if 1126 <= len <= 1200:
            count_1126_1200 += 1
        if 1201 <= len <= 1275:
            count_1201_1275 += 1
        if 1276 <= len <= 1350:
            count_1276_1350 += 1
        if 1351 <= len <= 1425:
            count_1351_1425 += 1
        if 1426 <= len <= 1500:
            count_1426_1500 += 1
    else:
        continue
f .close()
print """IP packet Size    Count              %
     (bytes)          """
print "   1 to   75:    ", count_1_75, "        ", float(count_1_75) / float(count_ip_pkts) * 100
print "  76 to  150:    ", count_76_150, "        ", float(count_76_150) / float(count_ip_pkts) * 100
print " 151 to  225:    ", count_151_225, "        ", float(count_151_225) / float(count_ip_pkts) * 100
print " 226 to  300:    ", count_226_300, "        ", float(count_226_300) / float(count_ip_pkts) * 100
print " 301 to  375:    ", count_301_375, "        ", float(count_301_375) / float(count_ip_pkts) * 100
print " 376 to  450:    ", count_376_450, "        ", float(count_376_450) / float(count_ip_pkts) * 100
print " 451 to  525:    ", count_451_525, "        ", float(count_451_525) / float(count_ip_pkts) * 100
print " 526 to  600:    ", count_526_600, "        ", float(count_526_600) / float(count_ip_pkts) * 100
print " 601 to  675:    ", count_601_675, "        ", float(count_601_675) / float(count_ip_pkts) * 100
print " 676 to  750:    ", count_676_750, "        ", float(count_676_750) / float(count_ip_pkts) * 100
print " 751 to  825:    ", count_751_825, "        ", float(count_751_825) / float(count_ip_pkts) * 100
print " 826 to  900:    ", count_826_900, "        ", float(count_826_900) / float(count_ip_pkts) * 100
print " 901 to  975:    ", count_901_975, "        ", float(count_901_975) / float(count_ip_pkts) * 100
print " 976 to 1050:    ", count_976_1050, "        ", float(count_976_1050) / float(count_ip_pkts) * 100
print "1051 to 1125:    ", count_1051_1125, "        ", float(count_1051_1125) / float(count_ip_pkts) * 100
print "1126 to 1200:    ", count_1126_1200, "        ", float(count_1126_1200) / float(count_ip_pkts) * 100
print "1201 to 1275:    ", count_1201_1275, "        ", float(count_1201_1275) / float(count_ip_pkts) * 100
print "1276 to 1350:    ", count_1276_1350, "        ", float(count_1276_1350) / float(count_ip_pkts) * 100
print "1351 to 1425:    ", count_1351_1425, "        ", float(count_1351_1425) / float(count_ip_pkts) * 100
print "1426 to 1500:    ", count_1426_1500, "        ", float(count_1426_1500) / float(count_ip_pkts) * 100
print "Common packet statistic"
print "Total IP packets:", count_ip_pkts
print "Total TCP packets:", count_tcp_pkt, "        ", float(count_tcp_pkt) / float(count_ip_pkts) * 100
print "Total UDP packets:", count_udp_pkt, "        ", float(count_udp_pkt) / float(count_ip_pkts) * 100
#!/usr/bin/python

import m3u8
from urllib import urlopen
from sys import argv 
import time


if len(argv) <4 :
	print "usage :%s <m3u8_url> <saved_tsfile> <duration>" , argv[0]
	quit()

ts_file =  open(argv[2], "wb")

retrive_seq = -1 
Err_flag = False

duration = int(argv[3])
if duration <= 0:
	duration = 3600*72
end_time = time.time() + duration

packet_timings = []
last_timing_time = time.time()
last_timing_size = 0
total_size = 0
last_speed_timing_time = time.time()

while time.time() < end_time and not Err_flag :

	m3u8_obj = m3u8.load(argv[1])

	new_seg_flag = False
	print time.strftime('%Y-%m-%d %H:%M:%S ',time.localtime(time.time())) , "#EXT-X-MEDIA-SEQUENCE:", m3u8_obj.media_sequence
	
	seg_seq = m3u8_obj.media_sequence

	for seg in  m3u8_obj.segments:
	
		if m3u8.is_url(seg.uri) :
			segurl = seg.uri
		else :
			segurl =  m3u8.model._urijoin( seg.base_uri ,  seg.uri )
	

		if seg_seq > retrive_seq :
			if retrive_seq>=0 and seg_seq<>retrive_seq+1 :
				print "WARN: SEQ not continue!!!! %d - %d" , retrive_seq , seg_seq 

			retrive_seq = seg_seq		
			new_seg_flag = True

			#print segurl

			start_ts = time.time()
			
			resp = urlopen(segurl)
			if resp.getcode()!=200 :
				print "Error HTTP resp code:" , resp.getcode(), segurl
	        		Err_flag = True
				break	

			doc = resp.read(1408)
			while doc:
				total_size += len(doc)
				cur = time.time()
				# print cur
				if cur - last_timing_time >= 1:
					# print cur
					# print packet_timings
					last_timing_time = cur
					packet_timings.append((last_timing_time, total_size))
					last_timing_size = total_size
					
					delete_to_index = -1
					for i, timing in enumerate(packet_timings):
						timing_time = timing[0]
						timing_size = timing[1]

						if cur - timing_time < 11:
							delete_to_index = i
							break

					if delete_to_index > 0:
						# print delete_to_index, cur
						del packet_timings[:delete_to_index]
					
					if len(packet_timings) >= 2:
						first_timing = packet_timings[0]
						last_timing = packet_timings[-1]
						if cur - last_speed_timing_time > 11:
							last_speed_timing_time = cur
							print 'speed:', (last_timing[1] - first_timing[1]) / (last_timing[0] - first_timing[0]) / 1024, 'time span:', last_timing[0] - first_timing[0]
							

				doc = resp.read(1408)
				pass
			
			resp.close()

			end_ts  = time.time()
			size = len(doc)
			dur = end_ts-start_ts
	
			# if dur > 8 :
   #                      	print "Error TOO SLOW!!!!! " ,  dur, size , size*8/dur/1024,  " - ", segurl 
   #              	else:
   #                  		print dur, size , size*8/dur/1024,  " - ", segurl

			# ts_file.write(doc)     
		
		seg_seq = seg_seq + 1
		
	if m3u8_obj.is_endlist:
		break;
	elif not new_seg_flag :
		time.sleep(5) 
	 	print "sleep 5s..." 


ts_file.close()

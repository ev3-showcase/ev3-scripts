#!/bin/bash

# Update the video-stream script
wget --quiet --spider https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/video-stream.sh
if [ $? -eq 0 ] ; then
    # If the file exists download and overwrite
    wget -O video-stream.sh https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/video-stream.sh
fi
chmod u+x video-stream.sh

# Load Environment Variables
export $(grep -v '^#' .env | xargs)

expiry=$(date -d "today + 24 hours" +%s)

server=$LEGOCAR_VIDEO_SERVER
path="/live/car-cloudhub"
token=$LEGOCAR_VIDEO_SERVER_TOKEN

hashString="${path}-${expiry}-${token}"

md5hash=$(echo -n $hashString | md5sum | head -c 32)


url="${server}${path}?sign=${expiry}-${md5hash}"
echo $url

# Fastest so far: 
raspivid -a 12 -w 640 -h 480 -fps 10 -b 500000 -t 0 -o - | ffmpeg -y -f h264     -i -     -c:v copy     -map 0:0     -f flv     -rtmp_buffer 100 -rtmp_live live     -preset veryfast     $url




# raspivid -a 12 -w 640 -h 480 -fps 10 -b 500000 -t 0 -o - | ffmpeg \
#     -y \
#     -f h264 -r 10\
#     -i - \
#     -c:v copy \
#     -map 0:0 \
#     -f flv \
#     -rtmp_buffer 100 \
#     -rtmp_live live \
#     -preset veryfast \
#     rtmp://104.45.150.248:1935/live/car-cloudhub
#     -fflags nobuffer


# raspivid -a 12 -w 640 -h 480 -fps 10 -b 500000 -t 0 -o - | ffmpeg   
#   -y     -f h264   -i -     -c:v copy     -map 0:0     -f flv     -rtmp_buffer 100   
#     -rtmp_live live     -preset veryfast     rtmp://104.45.150.248:1935/live/car-cloudhub
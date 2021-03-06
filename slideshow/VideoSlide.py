#!/usr/bin/env python3

from .Slide import Slide
import subprocess

class VideoSlide(Slide):

    def __init__(self, ffmpeg_version, file, ffprobe, output_width, output_height, fade_duration = 1, title = None, fps = 60, overlay_text = None, transition = "random", force_no_audio = False, video_start = None, video_end = None):
        
        duration = subprocess.check_output("%s -show_entries format=duration -v error -of default=noprint_wrappers=1:nokey=1 \"%s\"" %(ffprobe, file)).decode()
        width = subprocess.check_output("%s -select_streams v -show_entries stream=width -v error -of default=noprint_wrappers=1:nokey=1 \"%s\"" %(ffprobe, file)).decode()
        height = subprocess.check_output("%s -select_streams v -show_entries stream=height -v error -of default=noprint_wrappers=1:nokey=1 \"%s\"" %(ffprobe, file)).decode()
        
        duration = float(duration)
        
        self.is_trimmed = False
        self.start = None
        self.end = None
        
        if video_start is not None:
            self.start = video_start
        if video_end is not None:
            self.end = video_end
            
        if self.start is not None or self.end is not None:
            self.is_trimmed = True
            
            # calculate new duration
            start = self.start if self.start is not None else 0
            end = self.end if self.end is not None else duration
            duration = end - start
        
        super().__init__(ffmpeg_version, file, output_width, output_height, duration, fade_duration, fps, title, overlay_text, transition)
        
        audio = subprocess.check_output("%s -select_streams a -show_entries stream=codec_type -v error -of default=noprint_wrappers=1:nokey=1 \"%s\"" %(ffprobe, file)).decode()
        has_audio = "audio" in str(audio)
        
        self.has_audio = False if force_no_audio else has_audio
        self.width = int(width)
        self.height = int(height)
        self.ratio = self.width/self.height
        
    def getFilter(self):
        width, height = [self.output_width, -1]
        if self.ratio < self.output_ratio:
           width, height = [-1, self.output_height]

        filters = []
        filters.append("scale=w=%s:h=%s" %(width, height))
        filters.append("fps=%s" %(self.fps))
        filters.append("pad=%s:%s:(ow-iw)/2:(oh-ih)/2" %(self.output_width, self.output_height))
        
        if self.is_trimmed:
            trim = []
            if self.start is not None:
                trim.append("start=%s" %(self.start))
            if self.end is not None:
                trim.append("end=%s" %(self.end))
                
            filters.append("trim=%s,setpts=PTS-STARTPTS" %(":".join(trim)))
        
        return [",".join(filters)]
        
    def getAudioFilter(self):
        if self.is_trimmed:
            trim = []
            if self.start is not None:
                trim.append("start=%s" %(self.start))
            if self.end is not None:
                trim.append("end=%s" %(self.end))
                
            return "atrim=%s,asetpts=PTS-STARTPTS" %(":".join(trim))
            
        return None
        
    def getObject(self, config):
        object = super().getObject(config)
        
        if self.start is not None:
            object["start"] = self.start
        
        if self.end is not None:
            object["end"] = self.end

        return object
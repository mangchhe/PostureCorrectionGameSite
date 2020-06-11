from django import forms
from .models import VideosDB
from Edus.camera import VideoCamera
import json

# VideosDB 데이터베이스 테이블을 기반으로 한 양식
class VideoForm(forms.ModelForm):
    class Meta:
        model= VideosDB
        fields= ["title", "editor", "videofile", "video_img", "level", "skeleton"]
    
from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import StreamingHttpResponse
from Edus.camera import VideoCamera
from .models import EdusDB
from Users.models import UsersDB
from Videos.models import VideosDB
from django.core.paginator import Paginator
import datetime

# Create your views here.

# 모드 선택 후 화면

def play(request, page_no):

	# 비디오 정보 (mp4, avi 등)

	edu = EdusDB.objects.filter(video_id = 1, user_id = 1).order_by('-edu_days') # 해당 영상과, 사용자 주

	eduList = Paginator(edu, 4)

	idx = []
	days = []
	video = []

	totalPageList = [i for i in range(1, eduList.num_pages + 1)]
	currentPage = page_no

	for i, j in enumerate(eduList.get_page(page_no).object_list.values()):

		idx.append((page_no-1) * 4 + i+1)
		video.append(j['recode_video'])
		days.append(j['edu_days'])

	context = {
		'videoList' : zip(idx, video, days),
		'totalPageList' : totalPageList,
		'currentPage' : currentPage,
	}

	if request.method == 'POST':
		new_video = EdusDB.objects.create(
			# edu_days = 현재 시간 자동 저장
			video_id=VideosDB.objects.all()[0],
			user_id=UsersDB.objects.all()[0],
			recode_video='test',
			score=99
		)

	return render(request, 'playView.html', context)

def play_after(request, page_no):

	# 비디오 정보 (mp4, avi 등)

	# after

	rankList = ['A+', 'A0', 'B+', 'B0', 'C+', 'C0', 'D+', 'D0', 'F']
	zum = 90
	rank = 'F'
	nowDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	for idx, val in enumerate(rankList):

		if zum >= 95 - idx * 5:

			rank = rankList[idx]
			break

	# before

	edu = EdusDB.objects.filter(video_id = 1, user_id = 1).order_by('-edu_days') # 해당 영상과, 사용자 주

	eduList = Paginator(edu, 4)

	idx = []
	days = []
	video = []

	totalPageList = [i for i in range(1, eduList.num_pages + 1)]
	currentPage = page_no

	for i, j in enumerate(eduList.get_page(page_no).object_list.values()):

		idx.append((page_no-1) * 4 + i+1)
		video.append(j['recode_video'])
		days.append(j['edu_days'])

	context = {
		'videoList' : zip(idx, video, days),
		'totalPageList' : totalPageList,
		'currentPage' : currentPage,
		'result' : str(zum)+' , '+str(rank)+' , '+str(nowDate),
	}

	if request.method == 'POST':
		new_video = EdusDB.objects.create(
			# edu_days = 현재 시간 자동 저장
			video_id=VideosDB.objects.all()[0],
			user_id=UsersDB.objects.all()[0],
			recode_video='test',
			score=99
		)

	return render(request, 'playViewResult.html', context)

def gen(camera): # https://item4.blog/2016-05-08/Generator-and-Yield-Keyword-in-Python/
# 앨범 이미지
	while True:

		frame = camera.get_frame()

		yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def video_feed(request):
# 웹캠 정보
	return StreamingHttpResponse(gen(VideoCamera()),
					content_type='multipart/x-mixed-replace; boundary=frame') # 찾아보기

# 마이페이지

def mypage(request):

	return render(request, 'mypageView.html')
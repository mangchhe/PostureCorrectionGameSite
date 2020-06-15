from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import StreamingHttpResponse
from django.http import HttpResponse, JsonResponse
from Edus.camera import VideoCamera
from Edus.camera2 import VideoCamera2
from .models import EdusDB
from Users.models import UsersDB
from Videos.models import VideosDB
from django.core.paginator import Paginator
import datetime
import webbrowser
from PostureCorrectionGameSite import settings
from mutagen.mp4 import MP4
from django.db.models import Sum
from Videos.forms import VideoForm
# Create your views here.
from django.urls import reverse_lazy
import json
from pathlib import Path
import pickle
import cv2
import numpy as np

# 모드 선택 후 화면

def play(request, page_no, video_id):

	# 비디오 정보 (mp4, avi 등)

	VIDEO_NAME = VideosDB.objects.get(id=video_id)
	videoName = str(VIDEO_NAME.videofile)

	videoLength = MP4(settings.MEDIA_ROOT + videoName).info.length + .5

	edu = EdusDB.objects.filter(video_id = video_id, user_id = request.user.id).order_by('-edu_days') # 해당 영상과, 사용자 주
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
		'videoLength' : videoLength,
		'videoName' : videoName,
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

def play_after(request, page_no, video_no):

	# 비디오 정보 (mp4, avi 등)

	# after
	# 조회수 증가
	views = VideosDB.objects.get(id=video_no)
	views.views += 1
	views.save()

	rankList = ['A+', 'A0', 'B+', 'B0', 'C+', 'C0', 'D+', 'D0', 'F']
	zum = 90
	rank = 'F'
	nowDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	for idx, val in enumerate(rankList):

		if zum >= 95 - idx * 5:

			rank = rankList[idx]
			break

	# before

	edu = EdusDB.objects.filter(video_id = video_no, user_id = request.user.id).order_by('-edu_days') # 해당 영상과, 사용자 주

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

	""" 초당 평균 데이터 구하는 부분 """
	p_list =[]
	save = [[0 for col in range(2)] for row in range(19)]
	count = 0

	while True:		
		frame, points = camera.get_frame()

		for i in range(0,19):
			save[i][0] += points[i][0]
			save[i][1] += points[i][1]

		# fps 평균 구하기
		if(count % 3 == 2):
			for i in range(0,19):
				save[i][0] /= 3
				save[i][1] /= 3

			p_list.append(save) # 초당 평균 데이터 -> 이 데이터와 학습 영상 데이터랑 비교하면 됨
			
			save = [[0 for col in range(2)] for row in range(19)]
		
		#print(p_list)
		count += 1
		print(count, p_list, len(p_list))
		yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def video_feed(request):
# 웹캠 정보
	return StreamingHttpResponse(gen(VideoCamera()),
					content_type='multipart/x-mixed-replace; boundary=frame') # 찾아보기


# 마이페이지
def mypage(request):
	
	return render(request, 'mypageView.html')

def hangulFilePathImageRead(filePath) :
	stream = open(filePath.encode('utf-8') , "rb")
	bytes = bytearray(stream.read())
	numpyArray = np.asarray(bytes, dtype=np.uint8)
		
	return cv2.imdecode(numpyArray , cv2.IMREAD_UNCHANGED)

def post_list(request):
	""" 비디오 업로드 """
	
	lastvideo= VideosDB.objects.last() # 데이터베이스 테이블에서 마지막 비디오(객체)인 변수 lastvideo를 생성
	
	videofile= lastvideo.videofile.url # 비디오 파일 경로를 포함하는 변수 videofile을 생성

	form= VideoForm(request.POST or None, request.FILES or None) #ne, request.FILES request.POST 또는 None은 사용자가 양식을 제출 한 후 데이터를 필드에 유지

	if request.method == 'POST':
		
		#print(form.errors)
		if form.is_valid():
			print("test")
			video_form = form.save(commit=False)
			dir = str(request.FILES['videofile'])
			#dir = hangulFilePathImageRead(dir)
			#path = Path(dir)
			#dir = str(dir, 'utf-8')
			video_form.editor = request.user
			video_form.save()
			print(form.instance.id)
			item = VideosDB.objects.get(pk=form.instance.id)
			skeleton = VideoCamera2(dir)
			p_list =[]
			save_data = [[0 for col in range(2)] for row in range(19)]
			count = 0
			n_count = [0 for row in range(19)]

			while True:
				frame, points = skeleton.get_frame()

				print(points)
				if frame == 2:
					break
				elif frame == 1:
					continue
				else:
					for i in range(0,19):
						if(points[i] == None):
							save_data[i] = None
							n_count[i] += 1
						else:
							save_data[i][0] += points[i][0]
							save_data[i][1] += points[i][1]

					# fps 평균 구하기
					if(count % 3 == 2):
						for i in range(0,19):
							if(save_data[i] != None):
								save_data[i][0] /= 3 - n_count[i]
								save_data[i][1] /= 3 - n_count[i]

						p_list.append(save_data) # 초당 평균 데이터
						save_data = [[0 for col in range(2)] for row in range(19)]
						n_count = [0 for row in range(19)]
					
					count += 1
			
			# JSON 인코딩
			print(p_list)
			print(len(p_list))
			jsonString = json.dumps(p_list)

			item.skeleton = jsonString
			item.save()
		else:
			print("else_test")

	""" 업로드 된 영상 및 나의 점수 """

	Edus_list = EdusDB.objects.all().filter(user_id=request.user.id) # Edus 테이블의 전체 데이터 가져오기 -> 로그인이랑 회원가입 만들어지면 queryset 다시 작성 예정
	#s_sum = EdusDB.objects.aggregate(Sum('score'))['score__sum'] # Edus 테이블의 전체 score 값 더하기 -> 로그인이랑 회원가입 만들어지면 queryset 다시 작성 예정
	s_sum = Edus_list.aggregate(Sum('score'))['score__sum'] # Edus 테이블의 전체 score 값 더하기 -> 로그인이랑 회원가입 만들어지면 queryset 다시 작성 예정
	# mypageView로 넘길 데이터
	context= {'videofile': videofile,
              'form': form,
			  'score_sum': s_sum,
              'Edus_list' : Edus_list}
	return render(request, 'mypageView.html', context)

def VideoSelect(request): # 영상 선택 후 화면 view
    EdusDB_list = EdusDB.objects.all().order_by('-score') # 점수가 높은순으로
    UsersDB_list = UsersDB.objects.all()
    VideosDB_list = VideosDB.objects.all().order_by('-start_date') #게시일 최근순으로

    context = {'EdusDB_list': EdusDB_list,
               'UsersDB_list': UsersDB_list,
               'VideosDB_list': VideosDB_list}
    return render(request, 'modepage.html', context)


def ResultVideosList(request): # 학습한 결과 영상 리스트 화면 view
    ResultVideos = EdusDB.objects.all()
    EdusDB_list = EdusDB.objects.all().filter(user_id=request.user.id).order_by('-edu_days') #학습일 최근순으로
    paginator = Paginator(EdusDB_list, 5) #Paginator를 이용해서 한 페이지에 보여줄 객체 갯수
    page = request.GET.get('page') #현재 페이지를 받아옴
    Edus = paginator.get_page(page)

    context = {'EdusDB_list': EdusDB_list,
               'Edus': Edus}

    return render(request, 'ResultVideosList.html', context)

def video_select(request, video_id):
	return render(request, 'modepage.html',{'video_id':video_id})


def resultView(request, edu_id):
	result = EdusDB.objects.filter(id=edu_id)
	print(result)
	return render(request, 'resutlView.html',{'result':result})

def resultView(request, edu_id):
	result = EdusDB.objects.filter(id=edu_id)
	print(result)
	return render(request, 'resultView.html',{'result':result})

def calculatePosture(request):

	accuracy = 99
	rank = 'A'
	description = '설명'

	content = {
		'accuracy' : accuracy,
		'rank' : rank,
		'description' : description,
	}

	return JsonResponse(content)


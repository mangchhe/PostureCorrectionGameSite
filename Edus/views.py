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
from .forms import EdusDBForm
# Create your views here.
from django.urls import reverse_lazy
import json
from pathlib import Path
import pickle
import cv2
import numpy as np
import datetime

accuracy = 0
rank = ''
rankList = []
total_accuracy_list = []
total_rank_list = []
total_zum_list = []
total_accuracy = 0
total_rank = ''
total_zum = 0

BODY_PARTS = {"Nose": 0, "Neck": 1, "RShoulder": 2, "RElbow": 3, "RWrist": 4,
              "LShoulder": 5, "LElbow": 6, "LWrist": 7, "RHip": 8, "RKnee": 9,
              "RAnkle": 10, "LHip": 11, "LKnee": 12, "LAnkle": 13, "REye": 14,
              "LEye": 15, "REar": 16, "LEar": 17, "Background": 18}

POSE_PAIRS = [["Neck", "RShoulder"], ["Neck", "LShoulder"], ["RShoulder", "RElbow"], ["RElbow", "RWrist"],
              ["LShoulder", "LElbow"], ["LElbow", "LWrist"], [
                  "Neck", "RHip"], ["RHip", "RKnee"],
              ["RKnee", "RAnkle"], ["Neck", "LHip"], [
                  "LHip", "LKnee"], ["LKnee", "LAnkle"],
              ["Neck", "Nose"], ["Nose", "REye"], ["REye", "REar"], ["Nose", "LEye"], ["LEye", "LEar"]]

nowDatetime = ""
r_score = 0


def dist(v):
    return np.sqrt(v[0]**2 + v[1]**2)


def innerProduct(v1, v2):
    # 벡터 v1, v2의 크기 구하기

    distA = dist(v1)
    distB = dist(v2)

    # 내적 1 (x1x2 + y1y2)
    if v1[0] + v1[1] == 0 or v2[0] + v2[1] == 0:
        return None

    ip = v1[0] * v2[0] + v1[1] * v2[1]

    # 내적 2 (|v1|*|v2|*cos x)
    ip2 = distA * distB

    # cos x값 구하기s
    cost = ip / ip2

    # x값(라디안) 구하기 (cos 역함수)
    x = np.arccos(cost)

    # x값을 x도로 변환하기
    degX = np.rad2deg(x)

    return degX


def score_skeleton(train, result):

    global rankList

    for pair in POSE_PAIRS:
        partA = pair[0]  #  Head
        partA = BODY_PARTS[partA]  # 1
        partB = pair[1]  # Neck
        partB = BODY_PARTS[partB]  # 1

        if train[partA] and result[partB]:
            t_vector = (train[partA][0]-train[partB][0],
                        train[partA][1]-train[partB][1])
            r_vector = (result[partA][0]-result[partB][0],
                        result[partA][1]-result[partB][1])

            # t_vector백터, r_vector -> train, result 각각 백터 값 구해서 넣기
            degree = innerProduct(t_vector, r_vector)

            for i in range(1, 10):

                if degree:

                    if degree < 20 * i:

                        rankList.append(4.5 - .5 * (i - 1))
                        break

                else:

                    break
# 모드 선택 후 화면


def play(request, page_no, video_id):

    # 비디오 정보 (mp4, avi 등)

    VIDEO_NAME = VideosDB.objects.get(id=video_id)
    videoName = str(VIDEO_NAME.videofile)

    videoLength = MP4(settings.MEDIA_ROOT + videoName).info.length + .5

    edu = EdusDB.objects.filter(video_id=video_id, user_id=request.user.id).order_by(
        '-edu_days')  # 해당 영상과, 사용자 주
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
        'videoList': zip(idx, video, days),
        'totalPageList': totalPageList,
        'currentPage': currentPage,
        'videoLength': videoLength,
        'videoName': videoName,
        'videoNo': video_id,
    }

    return render(request, 'playView.html', context)


def play_after(request, page_no, video_no):
    global r_score, nowDatetime
    # 비디오 정보 (mp4, avi 등)

    # after
    # 조회수 증가
    views = VideosDB.objects.get(id=video_no)
    views.views += 1
    views.save()

    nowDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # before

    edu = EdusDB.objects.filter(video_id=video_no, user_id=request.user.id).order_by(
        '-edu_days')  # 해당 영상과, 사용자 주

    eduList = Paginator(edu, 4)

    total_accuracy = round(sum(total_accuracy_list) //
                           len(total_accuracy_list), 2)
    total_zum = round(sum(total_zum_list) // len(total_zum_list), 2)

    zumList = ['A+', 'A0', 'B+', 'B0', 'C+', 'C0', 'D+', 'D0', 'F']

    for i in range(1, 10):

        if total_zum > 4.5 - .5 * i:

            total_rank = zumList[i - 1]
            break

    idx = []
    days = []
    video = []

    totalPageList = [i for i in range(1, eduList.num_pages + 1)]
    currentPage = page_no

    for i, j in enumerate(eduList.get_page(page_no).object_list.values()):

        idx.append((page_no-1) * 4 + i+1)
        video.append(j['recode_video'])
        days.append(j['edu_days'])
        
    
    video_get = VideosDB.objects.get(id=video_no)

    if request.method == 'POST':
        form = EdusDBForm(request.POST)
        if form.is_valid():
            edus_form = form.save(commit=False)
            edus_form.video_id=video_get
            edus_form.user_id=request.user
            edus_form.recode_video = settings.EDUS_ROOT+nowDatetime+'.mp4'
            edus_form.score = r_score
            edus_form.save()
    elif request.method == 'GET':
        form = EdusDBForm()
    else:
        pass

    total_zum = str(total_zum)
    total_rank= str(total_rank)
    total_accuracy = str(total_accuracy)
    context = {
        'videoList': zip(idx, video, days),
        'totalPageList': totalPageList,
        'currentPage': currentPage,
        'total_zum': total_zum, 
        'total_rank' : total_rank, 
        'total_accuracy' : total_accuracy,
        'videoNo': video_no,
        'form': form,
    }

    return render(request, 'playViewResult.html', context)


def gen(camera, video_id):  # https://item4.blog/2016-05-08/Generator-and-Yield-Keyword-in-Python/
    # 앨범 이미지
    global nowDatetime

    """ 초당 평균 데이터 구하는 부분 """
    p_list = []
    save = [[0 for col in range(2)] for row in range(19)]
    count = 0
    n_count = [0 for row in range(19)]
    s_count = 0

    global accuracy
    global rank
    global rankList

    qVideo = VideosDB.objects.get(id=video_id)

    skel_list = json.loads(qVideo.skeleton)

    s_len = len(skel_list)

    nowDatetime = camera.nowDatetime

    while True:

        if s_count == s_len:
            del camera
            break

        frame, points = camera.get_frame()

        for i in range(0, 19):
            if(points[i] == None):
                n_count[i] += 1
            else:
                save[i][0] += points[i][0]
                save[i][1] += points[i][1]

        # fps 평균 구하기
        if(count % 3 == 2):
            for i in range(0, 19):
                if(save[i][0] != 0):
                    save[i][0] /= 3 - n_count[i]
                if(save[i][1] != 0):
                    save[i][1] /= 3 - n_count[i]

            score_skeleton(skel_list[s_count], save)

            zum = round(sum(rankList) / len(rankList), 2)

            accuracy = round(zum / 4.5 * 100, 2)

            total_zum_list.append(zum)
            total_accuracy_list.append(accuracy)

            zumList = ['A+', 'A0', 'B+', 'B0', 'C+', 'C0', 'D+', 'D0', 'F']

            for i in range(1, 10):

                if zum > 4.5 - .5 * i:

                    rank = zumList[i - 1]
                    break

            del rankList[:]

            print('점수 :', zum, '랭크 : ', rank, '정확도 : ', accuracy)
            # p_list.append(save) # 초당 평균 데이터 -> 이 데이터와 학습 영상 데이터랑 비교하면 됨

            save = [[0 for col in range(2)] for row in range(19)]
            n_count = [0 for row in range(19)]
            s_count += 1

        count += 1
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def video_feed(request, video_id):
    # 웹캠 정보
    now = datetime.datetime.now()
    nowDatetime = now.strftime('%Y%m%d%H%M%S')
    return StreamingHttpResponse(gen(VideoCamera(nowDatetime), video_id),
                                 content_type='multipart/x-mixed-replace; boundary=frame')  # 찾아보기


# 마이페이지
def mypage(request):

    return render(request, 'mypageView.html')


def post_list(request):
    """ 비디오 업로드 """

    lastvideo = VideosDB.objects.last()  # 데이터베이스 테이블에서 마지막 비디오(객체)인 변수 lastvideo를 생성

    videofile = lastvideo.videofile.url  # 비디오 파일 경로를 포함하는 변수 videofile을 생성

    # ne, request.FILES request.POST 또는 None은 사용자가 양식을 제출 한 후 데이터를 필드에 유지
    form = VideoForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':

        # print(form.errors)
        if form.is_valid():
            video_form = form.save(commit=False)
            dir = str(request.FILES['videofile'])
            video_form.editor = request.user
            video_form.save()

            # print(form.instance.id)
            item = VideosDB.objects.get(pk=form.instance.id)
            skeleton = VideoCamera2(dir)

            p_list = []
            save_data = [[0 for col in range(2)] for row in range(19)]
            count = 0
            n_count = [0 for row in range(19)]

            while True:
                frame, points = skeleton.get_frame()

                if frame == 2:
                    break
                elif frame == 1:
                    continue
                else:
                    for i in range(0, 19):
                        if(points[i] == None):
                            n_count[i] += 1
                        else:
                            save_data[i][0] += points[i][0]
                            save_data[i][1] += points[i][1]

                    # fps 평균 구하기
                    if(count % 3 == 2):
                        for i in range(0, 19):
                            if(save_data[i][0] != 0):
                                save_data[i][0] /= 3 - n_count[i]
                            if(save_data[i][1] != 0):
                                save_data[i][1] /= 3 - n_count[i]

                        p_list.append(save_data)  # 초당 평균 데이터
                        save_data = [
                            [0 for col in range(2)] for row in range(19)]
                        n_count = [0 for row in range(19)]

                    count += 1

            # JSON 인코딩
            jsonString = json.dumps(p_list)

            item.skeleton = jsonString
            item.save()
        else:
            print("else_test")

    """ 업로드 된 영상 및 나의 점수 """

    # Edus 테이블의 전체 데이터 가져오기 -> 로그인이랑 회원가입 만들어지면 queryset 다시 작성 예정
    Edus_list = EdusDB.objects.all().filter(user_id=request.user.id)
    # s_sum = EdusDB.objects.aggregate(Sum('score'))['score__sum'] # Edus 테이블의 전체 score 값 더하기 -> 로그인이랑 회원가입 만들어지면 queryset 다시 작성 예정
    # Edus 테이블의 전체 score 값 더하기 -> 로그인이랑 회원가입 만들어지면 queryset 다시 작성 예정
    s_sum = Edus_list.aggregate(Sum('score'))['score__sum']
    # mypageView로 넘길 데이터
    context = {'videofile': videofile,
               'form': form,
               'score_sum': s_sum,
               'Edus_list': Edus_list}
    return render(request, 'mypageView.html', context)


def ResultVideosList(request):  # 학습한 결과 영상 리스트 화면 view
    ResultVideos = EdusDB.objects.all()
    EdusDB_list = EdusDB.objects.all().filter(
        user_id=request.user.id).order_by('-edu_days')  # 학습일 최근순으로
    paginator = Paginator(EdusDB_list, 5)  # Paginator를 이용해서 한 페이지에 보여줄 객체 갯수
    page = request.GET.get('  page')  # 현재 페이지를 받아옴
    Edus = paginator.get_page(page)

    context = {'EdusDB_list': EdusDB_list,
               'Edus': Edus}

    return render(request, 'ResultVideosList.html', context)


def video_select(request, video_id):  # 영상 선택 후 화면 view
    EdusDB_list = EdusDB.objects.all().order_by('-score')  # 점수가 높은순으로 쿼리문 수정
    UsersDB_list = UsersDB.objects.all()
    VideosDB_list = VideosDB.objects.all().exclude(
        editor__id=request.user.id)  # 게시일 최근순으로

    context = {'EdusDB_list': EdusDB_list,
               'UsersDB_list': UsersDB_list,
               'VideosDB_list': VideosDB_list,
               'video_id': video_id}
    return render(request, 'modepage.html', context)


def resultView(request, edu_id):
    result = EdusDB.objects.filter(id=edu_id)

    return render(request, 'resultView.html', {'result': result})



def calculatePosture(request):

    global accuracy
    global rank

    content = {
        'accuracy': accuracy,
        'rank': rank,
    }

    return JsonResponse(content)


def playResultView(request, edu_id):
    result = EdusDB.objects.filter(id=edu_id)
    return render(request, 'playviewshowmodal.html', {'result': result})


def UploadPreView(request):
    result = settings.EDUS_ROOT+nowDatetime+'.mp4'
    return render(request, 'uploadpreview.html', {'result': result})
from django.shortcuts import render
from .models import VideosDB
from .forms import VideoForm
from Users.models import UsersDB
from Edus.models import EdusDB

import math

# Create your views here.

def search(request):
    
    where = request.GET.get('where',None)

    if where == 'pop':
        qs = VideosDB.objects.all().order_by('-views')
    elif where == 'last':
        qs = VideosDB.objects.all().order_by('start_date')
    else:
        qs = VideosDB.objects.all()

    page = int(request.GET.get('page',1))
    paginated_by = 1


    q = request.GET.get('q', '') # GET request의 인자중에 q 값이 있으면 가져오고, 없으면 빈 문자열 넣기
    le = request.GET.getlist('le','')
    llist = ['상', '중', '하']
    nole = []
    if le:
        for x in llist:
            if str(x) not in le:
                nole.append(x)

        for x in nole:
            qs = qs.exclude(level=x)
    
    if q: # q가 있으면
        qs = qs.filter(title__icontains=q) # 제목에 q가 포함되어 있는 레코드만 필터링
    
    total_count = len(qs)
    total_page = math.ceil(total_count/paginated_by)
    page_range = range(1, total_page+1)
    start_index = paginated_by * (page-1)
    end_index = paginated_by * page

    qs = qs[start_index:end_index]

    return render(request, 'search.html', {'search' : qs, 'q' : q, 'where':where, 'page_range':page_range, 'le':le})

def main(request):

    pop = VideosDB.objects.all().order_by('-views')
    late = VideosDB.objects.all().order_by('start_date')
    #user = UsersDB.objects.prefetch_related('id')
    user = EdusDB.objects.order_by('score')
    pop = pop[0:4]
    late = late[0:4]

    return render(request, 'main.html', {'pop' : pop, 'late' : late,'user':user,})


  

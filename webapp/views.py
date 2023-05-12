import datetime
import json
import random
import time
from functools import wraps

from django.contrib.auth.hashers import check_password
from django.db.models import F, Q
# from django.http import JsonResponse
from django.http import JsonResponse
from django.shortcuts import render
from .models import *
# Create your views here.
from django.views.decorators.http import require_POST

from webapp import models


def loginfailed(request):
    return JsonResponse({"status": 403, "message": "Unauthorizd Access"})

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('username'):
            # 如果用户未登录，则重定向到登录页面
            return JsonResponse(status=403, data={'msg': 'Non-login Status'})
        else:
            # 如果用户已登录，则继续执行原始视图函数
            return view_func(request, *args, **kwargs)

    return wrapper






@require_POST
def signup(request):
    data = json.loads(request.body)
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    password = data.get('password')
    account_number = random.randint(100000, 99999999999)
    if not all([first_name, last_name, password, account_number]):
        return JsonResponse(status=500, data={'msg': 'Incomplete Information'})
    try:
        user = Users.objects.create_user(username=account_number,
                                         first_name=first_name,
                                         last_name=last_name,
                                         password=password)
    except Exception:
        return JsonResponse(data={"msg": "error"}, status=500)

    return JsonResponse(data={'account_number': account_number},
                        status=201)







@require_POST
def signin(request):
    data = json.loads(request.body)
    account_number = data.get('account_number')
    password = data.get('pwd')

    if not all([account_number, password]):
        return JsonResponse(status=500, data={'msg': 'Incomplete Information'})

    try:
        u = Users.objects.get(username=account_number)
        # 匹配账户
    except Exception:
        return JsonResponse(status=500, data={'msg': 'User Not Exist'})

    if check_password(password, u.password):
        # 匹配密码
        request.session['username'] = u.username
        return JsonResponse(status=200, data={})

    return JsonResponse(status=500, data={'msg': 'Wrong Password'})







@require_POST
@login_required
def deposit(request):
    data = json.loads(request.body)
    user_now = request.session['username']

    try:
        deposit_amount = float(data.get('deposit_amount'))
        # 规范存款金额格式
    except:
        return JsonResponse(status=500, data={'msg': 'Error'})

    if not all([deposit_amount]):
        return JsonResponse(status=500, data={'msg': 'Incomplete Information'})


    try:
        u = Users.objects.get(username=user_now)
        # db中查找用户，和当前已登录的账户匹配
    except Exception:
        return JsonResponse(status=500, data={'msg': 'Error'})

    date = datetime.datetime.now()
    Statements.objects.create(payer_account_id=u,
                              receiver_account_id=u,
                              amount=deposit_amount,
                              type=0,
                              date_time=date)
    # 更新statement
    Users.objects.filter(username=user_now).update(account_balance=F('account_balance') + deposit_amount)
    # 增加金额
    return JsonResponse(data={'target_account_number': u.username,
                              'amount': deposit_amount,
                              'date': date}, status=201)







@require_POST
def createinvoice(request):
    data = json.loads(request.body)
    booking_number = data['booking_number']
    payment_provider = data['payment_provider_name']
    receiver_now = data['receiver_account_number']
    amount = data['amount']

    if not all([booking_number, payment_provider, receiver_now, amount]):
        return JsonResponse(status=500, data={'msg': 'Incomplete Information'})

    print(receiver_now)
    receiver_now_id = Users.objects.get(username=receiver_now)
    receiver_now_id = receiver_now_id.id

    if payment_provider != "Apple Pay":
        return JsonResponse(status=500, data={'msg': 'Payment Provider does not Match'})

    try:
        u = Users.objects.get(username=receiver_now)
        # 匹配账户
    except Exception:
        return JsonResponse(status=500, data={'msg': 'Receiver Not Exist'})

    invoice_number = random.randint(1, 99999)
    invoice_number = str(invoice_number)
    stamp = random.randint(999999999, 9999999999)
    stamp = str(stamp)


    try:
        Invoices.objects.create(
            invoice_number=invoice_number,
            booking_number=booking_number,
            payment_provider_id=4,
            # payer_id_id='20273557286',
            receiver_id_id=receiver_now_id,
            amount=amount,
            create_time=datetime.datetime.now(),
            status=0,
            stamp=stamp)
    except:
        return JsonResponse(status=500, data={'msg': 'Fail to Create'})

    return JsonResponse(data={'stamp': stamp, 'invoice_number': invoice_number, 'create_time': datetime.datetime.now()}, status=201)






@require_POST
def payinvoice(request):
    data = json.loads(request.body)
    invoice_number = data.get('invoice_num')
    account_number = data.get('account_num')
    password = data.get('pwd')

    if not all([invoice_number, account_number, password]):
        return JsonResponse(status=500, data={'msg': 'Incomplete Information'})

    try:
        current_user = Users.objects.get(username=account_number)
    except:
        return JsonResponse(status=500, data={'msg': 'User Not Exist'})
    # 检查用户是否存在

    if check_password(password, current_user.password) == 0:
        return JsonResponse(status=500, data={'msg': 'Wrong Password'})

    try:
        i = Invoices.objects.get(invoice_number=invoice_number)
        # 获取要操作的invoice
    except Exception:
        return JsonResponse(status=500, data={'msg': 'No Such Invoice'})

    if i.status != 0:
        return JsonResponse(status=500, data={'msg': 'The Invoice was Paid Already'})

    u = current_user

    if u.account_balance < i.amount:
        return JsonResponse(status=500, data={'msg': 'No Sufficient Funds'})
    # 余额不足

    i.status = 1
    i.pay_time = datetime.datetime.now()
    i.payer_id = u
    i.save()
    # 支付成功并更新invoice

    Statements.objects.create(payer_account_id=u,
                              receiver_account_id=i.receiver_id,
                              amount=i.amount,
                              type=1,
                              date_time=datetime.datetime.now())

    u.account_balance = u.account_balance - i.amount
    u.save()
    # 扣款

    receiver_account_id = i.receiver_id
    receiver_account_id.account_balance = receiver_account_id.account_balance + i.amount
    receiver_account_id.save()
    # 增款

    return JsonResponse(data={'stamp': i.stamp}, status=200)








@require_POST
@login_required
def transfer(request):
    data = json.loads(request.body)
    account_number = request.session['username']
    target_account_number = data.get('target_account_number')
    amount = data.get('amount')

    if not all([amount, target_account_number, account_number]):
        return JsonResponse(status=500, data={'msg': 'Incomplete Information'})

    try:
        payer_account_id = Users.objects.get(username=account_number)
        receiver_account_id = Users.objects.get(username=target_account_number)
    except Exception:
        return JsonResponse(status=500, data={'msg': 'Invalid User'})
    # 没有找到

    if payer_account_id.account_balance < amount:
        return JsonResponse(status=500, data={'msg': 'Not Sufficient Funds'})
    # 余额不足


    Statements.objects.create(payer_account_id=payer_account_id,
                              receiver_account_id=receiver_account_id,
                              amount=amount,
                              type=1,
                              date_time=datetime.datetime.now())

    payer_account_id.account_balance = payer_account_id.account_balance - amount
    payer_account_id.save()
    # 扣款

    receiver_account_id.account_balance = receiver_account_id.account_balance + amount
    receiver_account_id.save()
    # 增款

    return JsonResponse(data={}, status=200)







@require_POST
@login_required
def balance(request):
    account_number = request.session['username']

    try:
        u = Users.objects.get(username=account_number)
    except Exception:
        return JsonResponse(status=500, data={'msg': 'Invalid User'})

    return JsonResponse(data={'amount': u.account_balance}, status=200)









@require_POST
@login_required
def statement(request):
    data = json.loads(request.body)
    account_number = request.session['username']
    date_begin = data.get('date_begin')
    date_end = data.get('date_end')

    if not all([account_number, date_begin, date_end]):
        return JsonResponse(status=500, data={'msg': 'Incomplete Information'})

    date_begin = datetime.datetime.strptime(date_begin, '%Y-%m-%d %H:%M:%S')
    date_end = datetime.datetime.strptime(date_end, '%Y-%m-%d %H:%M:%S')
    query = Q(date_time__gte=date_begin) & Q(date_time__lte=date_end)

    u = Users.objects.get(username=account_number)
    statements = Statements.objects.filter(Q(payer_account_id__id=u.id) |
                                           Q(receiver_account_id__id=u.id)).filter(query)
    # 任何涉及该账户的交易
    records = []
    for i in statements:
        records.append({
            'Statement_id': i.id,
            'date': i.date_time,
            'amount': i.amount,
            'type': i.type,
            'payer_account_number': i.payer_account_id.username,
            'target_account_number': i.receiver_account_id.username
        })
    print(records)
    return JsonResponse(data={'records': records}, status=200)

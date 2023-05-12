from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class Users(AbstractUser):
    # account_number = models.CharField(unique=True, max_length=20)
    # 使用User类的username替代
    # account_name = models.CharField(max_length=10)
    # 使用User类自带的first_name和last_name替代
    # account_password = models.CharField(max_length=16)
    # 使用User类自带的password替代
    account_balance = models.FloatField(default=0.0)
    REQUIRED_FIELDS = ['firstname', 'lastname', 'password']

class Statements(models.Model):
    payer_account_id = models.ForeignKey('Users',related_name='statement_payer', on_delete=models.PROTECT)
    receiver_account_id = models.ForeignKey('Users', related_name='statement_receiver', on_delete=models.PROTECT)
    amount = models.FloatField(default=0.0)
    type = models.IntegerField()  # 0-deposit; 1-pay; 2-receive.
    date_time = models.DateTimeField()  # YYYY-MM-DD HH:MM:SS

class Invoices(models.Model):
    invoice_number = models.CharField(unique=True, max_length=20)
    booking_number = models.CharField(unique=True, max_length=20)  # 对应Airline中的booking_number
    payment_provider_id = models.IntegerField(default=4)  # 按照各自分配的no.写
    payer_id = models.ForeignKey('Users', related_name='invoice_payer', on_delete=models.PROTECT, null=True)
    receiver_id = models.ForeignKey('Users', related_name='invoice_receiver', on_delete=models.PROTECT)
    create_time = models.DateTimeField()
    pay_time = models.DateTimeField(null=True)
    status = models.IntegerField(default=0) # 0-unpaid; 1-paid.
    amount = models.FloatField() # 订单金额
    stamp = models.CharField(max_length=20)

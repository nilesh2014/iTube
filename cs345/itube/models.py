from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserLog(models.Model):
	"""docstring for UserLog"""

	user_id = models.ForeignKey(User, on_delete=models.CASCADE)
	video_id = models.CharField(max_length=15)
	#log_info = models.CharField(max_length=50)
	like = models.IntegerField(default=0)
	dislike = models.IntegerField(default=0)
	view_count = models.IntegerField(default=0)
	favourite = models.IntegerField(default=0)
	# def __init__(self, arg):
	# 	super(UserLog, self).__init__()
	# 	self.arg = arg
	# 	

class QueryLog(models.Model):

	query = models.CharField(max_length=100)
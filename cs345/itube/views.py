from django.shortcuts import render,render_to_response, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from pymongo import MongoClient

from pymongo import MongoClient
from pymongo import IndexModel, TEXT
import pymongo
import MySQLdb


import pprint
import json, pprint
import os
import sys
from django.template import loader
import glob
from py2neo import Graph, authenticate
from operator import itemgetter
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from itube.models import UserLog, QueryLog

from django.contrib.auth.decorators import login_required

# Create your views here.

recent_query = ""
recent_opt_list = []
recent_exact_match = 0
recent_current_video = []
def index(request):
	global recent_query
	global recent_opt_list
	global recent_exact_match
	global recent_current_video
	data = []
	count = 0
	playingNow = []
	recomended = []
	count_info = {}
	print("In Index")
	if  request.method == "GET":
		recomended = get_recomended()
		print("Got GET request in Index")
		if "search_query" in request.GET:
			print("Search in:" )
			total_opt = 1
			opt_list = request.GET.getlist("search_option")
			print(opt_list)
			print("seach query request")
			query = request.GET['search_query'].strip()
			exact_match = request.GET.get('exact_match' , "0")
			print(exact_match + " " + query)
			for x in opt_list:
				total_opt = total_opt*int(x)
			print("total_opt is : " + str(total_opt))
			search_opt = str(total_opt)
			new_query = QueryLog(query=query)
			new_query.save()
			result = search_mongo(exact_match, query, search_opt)
			# client = MongoClient('mongodb://nilesh:nilesh123@127.0.0.1:27017/')
			# db = client.myNewDB
			# collection = db.newCollection
			# # print("Goring to search..." + exact_match +" " + query)
			# if exact_match == "0":
			# 	# print("CHoice is o")
			# 	result = db.newCollection.find({"$text": {"$search": query}})
			# 	# print (result.count())
			# elif exact_match == "1":
			# 	print("exact_match")
			# 	newquery = '\"' + query + '\"'
			# 	# print(newquery)
			# 	result = db.newCollection.find({"$text": {"$search": newquery}})
			# 	# print (result.count())
			
			for obj in result:
				jsonObj = {}
				jsonObj = obj
				jsonObj.pop("_id",None)
				data.append(jsonObj)
			recent_query = query
			recent_opt_list = opt_list
			recent_exact_match = exact_match
			#return HttpResponse(json.dumps({"result":data,"count":len(data)}),content_type="application/json")
		elif "id" in request.GET:
			print("related vedio query request " + request.GET["id"])
			#authenticate("localhost:7474", "neo4j", "nilesh123")
			graph =  Graph("http://neo4j:nilesh123@localhost:7474/db/data/")
			video_id = request.GET["id"]

			#query to get currentVedio
			query1 = """
			match (n) where n.id = """ + "\"" + video_id + "\"" + """
			return n
			"""
			tempData = graph.run(query1).data()
			#print(len(tempData))
			for obj in tempData:
				jsonObj = obj["n"]
				playingNow.append(jsonObj)
			recent_current_video  = playingNow
			#pprint.pprint(playingNow)
			#query = "match (n) return n.title as title" 



			query = """

			match (n:TubeVideo{id:""" + "\"" + video_id + "\"" + """})-[r]->(m)
			return  distinct m, collect(r) as relArray """
			
			data = refresh(query,graph)
			

			#print ( len(data))

			# Updata user_log
			if request.user.is_authenticated():
				user = request.user
				try:
					user_log = UserLog.objects.get(user_id=user,video_id=video_id)
				except UserLog.DoesNotExist:
					user_log = None
				if user_log is not None:
					user_log.view_count = user_log.view_count + 1
					user_log.save()
					print("Updated row in logs")
				else:
					user_log = UserLog(user_id=user,video_id=video_id,view_count=1)
					user_log.save()
					print("Added row in logs")
				
				count_info["like"] = user_log.like
				count_info["dislike"] = user_log.dislike
				count_info["favourite"] = user_log.favourite

			update_count(0,0,1,0,video_id)

		elif "cid" in request.GET:
			graph =  Graph("http://neo4j:nilesh123@localhost:7474/db/data/")
			videoId = request.GET["cid"]

			playingNow = recent_current_video

			queryChannel = """

			match (n:TubeVideo{id: """ + "\"" + videoId + "\"" + """})-[:sameChannel]->(m)
			with n,m
			match (n)-[r]->(m)
			return distinct m, collect(r) as relArray

			"""
			
			data = refresh(queryChannel,graph)
			#pprint.pprint(data
		
		# print("Requested query is: " + recent_query)
		# print("Exact Mantch: " + str(recent_exact_match))
		# print("Opt_list: ")
		# print(recent_opt_list)
		playingNow = recent_current_video
		if request.user.is_authenticated():
			print("User is authenticated")
			return render(request,'itube/topbarloggedin.html',{"recomended":recomended,"count_info":count_info, "currentVedio":playingNow, "result":data,"count":len(data)})
		return render(request,'itube/topbar.html',{"recomended":recomended,"count_info":count_info, "currentVedio":playingNow, "result":data,"count":len(data)})	
	# if request.is_ajax():
	# 	if 'like' in request.GET:
	# 		print("got Like request")
	# 	return HttpResponse(json.dumps({"result":"hi"}),content_type="application/json")
	
	# else:
	# 	return HttpResponse(
	# 		json.dumps({"error":"Not working"}),
	# 		content_type="application/json"
	# 		)

def login_view(request):
	recomended = get_recomended()
	if request.method == "GET":
		return index(request)
	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(request, username=username, password=password)
	if user is not None:
		login(request, user)
		# prepare a cursor object using cursor() method
		db = MySQLdb.connect("localhost","nilesh","nilesh123","itube" )
		cursor = db.cursor()

		# execute SQL query using execute() method.
		query = """

			select video_id
			from itube_userlog as user
			where user.user_id_id = """ + str(user.id) + """ and user.view_count >= all(select view_count
						from itube_userlog as u
						where u.user_id_id = """ + str(user.id) + """
					     )

			"""

		cursor.execute(query)

		# Fetch a single row using fetchone() method.
		vList = cursor.fetchall()
		vlist = []
		for l in vList:
			for s in l:
				print(s)
				if(s not in vlist):
					vlist.append(s)

		uList = []
		for vid in vlist:
			query = """
				select user_id_id
				from itube_userlog as user
				where user.video_id = """ + "\"" +  vid + "\"" 
		
			cursor.execute(query)
			users = cursor.fetchall()
			for user in users:
				for l in user:
					if(l != 1 and l not in uList):
						uList.append(l)
	
		print (uList)

		retVideo = []
		for user in uList:
			query = """
				select video_id
				from itube_userlog as u
				where u.user_id_id = """ + str(user) + """ and u.view_count >= all(select view_count
									from itube_userlog as u
									where u.user_id_id = """ + str(user) + """
					     				)
				"""
			cursor.execute(query)
			vlist = cursor.fetchall()
			for vid in vlist:
				for v in vid:
					if(v not in retVideo):
						retVideo.append(v)
	
		print (retVideo)
	
		#retVideo is the array of required id list

		# disconnect from server
		db.close()


		client = MongoClient('mongodb://nilesh:nilesh123@127.0.0.1:27017/')
		db = client.myNewDB
		collection = db.newCollection
		
		data = []
		for vid in retVideo:
			result = collection.find({"id":vid})
			for obj in result:
				obj.pop("_id",None)
				data.append(obj)
	

		playingNow= recent_current_video
		return render(request,'itube/topbarloggedin.html',{"label":"You may like!", "recomended":recomended, "currentVedio":playingNow, "result":data,"count":len(data)})
		#return render(request,'itube/topbarloggedin.html',{"currentVedio":[],"result":[],"count":0})
	return redirect('/itube/index/') #render(request, 'itube/topbar.html', {"currentVedio":[],"result":[],"count":0})	

def signup_view(request):
	username = request.POST['username']
	password = request.POST['password']
	firstname = request.POST['firstname']
	lastname = request.POST.get('lastname',"")

	user = User.objects.create_user(username,email=username,password = password)
	if user is not None:
		login(request,user)
		return redirect('/itube/index/')
	#return render(request,'itube/topbarloggedin.html',{"currentVedio":[],"result":[],"count":0})

def logout_view(request):
	logout(request)
	#return render(request,'itube/topbar.html',{"currentVedio":[],"result":[],"count":0})
	return redirect('/itube/index/')

def new_view(request):
	new_template = loader.get_template('itube/index.html')
	context = {"currentVedio":[],"result":[],"count":0}
	return HttpResponse(new_template.render(context, request))


def like_view(request):
	if request.user.is_authenticated():

		print("got Like request " + request.GET['id'])
		video_id = request.GET['id']
		print(request.GET['like'])
		like_value = int(request.GET['like'])
		dislike_value = int(request.GET['dislike'])
		
		user = request.user
		prev_like = 0
		prev_dislike = 0
		
		try:
			user_log = UserLog.objects.get(user_id=user,video_id=video_id)
		except UserLog.DoesNotExist:
			user_log = None
		if user_log is not None:
			prev_like = user_log.like
			prev_dislike = user_log.dislike
			user_log.like = like_value
			user_log.dislike = dislike_value

			user_log.save()
			print("Updated row in logs")
		else:
			user_log = UserLog(user_id=user,video_id=video_id,like=like_value, dislike=dislike_value)
			user_log.save()
			print("Added row in logs")
		if prev_like == 1 and like_value == 0:
			print("decrement Like")
			like_value = -1
		if prev_dislike == 1 and dislike_value == 0:
			dislike_value = -1
		update_count(like_value,dislike_value,0,0,video_id)

		#query to get currentVedio
		query1 = """
		match (n) where n.id = """ + "\"" + video_id + "\"" + """
		return n
		"""
		graph =  Graph("http://neo4j:nilesh123@localhost:7474/db/data/")

		tempData = graph.run(query1).data()
		tempVideo = []
		#print(len(tempData))
		for obj in tempData:
			jsonObj = obj["n"]
			tempVideo.append(jsonObj)
		counts = {}
		counts['like'] = tempVideo[0]["likeCount"]
		counts['dislike'] = tempVideo[0]["dislikeCount"]
		counts['view'] = tempVideo[0]["viewCount"]
		
		return HttpResponse(json.dumps({"result":counts}),content_type="application/json")
	else:
		return HttpResponse(json.dumps({"result":"required login"}),content_type="application/json")

def fav(request):
	prev_fav = 0
	if request.user.is_authenticated():
		video_id = request.GET['id']
		fav = int(request.GET['fav'])
		user = request.user
		try:
			user_log = UserLog.objects.get(user_id=user,video_id=video_id)
		except UserLog.DoesNotExist:
			user_log = None
		if user_log is not None:

			prev_fav = user_log.favourite
			user_log.favourite = fav

			user_log.save()
			print("Updated row in logs")
		else:
			user_log = UserLog(user_id=user,video_id=video_id,favourite=fav)
			user_log.save()
			print("Added row in logs")
		if prev_fav == 1 and fav == 0:
			print("decrement fav")
			fav = -1
		update_count(0,0,0,fav,video_id)
		return HttpResponse(json.dumps({"result":"Yuo have liked current video."}),content_type="application/json")
	else:
		return HttpResponse(json.dumps({"result":"required login"}),content_type="application/json")


def search_mongo(choice,string,something):
	client = MongoClient('mongodb://nilesh:nilesh123@127.0.0.1:27017/')
	db = client.myNewDB
	collection = db.newCollection

	# choice=sys.argv[1]
	# string=sys.argv[2]
	#something=sys.argv[3],name="search_index"
	# total_opt = 1
	# opt_list = ["2"]
	# for x in opt_list:
	# 	total_opt = total_opt*int(x)
	# print("total_opt is : " + str(total_opt))
	# something = str(total_opt)
	#something = "2"
	db.newCollection.drop_indexes()
	#something = "0"
	#collection.create_index([('field_i_want_to_index', pymongo.TEXT)],name="search_index", name='search_index', default_language='english')
	#my_collection.create_index([("mike", pymongo.DESCENDING),("eliot", pymongo.ASCENDING)],name="search_index")
	if something == "2" :
		db.newCollection.create_index([("title",pymongo.TEXT)],name="search_index")
	elif something == "5" :
		 db.newCollection.create_index([("description",pymongo.TEXT)],name="search_index")

	elif something == "7" :
		 db.newCollection.create_index([("tags",pymongo.TEXT)],name="search_index")

	elif something == "3":
		 db.newCollection.create_index([("channelTitle",pymongo.TEXT)],name="search_index")

	elif something == "10":
		 db.newCollection.create_index([("title",pymongo.TEXT),("description",pymongo.TEXT)],name="search_index")

	elif something == "14":
		 db.newCollection.create_index([("title",pymongo.TEXT),("tags",pymongo.TEXT)],name="search_index")

	elif something == "6":
		 db.newCollection.create_index([("title",pymongo.TEXT),("channelTitle",pymongo.TEXT)],name="search_index")

	elif something == "35":
		 db.newCollection.create_index([("description",pymongo.TEXT),("tags",pymongo.TEXT)],name="search_index")

	elif something == "15":
		 db.newCollection.create_index([("description",pymongo.TEXT),("channelTitle",pymongo.TEXT)],name="search_index")

	elif something == "21":
		 db.newCollection.create_index([("tags",pymongo.TEXT),("channelTitle",pymongo.TEXT)],name="search_index")

	elif something == "70":
		 db.newCollection.create_index([("title",pymongo.TEXT),("description",pymongo.TEXT),("tags",pymongo.TEXT)],name="search_index")

	elif something == "105":
		 db.newCollection.create_index([("description",pymongo.TEXT),("tags",pymongo.TEXT),("channelTitle",pymongo.TEXT)],name="search_index")

	elif something == "42":
		 db.newCollection.create_index([("title",pymongo.TEXT),("tags",pymongo.TEXT),("channelTitle",pymongo.TEXT)],name="search_index")

	elif something == "30":
		 db.newCollection.create_index([("title",pymongo.TEXT),("description",pymongo.TEXT),("channelTitle",pymongo.TEXT)],name="search_index")

	else :
		 index=db.newCollection.create_index([("title",pymongo.TEXT),("description",pymongo.TEXT),("tags",pymongo.TEXT),("channelTitle",pymongo.TEXT)],name="search_index")
		 print(index)

	print("Going to search..." + choice +" " + string)
	if choice == "0":
		print("CHoice is o")
		result = collection.find({"$text": {"$search": string}}, {"score": {"$meta": "textScore"}}).sort([("score",{"$meta":"textScore"})])
		print (result.count())
	elif choice == "1":
		newstring= '\"' + string + '\"'
		print(newstring)
		result = collection.find({"$text": {"$search": newstring}}, {"score": {"$meta": "textScore"}}).sort([("score",{"$meta":"textScore"})])
		print (result.count())
	#db.messages.find({$text: {$search: "dogs"}}, {score: {$meta: "toextScore"}}).sort({score:{$meta:"textScore"}})
	return result


def refresh(query,graph):
	result  = graph.run(query).data()     #result is an array of dictionary
	#print(len(result))
	data = []

	for dic in result:
		weight = 0
		for j in range(0, len(dic["relArray"])):
			try:
				w = int(dic["relArray"][j]["weight"])
				#print w
			except:
				pass
			else:
				weight = weight + w
		dic["weight"] = weight
		dic.pop('relArray', None)

	result = sorted(result, key=itemgetter('weight'), reverse=True)
	data = []
	for dic in result:
		data.append(dic["m"])
	return data


def update_count(like,dislike,view,fav,video_id):
	
	print( "Like Value: "+ str(like))
	# str_like = str(like)
	# str_dislike = str(dislike)
	# if like < 0:
	# 	str_like = "-" + str(-like)
	queryLike = """

	match (n:TubeVideo{id: """ + "\"" + video_id + "\"" + """})
	set n.likeCount = n.likeCount +  """ + str(like)  + """
	set n.dislikeCount = n.dislikeCount +  """ + str(dislike)  + """
	set n.favoriteCount = n.favoriteCount +  """ + str(fav)  + """
	set n.viewCount = n.viewCount +  """ + str(view)  + """
	return n

	"""

	graph =  Graph("http://neo4j:nilesh123@localhost:7474/db/data/")
	graph.run(queryLike)


	client = MongoClient('mongodb://nilesh:nilesh123@127.0.0.1:27017/')
	db = client.myNewDB
	collection = db.newCollection
	print(type(like))
	result = collection.update_one({'id': video_id }, {'$inc': {'likeCount': like}})
	collection.update_one({'id': video_id }, {'$inc': {'dislikeCount': dislike}})
	collection.update_one({'id': video_id }, {'$inc': {'viewCount': view}})
	collection.update_one({'id': video_id }, {'$inc': {'favoriteCount': fav}})

	#print(result)


# Gives popular videos
def get_recomended():
	client = MongoClient('mongodb://nilesh:nilesh123@127.0.0.1:27017/')
	db = client.myNewDB
	collection = db.newCollection
	result = collection.find().sort([("viewCount",-1)]).limit(35)
	data = []
	print(type(result))
	for obj in result:
		jsonObj = {}
		jsonObj = obj
		jsonObj.pop("_id",None)
		data.append(jsonObj)

	return data

def get_query_view(request):
	prev_query = QueryLog.objects.get()
	print("Got autocomplete request")
	print(prev_query)
	return HttpResponse(json_dumps({"data":['abcd','newmovie']},content_type="application/json"))


def category_view(request):
	recomended = get_recomended()
	if 'val' not in request.GET:
		return index(request)
	category = request.GET['val']
	client = MongoClient('mongodb://nilesh:nilesh123@127.0.0.1:27017/')
	db = client.myNewDB
	collection = db.newCollection

	if category == "10":
  		result=collection.find({"categoryId":"10"})
   
	elif category == "25":
		result=collection.find({"categoryId":"25"})
   
	elif category == "24":
		result=collection.find({"categoryId":"24"})

	elif category == "27":
		result=collection.find({"categoryId":"27"})
	
	data = []
	
	for obj in result:
		obj.pop("_id",None)
		data.append(obj)


	playingNow = recent_current_video

	if request.user.is_authenticated():
		print("User is authenticated")
		return render(request,'itube/topbarloggedin.html',{"recomended":recomended, "currentVedio":playingNow, "result":data,"count":len(data)})
	return render(request,'itube/topbar.html',{"recomended":recomended,"currentVedio":playingNow, "result":data,"count":len(data)})
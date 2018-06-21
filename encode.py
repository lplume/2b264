import argparse
import base64
from urllib.parse import urlparse
import shutil
from PIL import Image
from pymongo import MongoClient
import requests

ArgParser = argparse.ArgumentParser(description='2b264 - Base64 encode thumbs')
ArgParser.add_argument('-c','--connection', help='MongoDB connection url - example mongodb://localhost:27017/', required=True)
ArgParser.add_argument('-d','--database', help='MongoDB database', required=True)
ArgParser.add_argument('-l','--collection', help='Collection', required=True)
ArgParser.add_argument('-i','--imageurl', help='Image url property', required=True)
ArgParser.add_argument('-t','--thumb', help='Image thumb property', required=True)
ArgParser.add_argument('-rw', '--resizew', help='Resize width dimension', required=True, type=int)
ArgParser.add_argument('-rh', '--resizeh', help='Resize height dimension', required=True, type=int)

args = vars(ArgParser.parse_args())

banner = '''
  ____     ____    ____     __    _  _    
 |___"\ U | __")u |___"\ U /"/_ u| ||"|   
 U __) | \|  _ \/ U __) |\| '_ \/| || |_  
 \/ __/ \ | |_) | \/ __/ \| (_) ||__   _| 
 |_____|u |____/  |_____|u \___/   /|_|\  
 <<  //  _|| \\_  <<  //  _// \\_ u_|||_u 
(__)(__)(__) (__)(__)(__)(__) (__)(__)__) 

'''

print(banner)

client = MongoClient(args['connection'])
db = client[args['database']]

collection = db[args['collection']]

for c in collection.find():
	imgurl = c[args['imageurl']]
	parseResult = urlparse(imgurl)
	print(str(c['_id']) + " " + imgurl + " ", end='')

	if parseResult.scheme in ['http', 'https']:
		try:
			response = requests.get(imgurl, stream=True)
			if response.status_code == 200:
				with open('tmp', 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response
				im = Image.open('tmp')
				im.thumbnail((args['resizew'], args['resizeh']), Image.ANTIALIAS)
				im.save('tmpres', 'PNG', progressive=True, quality=100)
				with open("tmpres", "rb") as image_file:
					encoded_string = base64.b64encode(image_file.read())
				collection.find_one_and_update(
					{"_id": c['_id']}, {"$set": {args['thumb']: encoded_string}})
				print("OK")
			else:
					print("KO - http status != 200")
		except:
			print("KO - connection")
	else:
		print("KO - wrong url schema")

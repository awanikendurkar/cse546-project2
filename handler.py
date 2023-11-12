# import(s)
import face_recognition
import urllib.parse
import os
import pickle
import boto3
from boto3.dynamodb.conditions import Key
import csv

# define aws consts
input_bucket = ""
output_bucket = ""
aws_access_key_id = ""
aws_secret_access_key = ""
region_name = "us-east-1"

# lookup key in given table
def find_in_dynamo_db(table, key):
    print("Searching DynamoDB table")
    response = table.scan(FilterExpression=Key("name").eq(key))
    data = response["Items"]
    for item in data:
        print(item)
    return data

# encode given file
def generate_encoding(filename):
    with open(filename, "rb") as file:
        data = pickle.load(file)
        print(data)
    return data

# push given data to specified bucket using given key
def push_to_s3(data, key, bucket_name):
    print("Pushing data to S3")
    file_name = os.path.splitext(key)[0] + ".csv"
    header = ["year", "major", "name"]
    try:
        with open("/tmp/" + file_name, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerow({"year": data[0]["year"], "major": data[0]["major"], "name": data[0]["name"]})
        with open("/tmp/" + file_name, "rb") as f:
            s3 = boto3.resource(
                service_name="s3",
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            bucket = s3.Bucket(bucket_name)
            bucket.upload_fileobj(f, file_name)
    except Exception as e:
        print(e)
        print("Error in creating and uploading csv to bucket {}.".format(bucket_name))
        raise e

# recognize given face from video specified at path
def face_recognition_from_video(video_path, data):
    print("Recognizing face from video")
    path = "/tmp/"

    os.system("ffmpeg -i " + os.path.join(path, video_path) + " -r 1 " + os.path.join(path, "image-%3d.jpeg"))
    all_files = os.listdir(path)
    image_files = [fname for fname in all_files if fname.endswith(".jpeg")]

    dynamodb = boto3.resource("dynamodb", region_name=region_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    table = dynamodb.Table("student_data")

    for image_file in image_files:
        found_image = face_recognition.load_image_file(os.path.join(path, image_file))
        image_encoding = face_recognition.face_encodings(found_image)

        if not image_encoding:
            continue

        image_encoding = image_encoding[0]

        for i, known_encoding in enumerate(data["encoding"]):
            results = face_recognition.compare_faces([image_encoding], known_encoding)

            if results[0]:
                ans = data["name"][i]
                searched_data = find_in_dynamo_db(table, ans)
                push_to_s3(searched_data, video_path, output_bucket)
                return

    return "no_face_found"

# entrypoint for the lambda function
def face_recognition_handler(event, context):
    print("Handling face recognition event")
    print(event)
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")
    print("Bucket name: {}, Key: {}".format(bucket_name, key))

    s3 = boto3.client("s3", aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)
    s3.download_file(bucket_name, key, "/tmp/" + key)
    data = generate_encoding("encoding")

    return face_recognition_from_video(key, data)
# Convert the Videos to mp3 
import os 
import subprocess
files= os.listdir("Videos")
tutorial_number=1
for file in files:
    file_name=file.split(" [")[0].split(".")[0]
    print(file_name)
    subprocess.run(["ffmpeg", "-i", f"Videos/{file}", f"Audios/{tutorial_number}_{file_name}.mp3"])
    tutorial_number+=1
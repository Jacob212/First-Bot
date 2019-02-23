import time
import sqlite3
import re
import gzip
import requests

conn = sqlite3.connect('Discord.db')
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS Movies (movieID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,titleType TEXT NOT NULL,primaryTitle  TEXT NOT NULL,originalTitle TEXT,season  INTEGER,episodes  INTEGER,releaseYear INTEGER,runtimeMinutes  INTEGER,language  TEXT,genre TEXT,tconst  TEXT NOT NULL, UNIQUE(season,tconst));")
c.execute("CREATE TABLE IF NOT EXISTS Members (userID  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,discordID INTEGER NOT NULL UNIQUE,username  TEXT NOT NULL);")
c.execute("CREATE TABLE IF NOT EXISTS Watched (ID  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,userID  INTEGER,`movieID` INTEGER,episode INTEGER,FOREIGN KEY(movieID) REFERENCES Movies(movieID) ON DELETE SET NULL,FOREIGN KEY(userID) REFERENCES Members(userID) ON DELETE SET NULL);")
conn.commit()

def get_time(give_time):
  elapsed_time = time.time() - give_time
  minutes, seconds = divmod(elapsed_time,60)
  hours, minutes = divmod(minutes,60)
  return str(int(hours))+":"+str(int(minutes))+":"+str(round(seconds,2)) 

def menu():
  option = input("Enter either download or setup: ")
  if option == "download":
    download()
    setup()
  elif option == "setup":
    setup()

def download():
  url = "https://datasets.imdbws.com/title.basics.tsv.gz"
  req = requests.get(url, stream=True)
  total_size = int(req.headers.get('content-length', 0)); 
  with open("./Datasets/title.basics.tsv.gz", "wb") as f:
    for chunk in req.iter_content(1024): 
      if chunk:
        f.write(chunk)
  url = "https://datasets.imdbws.com/title.akas.tsv.gz"
  req = requests.get(url, stream=True)
  total_size = int(req.headers.get('content-length', 0)); 
  with open("./Datasets/title.akas.tsv.gz", "wb") as f:
    for chunk in req.iter_content(1024): 
      if chunk:
        f.write(chunk)
  url = "https://datasets.imdbws.com/title.episode.tsv.gz"
  req = requests.get(url, stream=True)
  total_size = int(req.headers.get('content-length', 0)); 
  with open("./Datasets/title.episode.tsv.gz", "wb") as f:
    for chunk in req.iter_content(1024): 
      if chunk:
        f.write(chunk)

def setup():
  print("Running setup. This could take a minute.")
  start_time = time.time()
  basics = gzip.open("./Datasets/title.basics.tsv.gz", mode="rt", encoding="utf-8")
  movie = []
  tv = []
  for rownum, line in enumerate(basics):
    line = line.rstrip("\n")
    words = line.split("\t")
    if words[1] == "movie":
      movie.append(line)
    elif words[1] == "tvSeries":
      tv.append(line)
  basics.close()

  akas = gzip.open("./Datasets/title.akas.tsv.gz", mode="rt", encoding="utf-8")
  sumLanguages = []
  total = []
  languages = []
  countries = []
  for rownum, line in enumerate(akas):
    line = line.rstrip("\n")
    words = line.split("\t")
    if words[0] != "titleId":
      if total == []:
        total = [words[0]]
        languages = [words[4]]
        countries = [words[3]]
      else:
        if words[0] == total[0]:
          languages.append(words[4])
          countries.append(words[3])
        else:
          sumLanguages.append(total[0]+"\t"+",".join(countries)+"\t"+",".join(languages))
          total = [words[0]]
          languages = [words[4]]
          countries = [words[3]]
  sumLanguages.append(total[0]+"\t"+",".join(countries)+"\t"+",".join(languages))
  akas.close()

  allTitles = []
  index = 0
  for line in movie:
    line = line.rstrip("\n")
    words = line.split("\t")
    done = 0
    while index < len(sumLanguages):
      line2 = sumLanguages[index].rstrip("\n")
      index += 1
      words2 = line2.split("\t")
      if words[0] == words2[0]:
        allTitles.append(line+"\t"+words2[1]+"\t"+words2[2]+"\t\\N\t\\N\n")
        done = 1
        break
      if words2[0] > words[0]:
        index -= 1
        break
    if done == 0:
      allTitles.append(line+"\t\\N\t\\N\t\\N\t\\N\n")

  tvLanguages = []
  index = 0
  for line in tv:
    line = line.rstrip("\n")
    words = line.split("\t")
    done = 0
    while index < len(sumLanguages):
      line2 = sumLanguages[index].rstrip("\n")
      index += 1
      words2 = line2.split("\t")
      if words[0] == words2[0]:
        tvLanguages.append(line+"\t"+words2[1]+"\t"+words2[2]+"\n")
        done = 1
        break
      if words2[0] > words[0]:
        index -= 1
        break
    if done == 0:
      tvLanguages.append(line+"\tNone\tNone\n")

  episodes = gzip.open("./Datasets/title.episode.tsv.gz", mode="rt", encoding="utf-8")
  info = []
  noInfo = []
  for rownum, line in enumerate(episodes):
    line = line.rstrip("\n")
    words = line.split("\t")
    if not(words[2] == "\\N" or words[3] == "\\N" or words[0] == "tconst"):
      info.append(words)
    elif not(words[0] == "tconst"):
      noInfo.append(words)
  episodes.close()
  info = sorted(info,key=lambda x:(x[1],int(x[2]),int(x[3])))

  numbers = []
  total = []
  for line in info:
    if total == []:
      total = [line[1]+"\t"+line[2]]
    else:
      if line[1]+"\t"+line[2] in total:
        total.append(line[1]+"\t"+line[2])
      else:
        numbers.append(total[0]+"\t"+str(len(total)))
        total = [line[1]+"\t"+line[2]]
  numbers.append(total[0]+"\t"+str(len(total)))

  index = 0
  for line in tvLanguages:
    line = line.rstrip("\n")
    words = line.split("\t")
    done = 0
    while index < len(numbers):
      words2 = numbers[index].split("\t")
      index += 1
      if words[0] == words2[0]:
        allTitles.append(line+"\t"+words2[1]+"\t"+words2[2]+"\n")
        done = 1
      if words2[0] > words[0]:
        index -= 1
        break
    if done == 0:
      allTitles.append(line+"\t\\N\t\\N\n")
  print("Finished in "+get_time(start_time))

  print("Importing titles into database")
  imported = 0
  notImported = 0
  start_time = time.time()
  tenSeconds = time.time()
  for line in allTitles:
    line = line.rstrip("\n")
    words = line.split("\t")
    try:
      c.execute("INSERT INTO Movies VALUES(?,?,?,?,?,?,?,?,?,?,?)", (None,words[1],words[2],words[3],words[11],words[12],words[5],words[7],words[10],words[8],words[0]))
      imported += 1
    except:
      notImported += 1
    if (time.time()-tenSeconds) > 10:
      print("Imported: "+str(imported)+"| Already in database: "+str(notImported)+"| Total time: "+get_time(start_time))
      tenSeconds = time.time()
      conn.commit()
  conn.commit()
  print("Imported: "+str(imported)+"| Already in database: "+str(notImported)+"| Total time: "+get_time(start_time)+"\nFinshed")

menu()
c.close()
conn.close()
input()
#c.execute("SELECT Movies.primaryTitle FROM Movies WHERE primaryTitle = ? AND season = ? ORDER BY Movies.primaryTitle, Movies.season;",(primaryTitle,season))
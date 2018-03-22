#!/usr/bin/python3

#last update : 2018/3/21
#author : justbio
#version : 1.0.0
#make graph from apache access logs

import os, sqlite3, datetime, re
import matplotlib
import numpy as np
import geoip2.database
from matplotlib import colors
matplotlib.use('Agg')  #setting in linux to not use x-window
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

matplotlib.rcParams['toolbar'] = 'None'
#plt.rcParams['font.sans-serif']=['SimHei']
#matplotlib.rcParams['font.family']='sans-serif'

def read_config():
    #open config file
    try:
        with open("conf/config.ini","r") as f:
            lines=f.readlines()
    except:
        print("ERROR: config.ini not found, please make sure config.ini in ./conf/")

    #read congfig file to dictionary
    paths={}
    for i in range(0,2):
        line=lines[i].strip("\n").split("=")
        paths.update({line[0] : line[1]})

    basepath = os.path.abspath(__file__).strip("mk_graph.py")

    paths.update({"basepath" : basepath})

    
    #if setting is null, make default setting
    if not paths["logpath"]:
        paths["logpath"] = "/var/log/httpd/"
        print("INFO: logpath setting is null, set logpath to /var/log/httpd/")
    if not paths["graphpath"]:
        paths["graphpath"] = basepath + "/pngs/" 
        print("INFO: graphpath setting is null, set logfile to ./pngs/")
    
    #check path exists, make dir if not exists 
    if not os.path.exists(paths["logpath"]):
        print("INFO: logpath not exist ,creating logpath")
        os.makedirs(paths["logpath"], 0o755)

    if not os.path.exists(paths["graphpath"]):
        print("INFO: graphpath not exist ,creating graphpath")
        os.makedirs(paths["graphpath"], 0o755)

    return paths

def get_filenames(logpath):
    file_list = []
    allfile = os.listdir(logpath)
    for file in allfile:
        if re.match("^access.*\.log$",file):
            file_list.append(file)
    return file_list

def spilt_logs(line):
    log=line.strip("\n")
    #split log with "
    a=log.split('"')
    #split 1st block with blank
    b=a[0].split()
    ip=b[0]
    #the block like [02/Feb/2018:04:56:14 ,split it to 02/Feb/2018 and 04 56 14
    dt=b[3][1:].split(':')
    trans={"Jan":"01","Feb":"02","Mar":"03","Apr":"04","May":"05","Jun":"06","Jul":"07","Aug":"08","Sep":"09","Oct":"10","Nov":"11","Dec":"12"}
    c=dt[0].split('/')
    date=c[2]+trans[c[1]]+c[0]
    time=dt[1]
    #split 2nd block with blank,get destnation
    dest=a[1].split()[1]
    #split 3rd block with blank,get code
    code=a[2].split()[0]
    return ip,date,time,dest,code

def analyze_logs(logpath):
    #set key for no use log
    key="spider|Googlebot|bingbot|AdsBot|Yahoo! Slurp|127.0.0.1|.png|.jpg|.js|.css|.mp4|.ico|404|301|x16|x03|x01"
    #get file list
    file_list=get_filenames(logpath)
    #question and answer
    print("insert these logfiles into database?")
    print(file_list)
    print("'y' for insert logfiles into database,'n' for select data from exist database")
    answer1 = input("please input [y/n],enter for NO:")
    if answer1 == "Y" or answer1 == "y":
        #make connection to sqlite3 ,if not exist, create new db file automaticly
        conn=sqlite3.connect('./logs.db')
        cursor=conn.cursor()
        #check table 'logs' exist, if not exist, create new table
        try:
            cursor.execute("select * from log limit 1")
        except:
            cursor.execute("CREATE TABLE logs(ip TEXT,date TEXT,time TEXT,dest TEXT,code int)")
            print("INFO: table 'logs' not exist ,creating table 'logs'")
        #open each file
        print("INFO: inserting logs ...")
        for files in file_list:
            with open(logpath + files,'r') as f:
                lines = f.readlines()
                #compile each line
                for line in lines:
                    #if match key ,do nothing
                    if re.search(key, line):
                        pass 
                    #if not match key ,insert into sqlite3
                    else:
                        try:
                            res=spilt_logs(line)
                        except:
                            continue
                        sql='insert into logs (ip, date, time, dest, code) values("'+res[0]+'","'+res[1]+'","'+res[2]+'","'+res[3]+'","'+res[4]+'")'
                        cursor.execute(sql)
        #commit and close connection
        conn.commit()
        cursor.close()
    else:
        print("select data from exist database")

def get_data(basepath,sql):
    #get data from sqlite3
    conn=sqlite3.connect(basepath +"/"+ 'logs.db')
    cursor=conn.cursor()
    res=cursor.execute(sql)
    resault=res.fetchall()
    return resault

def get_county(basepath,all_ips):
    all_countries=[]
    for ips in all_ips:
        ip=ips[0]
        count=ips[1]
        #GeoIP2 module IP to country
        reader = geoip2.database.Reader(basepath +"/source/GeoLite2-db/GeoLite2-City.mmdb")
        response = reader.city(ip)
        
        #get country and province
        try:
            country = response.country.iso_code
            province = response.subdivisions.most_specific.name
        except:
            continue
        a=[ip,country,province,count]
        all_countries.append(a)
    return all_countries

def get_provinces(all_countries):
    all_provinces = []
    #get data of China,Hongkong,Taiwan,Macau
    for [ip,country,province,count] in all_countries:
        if country== "CN":
            p=province
        elif country== "HK":
            p="Hongkong"
        elif country== "TW":
            p="Taiwan"
        elif country== "MO":
            p="Macau"
        else:
            continue
        data=[ip,p,country,count]
        all_provinces.append(data)
    return all_provinces

def set_data(data):
    tmp={}
    #sum the same countrie's counts
    for v in data:
        tmp[v[1]] = tmp.get(v[1]) and tmp[v[1]] + v[3] or v[3]
    counted_data= [ [k, v] for (k, v) in tmp.items() ]
    #sort it by counts
    data_sorted=sorted(counted_data,key=lambda c: c[1], reverse=True)
    return data_sorted

def get_lat_lon(basepath, txt):
    #get lonitude and latitude from txt file
    with open(basepath +"/conf/" + txt) as f:
        lines=f.readlines()
    lat_lons={}
    for line in lines:
        line=line.strip("\n")
        ename, cname, lon, lat=line.split(",")
        lat_lon={ename:[cname,float(lon),float(lat)]}
        lat_lons.update(lat_lon)
    return lat_lons

def mk_scatter(data,base,basepath,graphpath,map_type):
    lons = []
    lats = []
    counts = []
    colors = []
    sizes = []
    names = []
    #get data for graph
    for i in range(len(data)):
        row = data[i]
        #get lon,lat,name,count
        try:
            lon = float(base[row[0]][1])
            lat = float(base[row[0]][2])
            name = base[row[0]][0]
            count = row[1]
        #skip if not exist
        except:
            continue
        #from count get scatter size and color
        if count >= 10000:
            color = "#ff6666"  #red
            if count > 40000:
                size = 2000
            else:
                size = count/20
        elif count < 10000 and count >= 5000:
            color = "#ffa500"  #orange
            size = count/20
        elif count < 5000 and count >= 100:
            color = "#ffff00"  #yellow
            size = 40
        else:
            color = "#3399ff"  #sky blue
            size = 40
        sizes.append(size)
        names.append(name)
        counts.append(count)
        lons.append(lon)
        lats.append(lat)
        colors.append(color)
    
    #set image size
    plt.figure(figsize=(10,6))
    
    #Basemap projection
    if map_type == "china":
        print("INFO: making china scatter graph ...")
        #Drow china map
        map = Basemap(projection='mill',llcrnrlat=18,urcrnrlat=54,llcrnrlon=73,urcrnrlon=140)
        map.readshapefile(basepath + "source/shapefile/CHN_adm1","state",drawbounds=True)
    elif map_type == "world":
        print("INFO: making world scatter graph ...")
        #Drop world map
        map = Basemap(projection='mill',llcrnrlat=-70,urcrnrlat=80,llcrnrlon=-180,urcrnrlon=180)
        map.drawcountries(color='0.50',linewidth=0.25)
    map.drawcoastlines(color='0.50', linewidth=0.25)
    map.fillcontinents(color='#066d70')
    
    #set points to main scatter-graph
    x, y = map(lons, lats)
    for i,j,color,size in zip(x,y,colors,sizes):
        cs = map.scatter(i,j,size,marker='h',c=color, zorder=10,alpha=0.8)

    #set title for main scatter-graph
    plt.title("Website Access Counts in Last 3 Month over" + map_type)
    
    #set sub bar-graph for most 5 accessed contries
    if map_type == "china":
        plt.axes([0.685, 0.11, 0.2, 0.2])
    elif map_type == "world":
        plt.axes([0.13, 0.16, 0.2, 0.2])
    plt.bar(names[0:5],counts[0:5],color=colors[0:5]) 
    
    #set title for sub bar-graph
    plt.title("Most 5 Accessed Area", fontsize='small')
    plt.yticks([])
    #set text for sub bar-graph
    for i, j in zip(range(0,5),counts[0:5]):
        plt.text(i,counts[0]/2,j,ha='center')

    #set legend
    pointx=[0.2,0.2,0.2,0.2]
    pointy=[0.8,0.6,0.4,0.2]
    color=["#ff6666","#ffa500","#ffff00","#3399ff"]
    text=[">10K","5K-10K","0.1K-5K","<0.1K"]
    if map_type == "china":
        plt.axes([0.143, 0.11, 0.1, 0.1])
    elif map_type == "world":
        plt.axes([0.80, 0.16, 0.1, 0.1])
    plt.scatter(pointx,pointy,40,marker='h',c=color)

    for n ,m ,t in zip(pointx, pointy, text):
        plt.text(n+0.1,m,t,ha='left',va='center')
    plt.xticks([0,1],[])
    plt.yticks([0.1,1],[])

    #save image
    plt.savefig(graphpath + "/"+ map_type +"_scatter.png")

def mk_bar(data, graphpath, name, totle=""):
    #get xticks data list and yticks data list
    x_data = []
    y_data = []
    for row in data:
        x=row[0]
        y=row[1]
        x_data.append(x)
        y_data.append(y)
    
    plt.figure(figsize=(10,7))

    if name=="day":
        print("INFO: making day bar graph ...")
        #make day bar graph
        color=["blue","cornflowerblue","deepskyblue","darkturquoise","cyan","turquoise","aquamarine","lightskyblue","lightblue"]
        plt.bar(x_data,y_data,color=color,alpha=0.7)
        plt.text(len(x_data)/2,1000,"Totle access:" + str(totle[0][0]),ha='center')
        plt.xticks(rotation=90)
        plt.ylabel("accesses") 
    elif name=="hour":
        print("INFO: making hour pie graph ...")
        #make hour pie graph
        x=[np.pi/180*x for x in np.arange(7.5,360,15)]
        w=np.pi/12
        y=y_data
        color=["black","grey","silver","lightblue","skyblue","cyan","limegreen","greenyellow","gold","orange","orangered","red"]
        color.extend(color[::-1])
        fig=plt.figure(figsize=(10,6))
        ax=plt.subplot(111,projection='polar')
        ax.set_theta_zero_location('N')
        ax.set_thetagrids(np.arange(0.0, 360.0, 15.0))
        ax.set_theta_direction(-1)
        ax.set_xticklabels([str(x)+":00" for x in range(0,25)])
        ax.set_rlabel_position(180)
        plt.bar(x,y,w,color=color,alpha=0.7)
    elif name=="URL":
        print("INFO: making URL bar graph ...")
        #make URL bar graph
        color=['lightgrey', 'palegreen', 'greenyellow', 'lawngreen', 'yellow', 'gold', 'lightsalmon', 'darksalmon', 'salmon', 'coral', 'tomato', 'orangered', 'red', 'brown','maroon']
        plt.barh(x_data[::-1],y_data[::-1],color=color,alpha=0.7)
        for m,n in zip (range(0,len(x_data)), x_data[::-1]):
            plt.text(1,m,n,ha='left',va='center')
        plt.yticks([])
        plt.xlabel("accesses")
        plt.ylabel("URLs")

    #set title for graph
    plt.title("Accesses Count Every " + name.capitalize())
    
    plt.savefig(graphpath +  "/"+ name +"_bar.png")

def main():
    config = read_config()
    logpath = config["logpath"]
    graphpath = config["graphpath"]
    basepath = config["basepath"]
    analyze_logs(logpath)

    #get start_date and end_date
    start_date = input("please input start date \(format:YYYYMMDD\):" )
    end_date = input("please input end date \(format:YYYYMMDD\):" )
    while not re.match("[12]{1}[0-9]{3}[01]{1}[0-9]{1}[0-3]{1}[0-9]{1}",start_date):
        start_date = input("please input creccot format start date \(format:YYYYMMDD\):" )
    while not re.match("[12]{1}[0-9]{3}[01]{1}[0-9]{1}[0-3]{1}[0-9]{1}",end_date): 
        end_date = input("please input creccot format end date \(format:YYYYMMDD\):" )
    #=================make bar graph by date====================== 

    #get data for sum access
    sql1a='select count(*) from logs where date >= "'+ start_date +'" and date <= "'+ end_date +'"'
    all_access=get_data(basepath,sql1a)
    
    #get data for daily sum access
    sql1b='select date, count(*) from logs where date >= "'+ start_date +'" and date <= "'+ end_date +'" group by date order by date'
    day_access=get_data(basepath,sql1b)

    #make graph
    try:
        mk_bar(day_access,graphpath,"day",all_access)
    except Exception as e:
        print(e)
        print("ERROR: making day bar graph Failed, do next graph")
        pass
     
    #=================make bar graph by hour====================== 

    #get data for hour sum access
    sql2='select time, count(*) from logs where date >= "'+ start_date +'" and date <= "'+ end_date +'" group by time order by time'
    hour_access=get_data(basepath,sql2)

    #make graph
    try:
        mk_bar(hour_access,graphpath,"hour")
    except Exception as e:
        print(e)
        print("ERROR: making hour pie graph Failed, do next graph")
        pass
   
    #=================make bar graph by access page====================== 

    #get data for destination sum access
    sql3='select dest, count(*) from logs where date >= "'+ start_date +'" and date <= "'+ end_date +'" group by dest order by count(*) desc limit 15'
    dest_access=get_data(basepath,sql3)

    #make graph
    try:
        mk_bar(dest_access,graphpath,"URL")
    except Exception as e:
        print(e)
        print("ERROR: making URL bar graph Failed, do next graph")
        pass
    
    #=================make scatter graph by aera======================    

    #get data for ip sum access
    sql4='select ip, count(ip) from logs where date >= "'+ start_date +'" and date <= "'+ end_date +'" group by ip'
    all_ips=get_data(basepath,sql4)

    #get all country names with format [ip,name,count]
    all_countries=get_county(basepath,all_ips)
    
     
    try:
        #set data to format [country_name,sum_count]
        data_w=set_data(all_countries)

        #make scatter for world view
        txt_w="countries.ini"
        base_w=get_lat_lon(basepath, txt_w)
        mk_scatter(data_w,base_w,basepath,graphpath, "world")
    except Exception as e:
        print(e)
        print("ERROR: making world scatter graph Failed, do next graph")
        pass
    
    #get all province names with format [ip,name,count]
    all_provinces=get_provinces(all_countries)
    
    try:
        #set data to format [province_name,sum_count]
        data_c=set_data(all_provinces)

        #make scatter for china view
        txt_c="provinces.ini"
        base_c=get_lat_lon(basepath, txt_c)
        mk_scatter(data_c,base_c,basepath,graphpath, "china")
    except Exception as e:
        print(e)
        print("ERROR: making china scatter graph Failed")
        pass

    print("INFO: Jobs Done!!! please check " +graphpath)

if __name__=="__main__":
    main()
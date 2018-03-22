apache access log to graph
=======

`Version:` `1.0.0` </br>
`OS:` `Linux` </br>
`Author:` `justbio`

purpose
-------
make graph from apache access logs.
> Only support default log format now </br>
> LogFormat:`"%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined`

Requirements
------------
Base
* Python3.x

Need to install
* matplotlib
> pip3 install matplotlib
* numpy
> pip3 install numpy
* Basemap
> see [basemaptutorial](http://basemaptutorial.readthedocs.io)

Files 
* geoip2.database
> in `source\GeoLite2-db`
* shapefile
> in `source\shapefile`

Useage
------------
* unzip in any path of linux
* edit conf file
> vim conf/config.ini
>> logpath=apache_log_path_need_to_analyze</br>
>> graphpath=path_to_save_graph
> if not set ,default to 
>> logpath=/var/log/httpd/</br>
>> graphpath=./pngs/

* do it
> python3 mk_graph.py

Example
------------
![](https://github.com/justbio/apache-log-to-graph/blob/master/pngs/example/day_bar.png)
![](https://github.com/justbio/apache-log-to-graph/blob/master/pngs/example/hour_bar.png)
![](https://github.com/justbio/apache-log-to-graph/blob/master/pngs/example/URL_bar.png)
![](https://github.com/justbio/apache-log-to-graph/blob/master/pngs/example/china_scatter.png)
![](https://github.com/justbio/apache-log-to-graph/blob/master/pngs/example/world_scatter.png)
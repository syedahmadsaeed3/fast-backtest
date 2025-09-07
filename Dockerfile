FROM python:3.8
RUN apt-get update \
&& apt-get install gcc python3-dev python-dev -y \
&& apt-get install -y make \
&& apt install build-essential -y\
&& apt-get install wget -y\
&& wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz\
&& tar -xzvf ta-lib-0.4.0-src.tar.gz\
&& cd ta-lib\
&& ./configure --prefix=/usr\
&& make \
&& make install

RUN pip install fastapi
RUN pip install python-dotenv
RUN pip install vectorbt
RUN pip install pandas
RUN pip install numpy

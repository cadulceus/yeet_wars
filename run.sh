docker build . -t py_serv
docker run -d -p 5000:5000 py_serv

cd client
docker build . -t frontend
docker run -d -p 80:80 frontend
# ir-anthology-database
Contains the nessessary files and scripts to download and host the reduced dblp knowledge graph as a sparql database using the Qlever engine.

# Set up locally
Clone repository and install [Qlever](https://docs.qlever.dev/quickstart/).
For the easiest setup having [docker](https://docs.docker.com/get-started/get-docker/) installed is recommended
Run
```
qlever get-data
qlever index
qlever start
```
to run the database directly on localhost:7016.
Or build docker image via 
``` 
docker build -t your/name .
```
and lauch the image via
```
docker run -it your/name
```
to run the database in a docker container on localhost:7016

# Set up with docker container
You can also use the built docker container from this repo from ghcr.TODO

# How it works
```qlever get-data``` data runs the construct query located in query.rq on the dblp endpoint to create a smaller knowledge graph.
The smaller knowledge graph is then saved as full_dump.nt.
```qlever index``` indexes all files with the .nt ending (full_dump.nt).
```qlever start``` launches a docker container to host the database.

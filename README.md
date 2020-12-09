# About
This repository builds a pyhthon:3.8-slim based docker container running the script in the folder src
This script reads in the ini-files in the config folder and then proceeds to download pathway maps from the KEGG API.

The KEGG API has the following Restriction:

> KEGG API is provided for academic use by academic users belonging to academic institutions.

If you are not an academic user belonging to an academic institution please contact KEGG to aquire a licence.

# Building the image
After cloing the repository you can build the image with:

```
docker build -t kpwd .
```

# Running the container
To run the container you need to have two local directories ready to be mounted in the container
One of the directories is used to store the downloaded kgml files.
The other is the location of the config files used by the python script.

Please find an example call below; edit to your preferences and system:

```
docker run -it --volume=${PWD}/data:/data --volume=${PWD}/config:/config kpwd
```

# Configuring the logger
To change the logging behaviour during execution use the file

```
config/logging-config.ini
```

Please refer to the official documentation for instructions.
Most notably you might want to enable DEBUG output by changing the line

```
level=INFO
```

to

```
level=DEBUG
```

in case of errors.

# Configuring the downloader
To change the behaviour of the downloader use the file

> config/keggdownload-config.ini

The following sections are available

## kegg_api
Change the content to be downloaded

### topic
This defines the search term used when querying the `find` endpoint of the API. An example is:

> cancer

### orgCode
Give a three letter organism code to download the maps for this organism. To get the maps for homo sapiens use:

> hsa

If omitted the references maps are fetched.

### map_ids
This is intended to download the listed ids only. This will be made available at a later time.

## container_env
Here you can configure the environment of your specific container setup.
At the moment only the download folder can be configured. Open an Issue if you are in need of more configuration options.

### download_folder
The standard folder inside the container to use and to map the volume to is

> /data

but you change it if you need to use a different folder in the container.
If you omit this setting, the default `/data` will be used.

## No warranties
This tool comes without any warranties. Use at your own risk, I cannot be made liable for any damage to your hard- or software when using this program and to any breach of license you might infringe when using this program without a KEGG license. See below.

## KEGG API Restriction
Just to be safe I will repeat the KEGG restriction here which applies to your use of this software:

```
Restriction:
KEGG API is provided for academic use by academic users belonging to academic institutions.
```
For more details please visit the KEGG website at [https://www.kegg.jp/kegg/rest/]

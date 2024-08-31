# OSM Feature Extractor

## Introduction

Lightweight application to automatically extract features from an OSM file, and map them to 
user defined GeoJSON polygon(s). The mapped features can then be potentially used for machine learning applications based
on OSM data. The extracted features can be a `count` for nodes, a `length` for ways and `area` for areas.

For more details on the features that are extracted, check [FEATURES.md](FEATURES.md) and 
the [OSM wiki](https://wiki.openstreetmap.org/wiki/Map_Features).

Example generated dataframe:

![df](osm_feature_extractor/utils/img/data_frame.png)

Data visualised on a map:

![df](osm_feature_extractor/utils/img/data_kepler.png)

## Usage

After cloning the project into your local machine, you'll need to create a virtual environment with 
the required packages. This can be achieved easily with [Poetry](https://python-poetry.org/), as it 
will make sure all the versions are correct, but alternatively it can be installed by other means
with the `requirements.txt` file provided. At the root directory of the project run:

```shell script
$ poetry install

$ poetry shell
```

When all the packages have been installed and the virtual env is activated, you can then run
the script that will map the features:

```shell script
$ python osm_feature_extractor/main.py
```

The above command will run on an included OSM file `isle-of-wight-latest.osm.pbf` and `isle-of-wight.geojson`.

You can go to [configuration file](proj.conf) in order to adjust the app configuration parameters. 
The main ones are detailed below:

**osm_file**: Name of osm file whose features will be extracted. To download more files visit the 
[geofabrik](https://download.geofabrik.de/) website. <br>
**input_polygons_file**: Name of file containing the GeoJSON polygon(s) for which the OSM features will be mapped against. <br>
**output_file**: Path to the output file where the mapped OSM features are written to. <br>

**Note**: _Large files might take a while to process. It is recommended to use the CLI
[osmium extract](https://docs.osmcode.org/osmium/latest/osmium-extract.html) tool in order to reduce the OSM file to the 
area of interest first and then run the feature extractor._

`


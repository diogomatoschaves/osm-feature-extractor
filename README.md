# OSM Feature Extractor

## Introduction

Lightweight application to automatically extract features from an OSM file, and optionally, to map those features to 
user defined GeoJSON polygons. The mapped features can then be potentially used for machine learning applications based
on OSM data. The main features extracted are:

`amenity`,
`building`,
`craft`,
`cycleway`,
`emergency`,
`highway`,
`historic`,
`landuse`,
`leisure`,
`man_made`,
`military`,
`natural`,
`office`,
`power`,
`public_transport`,
`railway`,
`shop`,
`sport`,
`tourism`

For more details on the features that are extracted, check [FEATURES.md](feature_extractor/feature_augmenting/FEATURES.md) and 
the [OSM wiki](https://wiki.openstreetmap.org/wiki/Map_Features).

## Usage

After cloning the project into your local machine, the first thing will be to create a virtual environment with 
the required packages. For this, it is highly recommended to use conda, as it will make sure all packages can be 
installed. Thus, run:

```shell script
$ conda env create -f environment.yml

$ conda activate osm-feature-extractor 
```

in order to run the app do:

```shell script
$ python feature_extractor/main.py
```

The above command will run on an included OSM file `isle-of-wight-latest.osm.pbf`.

You can go to [configuration file](proj.conf) in order to adjust the app configuration parameters. 
The main ones are detailed below:

`osm_file`: Name of osm file whose features will be extracted. To download more files visit the 
[geofabrik](https://download.geofabrik.de/) website. <br>
`input_data_file`: Name of file containing GeoJSON polygons. Optional. <br>
    _This should be given if you'd like to limit the feature extraction to specific areas. 
    Otherwise the whole OSM file will be extracted into a single polygon encompassing all nodes._ <br>
`out_file`: Path to the output file where all features will be extracted to. <br>

`


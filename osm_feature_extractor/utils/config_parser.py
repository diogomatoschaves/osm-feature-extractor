import argparse
from configparser import ConfigParser
from distutils.util import strtobool


def _convert_booleans(config):
    converted_config = {}
    for config_key, config_value in config.items():
        try:
            converted_config[config_key] = strtobool(config_value)
        except ValueError:
            converted_config[config_key] = config_value
    return converted_config


def _add_extract_sub_parser(subparser, defaults):

    parser = subparser.add_parser(
        "extract", help="Extracts the data from the OSM file and maps it to the GeoJSON features."
    )

    defaults = _convert_booleans(defaults)

    parser.add_argument("--osm-file", dest='osm_file', help="Path to the osm file to be parsed and matched.")

    parser.add_argument(
        "--input-polygons-file",
        dest='input_polygons_file',
        help="Path to input geojson containing a feature collection of the polygons to be mapped.",
    )

    parser.add_argument("--output-file", dest='output_file', help="Path to output generated feature augmented file.")
    
    parser.add_argument(
        "--process-base-data",
        dest='process_base_data',
        help="If base data should be loaded or processed",
        default=True
    )
    
    parser.add_argument(
        "--process-osm-data",
        dest='process_osm_data',
        help="If osm data should be loaded or processed",
        default=True,
    )

    parser.add_argument(
        "--osm-extractor-files-dir",
        dest='osm_extractor_files_dir',
        help="Directory name of temp / generated extractor files",
        default='osm_extractor_files_dir',
    )

    parser.add_argument(
        "--polygons-file",
        dest='polygons_file',
        help="Name of intermediate step polygons file",
        default='polygons.geojson',
    )

    parser.set_defaults(**defaults)


def _add_analyze_sub_parser(subparser, defaults):

    parser = subparser.add_parser(
        "analyze", help="Analyzes the OSM file and outputs the results"
    )

    defaults = _convert_booleans(defaults)

    parser.add_argument(
        "--osm-file",
        dest='osm_file',
        help="Path to the osm file to be parsed and matched.",
    )

    parser.add_argument(
        "--osm-extractor-files-dir",
        dest='osm_extractor_files_dir',
        help="Directory name of temp / generated extractor files",
        default='osm_extractor_files_dir',
    )

    parser.set_defaults(**defaults)


def _get_config_file_parser():
    conf_parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    conf_parser.add_argument(
        "-c",
        "--conf-file",
        help="Specify config file",
        metavar="FILE",
    )
    args, remaining_argv = conf_parser.parse_known_args()

    default_config = {}

    if args.conf_file:
        for command in ['default', 'user-defined']:

            config = ConfigParser()
            config.read(args.conf_file)

            if command in config.sections():
                default_config.update(dict(config.items(command)))

    return conf_parser, default_config, remaining_argv


def get_config():
    conf_parser, default_config, remaining_argv = _get_config_file_parser()

    parser = argparse.ArgumentParser(parents=[conf_parser])
    subparser = parser.add_subparsers(help="command", dest="command")

    _add_extract_sub_parser(subparser, default_config)
    _add_analyze_sub_parser(subparser, default_config)

    config, unknown = parser.parse_known_args(remaining_argv)

    if (config.command == 'extract' and len(default_config.keys()) == 0 and
            (config.osm_file is None or config.input_polygons_file is None or config.output_file is None)):
        parser.error("--osm-file, --input-polygons-file and --output-file are required if --conf-file is not specified.")

    if config.command == 'analyze' and len(default_config.keys()) == 0 and config.osm_file is None:
        parser.error("--osm-file is required if --conf-file is not specified.")

    return config

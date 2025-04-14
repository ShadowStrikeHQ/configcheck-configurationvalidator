import argparse
import json
import logging
import sys
from pathlib import Path

import jsonschema
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def setup_argparse():
    """
    Sets up the argument parser for the configcheck tool.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Validates configuration files against a schema."
    )
    parser.add_argument(
        "config_file",
        type=str,
        help="Path to the configuration file (JSON, YAML, or INI).",
    )
    parser.add_argument(
        "schema_file", type=str, help="Path to the schema file (JSON)."
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "yaml"],
        help="Specify the configuration file format (json or yaml). If omitted, it will be inferred from the file extension.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level.",
    )
    return parser


def load_config(config_file, file_format=None):
    """
    Loads the configuration file based on its format.

    Args:
        config_file (str): Path to the configuration file.
        file_format (str, optional): Format of the configuration file ("json" or "yaml").
                                     If None, it's inferred from the file extension. Defaults to None.

    Returns:
        dict: The loaded configuration data as a dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the file format is not supported or cannot be inferred.
        Exception: If any other error occurs during file reading or parsing.
    """
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    if file_format is None:
        if config_path.suffix.lower() == ".json":
            file_format = "json"
        elif config_path.suffix.lower() == ".yaml" or config_path.suffix.lower() == ".yml":
            file_format = "yaml"
        else:
            raise ValueError(
                "Could not infer configuration file format. Please specify using --format."
            )

    try:
        with open(config_file, "r") as f:
            if file_format == "json":
                config_data = json.load(f)
            elif file_format == "yaml":
                config_data = yaml.safe_load(f)  # Safe load to prevent arbitrary code execution
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

        return config_data
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        raise
    except yaml.YAMLError as e:
        logging.error(f"Error decoding YAML: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise


def load_schema(schema_file):
    """
    Loads the JSON schema from the specified file.

    Args:
        schema_file (str): Path to the JSON schema file.

    Returns:
        dict: The loaded JSON schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the schema file contains invalid JSON.
        Exception: If any other error occurs during file reading or parsing.
    """
    try:
        with open(schema_file, "r") as f:
            schema = json.load(f)
        return schema
    except FileNotFoundError as e:
        logging.error(f"Schema file not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON schema: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise


def validate_config(config_data, schema):
    """
    Validates the configuration data against the provided JSON schema.

    Args:
        config_data (dict): The configuration data to validate.
        schema (dict): The JSON schema to validate against.

    Returns:
        None

    Raises:
        jsonschema.exceptions.ValidationError: If the configuration data does not conform to the schema.
        jsonschema.exceptions.SchemaError: If the schema itself is invalid.
    """
    try:
        jsonschema.validate(instance=config_data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        logging.error(f"Configuration validation error: {e}")
        raise
    except jsonschema.exceptions.SchemaError as e:
        logging.error(f"Invalid schema: {e}")
        raise


def main():
    """
    Main function to orchestrate the configuration validation process.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # Set log level based on command-line argument
    logging.getLogger().setLevel(args.log_level)

    try:
        config_data = load_config(args.config_file, args.format)
        schema = load_schema(args.schema_file)
        validate_config(config_data, schema)
        logging.info("Configuration is valid.")
        print("Configuration is valid.")  # Add user-friendly output
    except FileNotFoundError as e:
        logging.error(e)
        print(f"Error: {e}")  # Add user-friendly output
        sys.exit(1)
    except ValueError as e:
        logging.error(e)
        print(f"Error: {e}")  # Add user-friendly output
        sys.exit(1)
    except jsonschema.exceptions.ValidationError as e:
        logging.error(e)
        print(f"Configuration validation error: {e}")  # Add user-friendly output
        print(e)
        sys.exit(1)
    except jsonschema.exceptions.SchemaError as e:
        logging.error(e)
        print(f"Schema error: {e}")  # Add user-friendly output
        print(e)
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}") # Add user-friendly output
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Usage Examples (not part of the code, but for documentation)
#
# Example 1: Validate a JSON config file against a JSON schema
# python configcheck.py config.json schema.json
#
# Example 2: Validate a YAML config file against a JSON schema
# python configcheck.py config.yaml schema.json --format yaml
#
# Example 3: Validate a YAML config file (explicit format) and set log level to DEBUG
# python configcheck.py config.yml schema.json --format yaml --log-level DEBUG
#
# Example config.json:
# {
#   "name": "My Application",
#   "version": "1.0.0",
#   "settings": {
#     "log_level": "INFO",
#     "max_connections": 10
#   }
# }
#
# Example config.yaml:
# name: My Application
# version: 1.0.0
# settings:
#   log_level: INFO
#   max_connections: 10
#
# Example schema.json:
# {
#   "type": "object",
#   "properties": {
#     "name": { "type": "string" },
#     "version": { "type": "string" },
#     "settings": {
#       "type": "object",
#       "properties": {
#         "log_level": { "type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"] },
#         "max_connections": { "type": "integer", "minimum": 1 }
#       },
#       "required": ["log_level", "max_connections"]
#     }
#   },
#   "required": ["name", "version", "settings"]
# }
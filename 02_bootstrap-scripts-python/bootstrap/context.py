# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import abc
import json
import re
from deepmerge import always_merger
from ruamel.yaml import YAML
from jsonpath_ng import parse
from os import environ
from typing import Union, Any


_yaml = YAML(typ='safe')
_ALPHANUM_RE = re.compile('[\W_]+')
_TRUE_STRINGS = ['true', 'y']
_EXTENDED_TRUE_STRINGS = ['true', 'y', 't', 'yes']
_FALSE_STRINGS = ['false', 'n']
_TYPE_PARSE = {
    'STRING': lambda x: str(x),
    'BOOLEAN': lambda x: str(x) in _EXTENDED_TRUE_STRINGS,
    "NUMBER": lambda x: int(x)
}


def stringToNestedObject(locator: str, value: Any, ob: dict, separator: str = "."):
    """
    This helper functions takes a string to represent a JSONPath like string, and a value,
    and puts the value in the correct nested object inside the provided object.

    :param: locator: JSONPath-like string to denote object hierarchy
    :param: value: The value to insert
    :param: ob: The object to insert the value into
    :param: separator (optional): The delimiter in the locator to use, defaults to "."
    """
    splitit = locator.split(separator)
    buffer = ob
    for idx, val in enumerate(splitit):
        if val not in buffer.keys():
            buffer[val] = {}
        if idx < len(splitit) - 1:
            buffer = buffer[val]
        else:
            if type(value) == type(str()):
                if value.lower() == 'false':
                    buffer[val] = bool("")
                elif value.lower() == 'true':
                    buffer[val] = bool(value)
                else:
                    buffer[val] = value
            else:
                buffer[val] = value


class HelmValuesContext:
    """
    Abstract class to be implemented by other contexts.
    """
    def __init__(self, primaryInd: str, options: dict):
        """
        All contexts contain the indicator and an object to represent arbitrary
        options that are specific to a specific context type.
        """
        self.indicator: str = primaryInd
        self.options: dict = options

    @abc.abstractmethod
    def GetValues(self) -> dict:
        """Implement this method. Return values"""
        return {}

    @staticmethod
    @abc.abstractmethod
    def get_context_string() -> str:
        """Implement this method. Return a string representing the type of this context"""
        return ""


class EnvironmentVariablesContext(HelmValuesContext):
    """
    This context takes all environment variables matching the prefix provided as
    the indicator, and places them at the root of the values object. Nested objects
    can be created with the "__" separator in the variable name.
    """
    def GetValues(self) -> dict:
        values: dict = {}
        keys = list(filter(lambda x: x.startswith(
            self.indicator), environ.keys()))
        for key in keys:
            newKey = key.replace(self.indicator, "")
            value: Union([str, bool, int]) = environ[key]
            splitVal = value.split(":")
            if len(splitVal) > 1 and splitVal[-1] in _TYPE_PARSE.keys():
                type = splitVal[-1]
                newVal = ":".join(splitVal[0:-2])
                if type == "STRING":
                    value = newVal
                elif type == "BOOLEAN":
                    value = newVal.lower() in _TRUE_STRINGS
                elif type == "NUMBER":
                    value = int(newVal)
            elif value in _TRUE_STRINGS:
                value = True
            elif value in _FALSE_STRINGS:
                value = False
            stringToNestedObject(newKey, value, values, separator="__")
        return values

    @staticmethod
    def get_context_string() -> str:
        return "environment"


class VariableContentContext(HelmValuesContext):
    """
    Take an environment variable that contains structured data (currently only JSON)
    and parse that structured data and add to the values at the root (or location
    specified by the "key" option)
    """
    def GetContent(self, content: str) -> dict:
        type = self.options["type"]
        if type.lower() == "json":
            return json.loads(content)
        else:
            return {}

    def GetValues(self) -> dict:
        content = environ[self.indicator]
        if "key" in self.options.keys():
            sep: str = self.options.get("separator", ".")
            values: dict = {}
            stringToNestedObject(
                self.options["key"], self.GetContent(content), values, separator=sep)
            return values
        else:
            return self.GetContent(content)

    @staticmethod
    def get_context_string() -> str:
        return "varcontent"


class RawValueContext(HelmValuesContext):
    """
    Set a value directly. The indicator is the path to set, the "value" option
    is the value that will get set.
    """
    def GetValues(self) -> dict:
        sep: str = self.options.get("separator", ".")
        values: dict = {}
        stringToNestedObject(
            self.indicator, self.options.get("value", "null"), values, separator=sep)
        return values

    @staticmethod
    def get_context_string() -> str:
        return "raw"


class FileContext(HelmValuesContext):
    """
    This context reads a file, parses it, and adds it to the values. The primary
    indicator is the path to the file, and the following options can be specified:
    - type: the type of the file, currently yaml or json (implied)
    - pathfilter: JSONPath of the top level key to read into the values, optional
    - key: the location of the top level key of the values in the context
    """
    def GetValues(self) -> dict:
        filename = self.indicator
        parsetype = ""
        sep: str = self.options.get("separator", ".")
        if "type" in self.options.keys():
            parsetype = self.options["type"]
        with open(filename, 'r') as stream:
            if parsetype.lower() == "yaml":
                obj = _yaml.load(stream)
            else:
                obj = json.load(stream)
        if "pathfilter" in self.options.keys():
            expr = parse("$" + self.options["pathfilter"])
            try:
                obj = expr.find(obj)[0].value
            except Exception as e:
                print(e)
                print(f"Primary: {self.indicator}")
                print(f"Options: {self.options}")
                print("Filter returned no results, returning null")
                return {}
        if "key" in self.options.keys():
            new_values: dict = {}
            stringToNestedObject(
                self.options["key"], obj, new_values, separator=sep)
            obj = new_values
        return obj

    @staticmethod
    def get_context_string() -> str:
        return "file"

class JSONContext(HelmValuesContext):
    """
    Pass raw json or yaml as the indicator. Has the following options:
    - type: the type of the content, currently yaml or json (implied)
    - pathfilter: JSONPath of the top level key to read into the values, optional
    - key: the location of the top level key of the values in the context
    """
    def GetValues(self) -> dict:
        jsonobj = self.indicator
        parsetype = ""
        sep: str = self.options.get("separator", ".")
        if "type" in self.options.keys():
            parsetype = self.options["type"]
            if parsetype.lower() == "yaml":
                obj = _yaml.load(jsonobj)
            else:
                obj = json.loads(jsonobj)
        if "pathfilter" in self.options.keys():
            expr = parse("$" + self.options["pathfilter"])
            try:
                obj = expr.find(obj)[0].value
            except Exception as e:
                print(e)
                print(f"Primary: {self.indicator}")
                print(f"Options: {self.options}")
                print("Filter returned no results, returning null")
                return {}
        if "key" in self.options.keys():
            new_values: dict = {}
            stringToNestedObject(
                self.options["key"], obj, new_values, separator=sep)
            obj = new_values
        return obj

    @staticmethod
    def get_context_string() -> str:
        return "json"


class GenericMultiMuxContext(HelmValuesContext):
    """
    Perform a complex mapping of values from one file based on a key in another.
    The indicator is not used, and all values are configured via the options.
    The options available:
    - TargetSchemaFile: The file which contains the values that need to be added
    to the context, as well as where the mapping key exists. Values from this file
    are added to the context regardless of the mapping.
    - SourceMappingFile: The file that contains the mappings.
    - TargetKey: JSONPath-like string that locates the array in the TargetSchemaFile
    where mappings are to be performed.
    - TargetLookupKey: The name of the key in the objects found in TargetKey to
    use to map the value from SourceMappingFile.
    - TargetDestinationKey: The name of the key to insert the mapped value from
    SourceMappingFile into the objects in the context.
    - SourceMappingPathfilter (optional): Filter to use to locate the specific
    mapping int the SourceMappingFile.
    Example:
    FileA.json:
    ```
    {
        "values": [
            {
                "name": "foo"
            }
        ]
    }
    ```
    FileB.json:
    ```
    {
        "results": {
            "foo": "bar"
        }
    }
    ```
    Context:
    - TargetSchemaFile: FileA.json
    - SourceMappingFile: FileB.json
    - TargetKey: "values"
    - TargetLookupKey: "name"
    - TargetDestinationKey: "id"
    - SourceMappingPathfilter: "results"
    Resulting Values:
    ```
    {
        "values": [
            {
                "name": "foo",
                "id": "bar"
            }
        ]
    }
    ```
    """
    def __init__(self, primaryInd: str, options: dict):
        super().__init__(primaryInd, options)
        with open(self.options["TargetSchemaFile"], 'r') as f:
            self.target_schema = json.load(f)
        with open(self.options["SourceMappingFile"], 'r') as f:
            self.source_mapping = json.load(f)
        self.target_key = None
        if "TargetKey" in self.options.keys():
            self.target_key = self.options["TargetKey"]
            self.target_key_parse = parse("$." + self.target_key)
        self.target_lookup_key = parse("$." + self.options["TargetLookupKey"])
        self.target_destination_key = self.options["TargetDestinationKey"]
        self.source_mapping_pathfilter = None
        if "SourceMappingPathfilter" in self.options.keys():
            self.source_mapping_pathfilter = parse(
                "$." + self.options["SourceMappingPathfilter"])

    def evaluate_mapping(self, key: str) -> Any:
        search = self.source_mapping.copy()
        if self.source_mapping_pathfilter is not None:
            search = self.source_mapping_pathfilter.find(search)[0].value
        try:
            return search[key]
        except Exception as e:
            print("A Mapping failed:")
            print("Key: " + key)
            print(e)
            return None

    def get_mapping_key(self, sub_object: dict) -> str:
        raw_key = self.target_lookup_key.find(sub_object)[0].value
        sub_key = _ALPHANUM_RE.sub('', raw_key)
        return sub_key

    def get_toplevel_iterable(self) -> dict:
        out_object = self.target_schema.copy()
        if self.target_key is not None:
            out_object = self.target_key_parse.find(out_object)[0].value
        return out_object

    def insert_mapped_value(self, value: Any, original: dict) -> dict:
        dest = original.copy()
        stringToNestedObject(self.target_destination_key, value, dest)
        return dest

    def GetValues(self) -> dict:
        values = []
        top_iter = self.get_toplevel_iterable()
        for item in top_iter:
            mapping = self.get_mapping_key(item)
            mapped_value = self.evaluate_mapping(mapping)
            values.append(self.insert_mapped_value(mapped_value, item))
        return {
            self.target_key: values
        }


class HelmValuesBuilder:
    """
    Helper class to assist in registration of context instances. Can add contexts
    from strings, or add them from already instantiated instances of HelmValuesContext.
    """
    def __init__(self):
        self.contexts = []

    def add_context(self, context: HelmValuesContext):
        self.contexts.append(context)

    def add_context_from_string(self, context_str: str):
        #Take string of format <context>:<context primary indicator>:<context config>
        print(context_str)
        context_parts = context_str.split(":")
        context_name = context_parts[0]
        primary = context_parts[1]
        options = {}
        if len(context_parts) > 2:
            opts = context_parts[2].split(",")
            for opt in opts:
                spl = opt.split("=")
                options[spl[0]] = spl[1]
        if EnvironmentVariablesContext.get_context_string() == context_name:
            ctx: HelmValuesContext = EnvironmentVariablesContext(
                primary, options)
        elif RawValueContext.get_context_string() == context_name:
            ctx = RawValueContext(primary, options)
        elif VariableContentContext.get_context_string() == context_name:
            ctx = VariableContentContext(primary, options)
        elif FileContext.get_context_string() == context_name:
            ctx = FileContext(primary, options)
        elif JSONContext.get_context_string() == context_name:
            ctx = FileContext(primary, options)
        self.add_context(ctx)

    def get_values(self):
        all_values = {}
        for ctx in self.contexts:
            always_merger.merge(all_values, ctx.GetValues())
        return all_values

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple, Union

from .string_utils import capitalize_first_letter


class DataType(Enum):
    STRING = "string"
    BOOLEAN = "boolean"
    NUMBER = "number"
    INTEGER = "integer"
    LONG = "long"
    FLOAT = "float"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class Property:
    name: str
    obfuscate_name: str
    type: DataType
    description: str = ""
    items: Union["Property", None] = None
    properties: Dict[str, "Property"] = field(default_factory=dict)


@dataclass
class Class:
    name: str
    properties: Dict[str, Property] = field(default_factory=dict)
    description: str = ""


class SchemaParser:
    def parse(self, schema: Dict[str, Any]) -> List[Class]:
        classes = []
        main_class = Class(
            name=schema.get("title", "MainClass").rstrip("VO").rstrip("DTO")
        )
        main_class.description = schema.get("description", "")

        for key, data in schema.get("properties", {}).items():
            prop = self._parse_property(key, data)
            main_class.properties[prop.name] = prop
            classes.extend(self._extract_nested_classes(prop.name, prop))

        classes.insert(0, main_class)
        return classes

    def _parse_property_name(self, prop_name: str) -> Tuple[str, str]:
        """
        mystical(o_userGid) => ("mystical", "userGid")
        """
        pattern = r"(\w+)\((\w+)\)"
        matches = re.match(pattern, prop_name)
        if matches:
            return matches.group(1), matches.group(2)[2:]
        else:
            return prop_name, prop_name

    def _parse_property(self, key: str, data: Dict[str, Any]) -> Property:
        obfuscate_name, name = self._parse_property_name(key)
        prop_type = DataType(data.get("type", "string"))
        description = data.get("description", "")

        if prop_type == DataType.ARRAY:
            items = self._parse_property(f"{name}Item", data.get("items", {}))
            return Property(
                name=name,
                obfuscate_name=obfuscate_name,
                type=prop_type,
                description=description,
                items=items,
            )
        elif prop_type == DataType.OBJECT:
            properties = {
                k: self._parse_property(k, v)
                for k, v in data.get("properties", {}).items()
            }
            return Property(
                name=name,
                obfuscate_name=obfuscate_name,
                type=prop_type,
                description=description,
                properties=properties,
            )
        else:
            if prop_type == DataType.NUMBER:
                mock_type = data.get("mock", {}).get("mock")
                if mock_type == "@float":
                    prop_type = DataType.FLOAT
                elif mock_type == "@Long":
                    prop_type = DataType.LONG

            return Property(
                name=name,
                obfuscate_name=obfuscate_name,
                type=prop_type,
                description=description,
            )

    def _extract_nested_classes(self, name: str, prop: Property) -> List[Class]:
        classes = []
        if prop.type == DataType.OBJECT:
            new_class = Class(name=capitalize_first_letter(name))
            new_class.properties = prop.properties
            classes.append(new_class)
            for nested_prop in prop.properties.values():
                classes.extend(
                    self._extract_nested_classes(
                        f"{capitalize_first_letter(name)}{capitalize_first_letter(nested_prop.name)}",
                        nested_prop,
                    )
                )
        elif prop.type == DataType.ARRAY:
            if prop.items:
                classes.extend(self._extract_nested_classes(f"{name}Item", prop.items))
        return classes

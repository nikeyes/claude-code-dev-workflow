import json
import csv
import io
from typing import Any


def process(data: str, format_type: str) -> list[dict[str, Any]]:
    if format_type == "json":
        parsed = json.loads(data)
        if isinstance(parsed, dict):
            parsed = [parsed]
        result = []
        for item in parsed:
            result.append({
                "source": "json",
                "fields": item,
                "field_count": len(item),
            })
        return result

    elif format_type == "csv":
        reader = csv.DictReader(io.StringIO(data))
        result = []
        for row in reader:
            cleaned = {k: v.strip() for k, v in row.items()}
            result.append({
                "source": "csv",
                "fields": cleaned,
                "field_count": len(cleaned),
            })
        return result

    elif format_type == "key_value":
        result = []
        for line in data.strip().split("\n"):
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            result.append({
                "source": "key_value",
                "fields": {key.strip(): value.strip()},
                "field_count": 1,
            })
        return result

    elif format_type == "xml_simple":
        result = []
        current_tag = None
        current_value = []
        fields = {}
        for line in data.strip().split("\n"):
            line = line.strip()
            if line.startswith("</") and line.endswith(">"):
                tag = line[2:-1]
                if tag == current_tag:
                    fields[tag] = "".join(current_value)
                    current_tag = None
                    current_value = []
                elif tag == "record":
                    if fields:
                        result.append({
                            "source": "xml_simple",
                            "fields": dict(fields),
                            "field_count": len(fields),
                        })
                        fields = {}
            elif line.startswith("<") and line.endswith(">"):
                tag = line[1:-1]
                if tag == "record":
                    fields = {}
                else:
                    current_tag = tag
                    current_value = []
            else:
                if current_tag:
                    current_value.append(line)

        if fields:
            result.append({
                "source": "xml_simple",
                "fields": dict(fields),
                "field_count": len(fields),
            })
        return result

    elif format_type == "fixed_width":
        field_spec = None
        result = []
        for line in data.strip().split("\n"):
            if field_spec is None:
                field_spec = []
                pos = 0
                for name in line.split():
                    start = line.index(name, pos)
                    field_spec.append((name, start))
                    pos = start + len(name)
                continue
            fields = {}
            for i, (name, start) in enumerate(field_spec):
                if i + 1 < len(field_spec):
                    end = field_spec[i + 1][1]
                else:
                    end = len(line)
                fields[name] = line[start:end].strip()
            result.append({
                "source": "fixed_width",
                "fields": fields,
                "field_count": len(fields),
            })
        return result

    else:
        raise ValueError(f"Unsupported format: {format_type}")


def get_supported_formats() -> list[str]:
    return ["json", "csv", "key_value", "xml_simple", "fixed_width"]

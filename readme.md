# jsonic
A simple python library to support inheritable json structures.

## Inheritance Operations

| Operation | Syntax |
| -- | -- |
| Inherit | * : "filepath.json" |
| Import Full Json | "x" : "*.filepath.json" |
| Import Json Key | "x" : "*.filepath.json#key |
| Python Build | "x" : "*.filepath.py#method |

Merge behavior
| type | behavior |
| -- | -- |
| value | add / replace |
| array | merge |
|dict | recursive merge |

## Example

base.json
```json
{
	"base": 1,
	"override": 1,
	"dict": {
		"subValue": 1
	},
	"arr": [1]
}
```

reference.json
```json
{
	"name": "ref",
	"val": 2
}
```

build.py
```python
def get_value(config):
	return "python value"
```

child.json
```json
{
	"*": "base.json",
	"child": 3,
	"override": 3,
	"dict": {
		"subValue": 3,
		"ref": "*.reference.json"
	},
	"arr": [3],
	"ref": "*.reference.json#val",
	"py": "*.build.py#get_value"
}
```

### Resolution with jsonic

jsonic child.json > result.json

result.json
```json
{
	"*": "base.json",
	"base": 1, // inherit from base
	"child": 3, // from child
	"override": 3, // override
	"dict" : {
		"subValue": 3, // recursive override
		"ref": { // full json ref
			"name": "ref",
			"val": 2
		}
	},
	"arr": [1, 3], // array concat base + child
	"ref" : 2, // json key ref
	"py" : "python value" // python build value
}
```

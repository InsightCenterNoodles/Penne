# Penne

![Build Status](https://github.com/InsightCenterNoodles/Penne/workflows/CI/badge.svg)
![PyPI](https://img.shields.io/pypi/v/Penne)
[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/InsightCenterNoodles/Penne/python-coverage-comment-action-data/endpoint.json&color=brightgreen)](https://htmlpreview.github.io/?https://github.com/InsightCenterNoodles/Penne/blob/python-coverage-comment-action-data/htmlcov/index.html)

Python Client Library for NOODLES Protocol

## Description
Penne is the first client library to implement the NOODLES messaging protocol in Python. NOODLES allows multiple client
applications to interact collaboratively with data in real-time. The client uses a websocket connection to send CBOR 
encoded messages, and all components in the scene graph can be subclassed and customized to fit an application's 
needs. 

## Documentation

For more information, check out [the documentation](https://insightcenternoodles.github.io/Penne/).


## Installation

Installation is as simple as:

```bash
pip install penne
```

## Simple Example

```python
from penne import Method, Client


class CustomMethod(Method):
  
  custom_attribute = None
  
  def on_new(self, message: dict):
    print(f"New method named {self.name} was created")
    
      
with Client("ws://localhost:50000", {Method: CustomMethod}) as client:
  # do stuff

```

## Hungry for more NOODLES?
For more information and other related repositories check out [this collection](https://github.com/InsightCenterNoodles)


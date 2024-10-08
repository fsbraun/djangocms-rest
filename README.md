[![codecov](https://codecov.io/gh/fsbraun/djangocms-rest/graph/badge.svg?token=RKQJL8L8BT)](https://codecov.io/gh/fsbraun/djangocms-rest)
[![djangocms4]( https://img.shields.io/badge/django%20CMS-4-blue.svg)](https://www.django-cms.org/en/)

# django CMS Headless Mode

## What is djangocms-rest?

djangocms-rest enables frontend projects to consume django CMS content through a browseable
read-only, REST/JSON API. It is based on the django rest framework (DRF).

## What is headless mode?

A Headless CMS (Content Management System) is a backend-only content management system that provides
content through APIs, making it decoupled from the front-end presentation layer. This allows
developers to deliver content to any device or platform, such as websites, mobile apps, or IoT
devices, using any technology stack. By separating content management from content presentation,
a Headless CMS offers greater flexibility and scalability in delivering content.

## What are the main benefits of running a CMS in headless mode?

Running a CMS in headless mode offers several benefits, including greater flexibility in delivering
content to multiple platforms and devices through APIs, enabling consistent and efficient
multi-channel experiences. It enhances performance and scalability by allowing frontend and backend
development to progress independently using the best-suited technologies. Additionally, it
streamlines content management, making it easier to update and maintain content across various
applications without needing to alter the underlying infrastructure.

## Are there js packages for drop-in support of frontend editing in the javascript framework of my choice?

The good news first: django CMS headless mode is fully backend supported and works independently
of the javascript framework. It is fully compatible with the javascript framework of your choosing.

## How can I implement a plugin for headless mode?

It's pretty much the same as for a traditional django CMS project, see
[here for instructions on how to create django CMS plugins](https://docs.django-cms.org/en/latest/how_to/09-custom_plugins.html).

Let's have an example. Here is a simple plugin with two fields to render a custom header. Please
note that the template included is just a simple visual helper to support editors to manage
content in the django CMS backend. Also, backend developers can now toy around and test their
django CMS code independently of a frontend project.

After setting up djangocms-rest and creating such a plugin you can now run the project and see a
REST/JSON representation of your content in your browser, ready for consumption by a decoupled
frontend.

`cms_plugins.py`:
```
# -*- coding: utf-8 -*-
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from . import models


class CustomHeadingPlugin(CMSPluginBase):
    model = models.CustomHeadingPluginModel
    module = 'Layout Helpers'
    name = "My Custom Heading"

    # this is just a simple, unstyled helper rendering so editors can manage content
    render_template = 'custom_heading_plugin/plugins/custom-heading.html'

    allow_children = False


plugin_pool.register_plugin(CustomHeadingPlugin)
```

`models.py`:
```
from cms.models.pluginmodel import CMSPlugin
from django.db import models


class CustomHeadingPluginModel(CMSPlugin):

    heading_text = models.CharField(
        max_length=256,
    )

    size = models.PositiveIntegerField(default=1)
```

`templates/custom_heading_plugin/plugins/custom-heading.html`:
```
<h{{ instance.size }} class="custom-header">{{ instance.heading_text }}</h{{ instance.size }}>
```


## Do default plugins support headless mode out of the box?

Yes, djangocms-rest provides out of the box support for any and all django CMS plugins whose content
can be serialized.


## Does the TextPlugin (Rich Text Editor, RTE) provide a json representation of the rich text?

Yes, djangocms-text has both HTML blob and structured JSON support for rich text.

URLs to other CMS objects are dynamic, in the form of `<app-name>.<object-name>:<uid>`, for example
`cms.page:2`. The frontend can then use this to resolve the object and create the appropriate URLs
to the object's frontend representation.

## I don't need pages, I just have a fixed number of content areas in my frontend application for which I need CMS support.

Absolutely, you can use the djangocms-aliases package. It allows you to define custom _placeholders_
that are not linked to any pages. djangocms-rest will then make a list of those aliases and their
content available via the REST API.

## Requirements

- Python
- Django
- Django CMS

## Installation

Install using pip:

```bash
pip install git+https://github.com/fsbraun/djangocms-rest@main
```

Update your `INSTALLED_APPS` setting:

```python
INSTALLED_APPS = [
    ...
    'djangocms_rest',
    'rest_framework',
    ...
]
```

Add the API endpoints to your project's `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('api/', include('djangocms_rest.urls')),
    ...
]
```

## Usage

Navigate to django rest framework's browsable API at `http://localhost:8000/api/`.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would
like to change.

## License

[BSD-3](https://github.com/fsbraun/djangocms-rest/blob/main/LICENSE)

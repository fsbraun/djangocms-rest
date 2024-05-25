[![codecov](https://codecov.io/gh/fsbraun/djangocms-rest/graph/badge.svg?token=RKQJL8L8BT)](https://codecov.io/gh/fsbraun/djangocms-rest)
[![djangocms4]( https://img.shields.io/badge/django%20CMS-4-blue.svg)](https://www.django-cms.org/en/)

# Django CMS REST

This is a demo project that provides RESTful APIs for Django CMS. Currently, it offers public read-only access to pages and placeholders. This allows for the retrieval of structured and nested content from your Django CMS instance in a programmatic way.

Please note that this project is in its early stages and more features will be added in the future. For now, it provides basic functionality for placeholders.

## Features

- Basic functionality for reading public pages and placeholders
- Optional HTML rendering for placeholder content (including sekizai blocks)

## To dos

- Full language fallback support on page level
- Menu api
- Admin api for editing content
  - Placeholder API (adding, deleting, plugins)
  - Plugin API (changing, rendering, getting options)
- Tests

## Requirements

- Python
- Django
- Django CMS

## Installation

Install using pip:

```bash
pip install git+https://github.com/fsbraun/djangocms_rest@main
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

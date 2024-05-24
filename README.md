Sure, here's a basic `README.md` file for your Django CMS REST project:

```markdown
# Django CMS REST

This is a demo project that provides RESTful APIs for Django CMS.

## Features

- Basic functionality for placeholders

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
```

Please replace the repository URL, dependencies, and other project-specific details as necessary.

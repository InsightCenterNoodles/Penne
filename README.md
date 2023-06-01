# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/InsightCenterNoodles/Penne/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                  |    Stmts |     Miss |   Cover |   Missing |
|---------------------- | -------: | -------: | ------: | --------: |
| penne/\_\_init\_\_.py |        3 |        0 |    100% |           |
| penne/core.py         |      108 |        3 |     97% |   293-295 |
| penne/delegates.py    |      534 |       27 |     95% |783-787, 808, 824, 838, 848, 863-864, 869-873, 889-891, 977, 998, 1018-1019, 1054-1059 |
| penne/handlers.py     |       83 |       41 |     51% |6, 30-34, 48-65, 104-109, 113-118, 123-125, 137, 148-158, 167-172 |
|             **TOTAL** |  **728** |   **71** | **90%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/InsightCenterNoodles/Penne/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/InsightCenterNoodles/Penne/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/InsightCenterNoodles/Penne/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/InsightCenterNoodles/Penne/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FInsightCenterNoodles%2FPenne%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/InsightCenterNoodles/Penne/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.
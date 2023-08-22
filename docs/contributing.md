# Contributing

Any help with the project would be super appreciated. Here are some steps to get started.

1. Clone the repo
2. Install the dependencies

```bash
pip install -r requirements.txt
pip install -r tests/requirements.txt
``` 

3. Switch to the `develop` branch or create a new one
3. Make your changes
4. Run the tests

    -These flags will help show which lines are missing test coverage
```bash
 pytest --cov penne --cov-report term-missing
```
5. Submit a pull request